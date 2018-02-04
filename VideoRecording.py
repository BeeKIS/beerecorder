import sys
import os
import numpy as np
import subprocess as sp
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal


def get_encoder():
    if os.name == 'posix':
        pathlist = ['/usr/bin/avconv', '/usr/bin/ffmpeg', '/usr/local/bin/ffmpeg']#, '/usr/local/Cellar/ffmpeg/3.2.2/bin/ffmpeg']
        for p in pathlist:
            if os.path.exists(p):
                return p
        else:
            sys.exit('No encoder found. Check path! Provide correct symlinks. If on Os X, check your HomeBrew cellar!')
    else:
        pathlist = ["C:/Program Files/ffmpeg/bin/ffmpeg.exe",
                    "C:/Program Files (x86)/ffmpeg/bin/ffmpeg.exe"]
        for p in pathlist:
            if os.path.exists(p):
                return
        else:
            sys.exit('No encoder found')

encoder_path = get_encoder()


class VideoRecording(QtCore.QObject):
    # signals
    sig_set_timestamp = pyqtSignal(object)
    sig_raise_error = pyqtSignal(object)
    mutex = QtCore.QMutex()

    def __init__(self, camera, save_dir, cn, file_counter, resolution, fps,
                 color=False, parent=None):
        QtCore.QObject.__init__(self, parent)

        self.saving = False
        self.camera = camera
        self.save_dir = save_dir
        self.filename = camera.filename
        current_fn = '{:04d}__'.format(file_counter) + cn + '__' + self.filename + '.avi'
        out_path = os.path.join(self.save_dir, current_fn)
        metadata_fn = '{:04d}__'.format(file_counter) + cn + '__' + self.filename + '_timestamps.dat'
        self.metadata_fn = os.path.join(self.save_dir, metadata_fn)

        self.write_counter = 0
        quality = 2

        # connects
        self.sig_set_timestamp.connect(camera.control.set_timestamp)
        self.sig_raise_error.connect(camera.control.raise_error)

        # homebrew
        self.writer = VideoWriter(out_path, 'H264', int(fps), resolution, quality, color)
        
    def start_rec(self):
        self.saving = True
        self.continuous_writing()

    def isOpened(self):
        return self.writer.isOpened()

    def get_write_count(self):
        self.mutex.lock()
        wc = self.write_counter
        self.mutex.unlock()
        return wc

    def update_write_count(self):
        self.mutex.lock()
        self.write_counter += 1
        self.mutex.unlock()

    def stop_recording(self):
        self.mutex.lock()
        self.saving = False
        self.mutex.unlock()

        last = self.get_write_count()
        double_counter = -1
        while self.camera.get_recframesize() > 0:
            # print('Writing: {} of {}'.format(self.recording.get_write_count(), triggered_frames))
            print('Video frames left to write: {}'.format(self.camera.get_recframesize()))
            self.write()
            # if last == self.recording.get_write_count(): double_counter += 1
            # if double_counter == 10:
            #     error = 'Frames cannot be saved.'
            #     self.sig_raise_error.emit(error)
            #     break
            # QtCore.QThread.msleep(100)

    def recording(self):
        self.mutex.lock()
        s = self.saving
        self.mutex.unlock()
        return s

    def continuous_writing(self):
        while self.recording():
            self.write()
        print('video recording stopped')

    def write(self):
        # print('rec writing'+str(QtCore.QThread.currentThread()))
        data = self.camera.get_recframe()
        if data == None:
            QtCore.QThread.msleep(5)
            return
        frame, dtime = data
        self.writer.write(frame)
        self.update_write_count()
        self.write_metadata(dtime)
        if not self.recording:
            return

    def write_metadata(self, current_datetime):
        with open(self.metadata_fn, 'a') as f:
            f.write(current_datetime)
            f.flush()

    # def close(self):
    #     while len(self.audiodev.datachunks):
    #         self.write()
    #     while len(self.audiodev.metachunks):
    #         self.write_metadata()

    def release(self):
        self.writer.release()


class VideoWriter:
    def __init__(self, filename, fourcc='H264', fps=30, frameSize=(640, 480), quality=20, color=False):
        
        self.filename = filename

        # check if target file exists; if so: delete it
        if os.path.exists(filename):
            print('file exists: deleting ...')
            # os.path.remove(filename)
            os.remove(filename)

        self.quality = quality
        self.color = color
        self.fourcc = fourcc
        self.fps = fps
        self.width, self.height = frameSize
        self.depth = 3 if color else 1
        self.proc = None
        self.open()

    def open(self):
        # 4194304 bytes

        if self.color:
            cmd = [encoder_path, '-loglevel', 'error',
                   '-f', 'rawvideo',
                   '-pix_fmt', 'rgb24',
                   '-s', '{:d}x{:d}'.format(self.width, self.height),
                   '-r', '{:.10f}'.format(self.fps),
                   '-i', '-']
        else:
            cmd = [encoder_path, '-loglevel', 'error',
                   '-f', 'rawvideo',
                   '-pix_fmt', 'gray',
                   '-s', '{:d}x{:d}'.format(self.width, self.height),
                   '-r', '{:.10f}'.format(self.fps),
                   '-i', '-']

        codecs_map = {
            'XVID': 'mpeg4',
            'DIVX': 'mpeg4',
            'H264': 'libx264',
            'MJPG': 'mjpeg',
        }

        if self.fourcc in codecs_map:
            vcodec = codecs_map[self.fourcc]
        else:
            vcodec = self.fourcc
        cmd += ['-vcodec', vcodec, '-preset', 'ultrafast',]

        if self.fourcc == 'XVID':
            # variable bitrate ranging between 1 to 31
            # see: https://trac.ffmpeg .org/wiki/Encode/MPEG-4
            cmd += ['-qscale:v', str(self.quality)]
        
        cmd += [self.filename]
        self.proc = sp.Popen(cmd, stdin=sp.PIPE, bufsize=10**8)

    def isOpened(self):
        return (self.proc != None)

    def write(self, image):
        # if self.color:
        #     if image.shape[1] != self.height or image.shape[0] != self.width or image.shape[2] != self.depth:
        #         raise ValueError('Image dimensions do not match')
        # else:
        #     if image.shape[1] != self.height or image.shape[0] != self.width:
        #         print image.shape, self.height, self.width
        #         raise ValueError('Image dimensions do not match')
        # self.proc.stdin.write(image.astype(np.uint8).tostring())
        self.proc.stdin.write(image.tostring())
        # pipe.proc.stdin.write(image_array.tostring())

        self.proc.stdin.flush()

    def release(self):
        QtCore.QThread.msleep(100)  # wait for pipe to finish processing
        self.proc.communicate()  # closes pipe
        self.proc = None


