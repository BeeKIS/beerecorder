import sys

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore


class SpectrogramWidget(pg.PlotWidget):
    read_collected = QtCore.pyqtSignal(np.ndarray)

    # def __init__(self, chunksize=1000, samplerate=48000):
    def __init__(self, main, source, name, channel_control = False, samplerate = 48000, chunks=1000,
        playback = True, parent = None):
        super(SpectrogramWidget, self).__init__()

        """ cardinal variables """
        self.name = name
        self.main = main
        self.source = source
        self.chunksize=chunks
        self.img = pg.ImageItem()
        self.addItem(self.img)
        self.t = 10     # time of time display
        self.audio_samplerate = samplerate
        self.audio_display_time = (self.t * (self.audio_samplerate/self.chunksize))  # length of window
        self.update_rate = int(1/(self.chunksize/self.audio_samplerate))
        # self.update_rate = 100 # in herz

        """ define display size, cosmetics  """
        self.img_array = np.zeros((int(self.audio_display_time), int(self.chunksize / 2 + 1)))
        # self.img_array = np.zeros((self.audio_display_time, int(self.audio_samplerate/2)))
        # bipolar colormap
        pos = np.array([0., 1., 0.5, 0.25, 0.75])
        color = np.array([[0, 255, 255, 255], [255, 255, 0, 255], [0, 0, 0, 255], (0, 0, 255, 255), (255, 0, 0, 255)],
                         dtype=np.ubyte)
        cmap = pg.ColorMap(pos, color)
        lut = cmap.getLookupTable(0.0, 1.0, 256)
        self.img.setLookupTable(lut)
        self.img.setLevels([-50, 40])
        freq = np.arange((self.chunksize / 2) + 1) / (float(self.chunksize) / self.audio_samplerate)
        yscale = 1.0 / (self.img_array.shape[1] / freq[-1])
        self.img.scale((1. / self.audio_samplerate) * self.chunksize, yscale)
        self.setLabel('left', 'Frequency', units='Hz')
        self.win = np.hanning(self.chunksize)
        # self.setYRange(0, 0.5)
        self.show()

        """ buffer for sound """
        # self.audio_t = np.arange(-self.audio_display_time, 0., 1./self.audio_samplerate)
        # self.audiodata = np.zeros(int(self.audio_t.size), dtype=float)
        # -self.audio_display_time, 0., 1. / self.audio_samplerate)
        self.audiodata = np.zeros(self.chunksize)
        # self.stepsize = 500
        # self.mask = np.zeros(self.audiodata.size, dtype=bool)
        # self.mask[::self.stepsize] = 1.
        self.ymax = 1.

        """ refresher """
        self.datagrabber = DataGrabber(self)
        self.threadDisp = QtCore.QThread()
        self.datagrabber.moveToThread(self.threadDisp)
        self.main.control.threads.append(self.threadDisp)
        self.threadDisp.start()

    def update_data(self):
        # print('display update_data')
        datalist = self.source.get_dispdatachunk()
        if not len(datalist): return
        # print('audio-display: update_data called')
        try:
            data = np.hstack(datalist)
            # print(data.shape)
            if data.shape[1] > 0:
                data = data.mean(axis=-1)
        except:
            print(sys.exc_info()[0])
            print('length of data: {}'.format(len(data)))
            for d in datalist:
                print(d.shape)
            self.raise_error('Error in Displaydata: {}'.format(self.name))
        self.update(data)

    def update(self, chunk):

        # normalized, windowed frequencies in data chunk
        spec = np.fft.rfft(chunk * self.win) #/ self.chunksize

        # get magnitude
        psd = abs(spec)

        # convert to dB scale
        psd = 20 * np.log10(psd)

        # roll down one and replace leading edge with new data
        self.img_array = np.roll(self.img_array, -1, 0)
        self.img_array[-1:, :] = psd

        self.img.setImage(self.img_array, autoLevels=False)
        pass


class DataGrabber(QtCore.QObject):
    datatimer = QtCore.QTimer()

    def __init__(self, display, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.display = display
        # print('display data grabber initiated')
        self.datatimer.timeout.connect(self.display.update_data)
        QtCore.QTimer().singleShot(0, self.start_capture)

    def start_capture(self):
        # print('display data grabber capture started')
        self.datatimer.start(1/self.display.update_rate)

    def stop_capture(self):
        self.datatimer.stop()


# ######################################################

