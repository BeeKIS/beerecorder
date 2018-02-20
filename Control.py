"""
a class for connecting gui, hardware and experiments
"""
import os, argparse
from datetime import datetime, timedelta
import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal

from Devices import Devices
from ExperimentControl import ExperimentControl
from doc import doc, details

cfg = dict(audio_input=True,
           audio_output=False,
           video_input=True,
           audio_input_channels=2,
           audio_input_samplerate=48000,
           audio_input_chunksize=2048,
           use_hydro=False,
           # use_hydro=True,
           audio_output_chunksize=2048,
           pointgrey=False,
           fast_and_small_video=True,
           trigger=None,
           delay=0,
           scheduled_restarts=True,
           scheduled_restarts_interval=30,
           idle_screen=True,
           selected_cameras=[0, 1, 2], # add number of cameras search range.
           remote=False)


class Control(QtCore.QObject):
    # signals
    sig_start_saving = pyqtSignal()
    sig_start_capture = pyqtSignal()
    sig_stop_capture = pyqtSignal()
    sig_start_playback = pyqtSignal()
    sig_start_recordings = pyqtSignal(object)
    sig_stop_recordings = pyqtSignal()
    sig_start_experiment = pyqtSignal()
    sig_info_update = pyqtSignal(object)

    cfg = cfg
    name = 'bEye'

    mutex = QtCore.QMutex()
    threads = list()

    # device flags
    default_label_text = 'no recording'
    starttime = None
    saving = False
    working_dir = os.path.abspath(os.path.curdir)
    output_dir = ''
    save_dir = ''
    file_counter = 0

    start_delay = 1
    last_framerate = 0

    rec_info = dict(rec_info='',
                    rec_start='',
                    rec_end='',
                    comments=list())

    audio_playback = False
    audio_playback_file = ''
    color = False
    selected_cameras = None

    def __init__(self, main, debug=0, parent=None):
        QtCore.QObject.__init__(self, parent)

        self.main = main
        self.debug = debug
        self.handle_options()
        self.devices = Devices(self)
        # self.exclude_cam_checkbox = QtWidgets.QCheckBox('Exclude camera')
        self.cam_exclude = {key: 0 for (key, value) in self.devices.cameras.items()} # 0: not excluded; 1 excluded

        if self.options.audio_playback_list:
            self.exp_control = ExperimentControl(self)

            self.threadExpCon = QtCore.QThread(self)
            self.exp_control.moveToThread(self.threadExpCon)
            self.threads.append(self.threadExpCon)
            self.threadExpCon.start()

            self.sig_start_experiment.connect(self.exp_control.clicked_start)
            self.exp_control.sig_start_rec.connect(self.start_new_recording_session)
            # self.exp_control.sig_exp_finished.connect(self.experiment_finished)

        # set initial label
        self.displaytimer = QtCore.QTimer()
        self.displaytimer.timeout.connect(self.update_label_info)

        # #################
        # time related variables
        self.recording_restart_time = 0
        self.restart_times = np.concatenate((np.arange(self.cfg['scheduled_restarts_interval'], 24*60., self.cfg['scheduled_restarts_interval']), [24*60.]))  # in hours
        self.restart_dts = list()
        self.programmed_stop = False
        self.programmed_stop_dt = None
        self.starttime = None
        self.file_Name = None

    def handle_options(self):
        # parser = OptionParser()
        parser = argparse.ArgumentParser(description=doc, epilog=details,
                                         formatter_class=argparse.RawTextHelpFormatter)
        parser.add_argument("--audio", "-a", action="store_true", dest="do_not_use_audio", default=False)
        parser.add_argument("--video", "-v", action="store_true", dest="do_not_use_video", default=False)
        parser.add_argument("--output_directory", "-o", action="store", type=str, dest="output_dir", default='')
        parser.add_argument("--audio_playback", "-u", action="store", type=str, dest="audio_playback", default='')
        parser.add_argument("--audio_playback_list", "-l", action="store", type=str, dest="audio_playback_list", default='')
        parser.add_argument("--devices", "-d", action="store_true", dest="show_devices", default=False)
        parser.add_argument("--audio_channels", "-c", action="store", type=int, dest="audio_channels", default=1)
        parser.add_argument("--stop_time", "-s", action="store", type=str, dest="stop_time", default='')
        parser.add_argument("--farbe", "-f", action="store_true", dest="color", default=False)
        parser.add_argument("--selected_cameras", "-k", action="store", type=str, dest="selected_cameras", default='0')
        # parser.add_argument("--instant_start", "-s", action="store_true", dest="instant_start", default=False)
        parser.add_argument("--idle_screen", "-i", action="store_true", dest="idle_screen", default=False)
        parser.add_argument("--remote", "-r", action="store_true", dest="remote", default=False)
        self.options = parser.parse_args()

        # self.options.audio_playback_list = 'playback_files.txt'
        # self.options.audio_playback = 'test_data_midi__mod.wav'

        # # programmed stop-time
        if self.options.stop_time:
            try:
                a = datetime.strptime(self.options.stop_time, '%H:%M:%S')
                b = datetime.now()
                c = datetime(b.year, b.month, b.day, a.hour, a.minute, a.second)
                if c < b:
                    c += timedelta(days=1)
            except ValueError:
                pass
            else:
                self.programmed_stop = True
                self.programmed_stop_dt = c

            try:
                a = datetime.strptime(self.options.stop_time, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass
            else:
                self.programmed_stop = True
                self.programmed_stop_dt = a

            if self.programmed_stop is not True:
                print('Error: allowed stop-time formats are:' '\n"HH:MM:SS" and "YY-mm-dd HH:MM:SS"')
                quit()

            else:
                print('Automated Stop activated: {0:s}'.format(str(self.programmed_stop_dt)))

        if self.options.do_not_use_audio:
            self.cfg['audio_input'] = False

        if self.options.do_not_use_video:
            self.cfg['video_input'] = False

        # output directory
        if self.options.output_dir:
            if os.path.exists(self.options.output_dir):
                self.output_dir = os.path.realpath(self.options.output_dir)
                print('Output Directory: {0:s}'.format(self.output_dir))
            else:
                print('Error: output directory does not exist')
                self.close()

        if self.options.audio_playback:
            if os.path.exists(self.options.audio_playback):
                self.audio_playback_file = self.options.audio_playback
                if not os.path.exists(self.options.audio_playback):
                    print('Output audio-file does not exist')
                    self.close()
                self.cfg['audio_output'] = True

        if self.options.audio_playback_list:
            if os.path.exists(self.options.audio_playback_list):
                if not os.path.exists(self.options.audio_playback_list):
                    print('Playback-list-file does not exist')
                    self.close()
                self.cfg['audio_output'] = True

        # self.audio_channels = self.options.audio_channels

        if self.options.show_devices:
            from AudioDev import show_available_input_devices
            from AudioDevOut import show_available_output_devices

            show_available_input_devices()
            show_available_output_devices()
            quit()

        if not self.cfg['video_input']:
            self.name = 'fishear'

        #   record in color
        if self.options.color:
            self.color = True

        if self.options.selected_cameras:
            # self.cfg["selected_cameras"] = list(map(int, list(self.options.selected_cameras)))
            self.cfg["selected_cameras"] = [0, 1, 2]

        if self.options.remote:
            self.cfg["remote"] = True

    def triggered_start(self):
        # start new recording session
        if not self.options.audio_playback_list:
            ok = self.start_new_recording_session(self.cfg['delay'], query=True)
            if not ok:
                return
        else:# start experiment
            self.sig_start_experiment.emit()

    def triggered_stop(self):
        if self.options.audio_playback_list:
            self.exp_control.exp_running = False  # flag to stop experiment
        self.stop_all_saving()  # stop all ongoing inputs and outputs

    def start_capture(self):
        self.sig_start_capture.emit()

    def stop_capture(self):
        self.sig_stop_capture.emit()

    def start_new_recording_session(self, delay=0, query=False):
        if query:
            ok = self.query_recording_info()
            if not ok:
                return False
        self.starttime = datetime.now() + timedelta(seconds=delay)
        self.rec_info['rec_start'] = self.starttime.strftime("%Y-%m-%d  %H:%M:%S")

        # create a new directory for the data
        save_dirname = self.starttime.strftime("%Y-%m-%d__%H-%M-%S")
        if self.output_dir is None:
            self.save_dir = os.path.join(self.working_dir, self.name+'_'+save_dirname)
        else:
            self.save_dir = os.path.join(self.output_dir, self.name+'_'+save_dirname)

        try:
            os.mkdir(self.save_dir)
        except:
            print('start new recording:', self.save_dir)
            print('creation of output directory failed')
            self.close()

        self.write_recording_info()
        self.file_counter = 0

        # if requested, start with a short delay
        if delay > 0:
            self.delaytimer = QtCore.QTimer()
            self.delaytimer.timeout.connect(self.update_delay)
            self.delaytimer.start(1000)  # msec interval
            self.update_delay()
        else:
            self.start_recordings()
        return True

    def update_delay(self):
        countdown = self.starttime-datetime.now()
        if countdown.total_seconds() > 0:
            time_label = 'start in {:.0f} seconds'.format(countdown.total_seconds())
            self.sig_info_update.emit(time_label)
        else:
            self.delaytimer.stop()
            self.delaytimer = None
            self.start_recordings()

    def start_recordings(self):

        # if automated restarts are enabled, schedule them
        if self.cfg['scheduled_restarts'] and not (self.options.audio_playback or self.options.audio_playback_list):
            self.set_restart_times()
            self.displaytimer.timeout.connect(self.timecheck)

        self.file_counter += 1

        # in case of other synced recording devices:
        ## these have to be ready when the trigger from the audio-device arrives
        self.prepare_other_recordings(self.file_counter)
        if self.cfg['audio_input']:
            self.devices.audiodev.prepare_recording(self.save_dir, self.file_counter)

        if self.cfg['audio_output']:
            print('\n# Playing file: {}'.format(os.path.basename(self.audio_playback_file)))
            self.devices.audiodevout.open(self.audio_playback_file)
            # DROP TIMESTAMP
            timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            s = timestamp + ' \t ' + 'Playback - Using stimulus file: {}'.format(self.audio_playback_file)
            self.set_timestamp(s)

        # start saving and playback
        self.saving = True
        self.start_other_recordings()
        if self.cfg['audio_input']:
            self.devices.audiodev.start_saving()
        if self.cfg['audio_output']:
            print('playback start')
            self.sig_start_playback.emit()

        # DROP TIMESTAMP
        timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        s = timestamp + ' \t ' + 'recording started'
        self.set_timestamp(s)

        self.displaytimer.start(1000)  # msec interval

    def recording_restart(self):
        self.stop_all_saving(restart=True)
        self.start_recordings()
        self.set_restart_times() ## debug

    def query_recording_info(self):
        # query info on recording
        dlg =  QtWidgets.QInputDialog()
        dlg.setInputMode(QtWidgets.QInputDialog.TextInput)
        dlg.setLabelText('Info on recording:')
        dlg.setWindowTitle('Info on recording')
        dlg.resize(500,200)
        ok = dlg.exec_()  # shows the dialog
        if ok:
            self.rec_info['rec_info'] = dlg.textValue()
            if self.audio_playback:
                self.rec_info['rec_info'] += ' -- Playback of: {:}'.format(self.audio_playback_file)
            return True
        else:
            return False

    def write_recording_info(self):
        recording_info_fn = 'recording_info.txt'
        fn = os.path.join(self.save_dir, recording_info_fn)
        with open(fn, 'w', encoding='utf-8') as f:
            f.write('recording info: {0}\n'.format(self.rec_info['rec_info']))#.encode("utf-8"))
            f.write('starttime: {0}\n'.format(self.rec_info['rec_start']))#.encode("utf-8"))
            f.write('endtime: {0}\n'.format(self.rec_info['rec_end']))#.encode("utf-8"))
            for c in self.rec_info['comments']:
                f.write('comment: {0}\n'.format(c))#.encode("utf-8"))

    def stop_all_saving(self, restart=False):
        if not self.saving:
            return
        self.saving = False
        self.displaytimer.stop()
        self.sig_info_update.emit(self.default_label_text)

        if self.cfg['audio_input']:
            self.devices.audiodev.stop_saving()
        self.stop_other_recordings()
        if self.cfg['audio_output']:
            self.devices.audiodevout.stop_playing()
            self.main.audioout_disp.reset_plot()

        # DROP TIMESTAMP
        timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        s = timestamp + ' \t ' + 'recording stopped'
        self.set_timestamp(s)

        if not restart:
            # document stop
            self.rec_info['rec_end'] = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            self.write_recording_info()
            self.rec_info = dict(rec_info='',
                                 rec_start='',
                                 rec_end='',
                                 comments=list())
        if self.options.audio_playback_list:
            self.exp_control.rec_session_finished()

    def playback_finished(self):
        if self.options.audio_playback_list:
            print('playback finished: stop all saving')
            self.stop_all_saving()
        elif self.options.audio_playback:
            print('playback finished: triggered stop')
            self.triggered_stop()

    def set_restart_times(self):

        if not self.cfg['scheduled_restarts']:
            return

        # do nothing if there are defined restart times
        if len(self.restart_dts) or self.audio_playback:
            return

        now = datetime.now()
        midnight_yesterday = datetime(now.year, now.month, now.day)
        midnight_today = datetime(now.year, now.month, now.day)+timedelta(hours=24)

        self.restart_dts = list()
        for mi in self.restart_times:
            new_dt = midnight_yesterday + timedelta(minutes=mi)
            if new_dt > now and new_dt <= midnight_today:
                self.restart_dts.append(new_dt)


        # debug: test restart times
        # self.restart_dts = [datetime.now()+timedelta(seconds=5 )]
        # print self.restart_dts

    def update_label_info(self):
        timestamp = self.starttime.strftime("%Y-%m-%d  %H:%M:%S")
        time_label = 'start-time: {0:s}   ---  running: {1:s}'.format(timestamp, str(datetime.now()-self.starttime)[:-7])
        self.sig_info_update.emit(time_label)

    def timecheck(self):
        # check for next_inrecording_restart
        if len(self.restart_dts) and datetime.now() > self.restart_dts[0]:
            self.restart_dts.pop(0)
            self.recording_restart()

    def stop_all_capture(self):
        if self.cfg['video_input']:
            self.main.canvastimer.stop()
        if self.cfg['audio_input']:
            self.devices.audiodev.stop_recording()
        self.close_other_recordings()

    def prepare_other_recordings(self, file_counter):
        if self.cfg['trigger']:
            framerate = self.devices.audiodev.get_defined_framerate()
            if self.last_framerate < self.devices.audiodev.get_defined_framerate()*.8:
                framerate = self.last_framerate
                self.raise_warning('Actual video framerate much smaller than defined framerate!')

            for cam_name, cam in self.devices.cameras.items():
                if self.main.control.cam_exclude[cam_name] == 0:
                    cam.new_recording(self.save_dir, cam_name, self.file_counter, framerate)
                else:
                    # self.exclude_cam_checkbox.setDisabled(True)
                    print('Cam will stay excluded until app restarts')
        else:
            for cam_name, cam in self.devices.cameras.items():
                    # cam.new_recording(self.save_dir, self.file_counter)
                    if self.main.control.cam_exclude[cam_name] == 0:
                        cam.new_recording(self.save_dir, cam_name, self.file_counter)
                    # else:
                    #     self.exclude_cam_checkbox.setDisabled(True)
                    #     print('Cam will stay excluded until app restarts')

    def start_other_recordings(self):
        for cam_name, cam in self.devices.cameras.items():
            cam.start_saving()

    def stop_other_recordings(self):
        for cam_name, cam in self.devices.cameras.items():
            if self.main.control.cam_exclude[cam_name] == 0:
                cam.stop_saving()

    def close_other_recordings(self):
        QtCore.QThread.msleep(500)
        for cam_name, cam in self.devices.cameras.items():
            if self.cfg['trigger'] is None:
                cam.stop_capture()
                QtCore.QThread.msleep(500)
            cam.close()

    def set_timestamp(self, s):
        print('Timestamp: {}'.format(s))

        if self.save_dir is None: return
        if not len(self.save_dir): return
        if self.debug > 0:
            print('timestamp: {}'.format(s))
        timestamp_fn = '{:04d}_timestamps.txt'.format(self.file_counter)
        fn = os.path.join(self.save_dir, timestamp_fn)
        with open(fn, 'a') as f:
            f.write(s+'\n')
        self.rec_info['comments'].append(s)

    def raise_warning(self, s):
        e = '\n'+80*'#'+'\n'
        print(e+'Warning raised: {}'.format(s)+e)

    def raise_error(self, s):
        e = '\n'+80*'#'+'\n'
        print(e+'Error raised: {}'.format(s)+e)
        self.main.close()

    def close(self):
        self.main.close()