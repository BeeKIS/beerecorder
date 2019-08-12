from datetime import datetime

import numpy as np
import pyqtgraph as pg
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal
# from pyqtgraph.Qt import QtCore as pgQtCore
from scipy.signal import square

""" 
fligh projector projects striped (or any other) pattern to convince the insect to fly by generating "moving landscape".
Flight projector operates its own stand-alone window, to which projection is "projected".

"""

__author__ = 'Janez Presern'


class ProjectorWindow():#pg.GraphicsWindow):

    def __init__(self, main, source, name):
        super(ProjectorWindow, self).__init__()

        """ mandatory who am I"""
        self.name = name
        self.main = main
        self.source = source

        """ empty variables """
        self.x = None
        self.y = None
        self.arr = None

        """ other variables """
        self.step = -1
        self.speed = -5

        """ get window ready"""
        # self.w = pg.GraphicsWindow()
        # self.w.setWindowTitle('Landscape projector')

        # """ get plot ready """
        # self.p = self.w.addPlot()
        # # self.pattern_gen_square()
        # self.pattern_gen_square()
        # self.curve = self.p.plot(self.x, self.y, stepMode=True, fillLevel=0, brush=(255, 255, 255, 255))
        # self.update_rate = int(0)
        # self.p.showAxis('bottom', False)
        # self.p.showAxis('left', False)

        """ get image ready """
        self.w = pg.ImageWindow()
        self.pattern_gen_square_noise()
        self.w.setImage(self.arr, autoLevels=False)
        # self.w.getHistogramWidget().hide()
        # self.w.getRoiPlot().hide()
        # self.w.roi.hide()
        self.w.ui.histogram.hide()
        self.w.ui.roiBtn.hide()
        self.w.ui.menuBtn.hide()

        # self.w.getMenuBtn().hide()
        # self.curve = self.p.plot(self.x, self.y, stepMode=True, fillLevel=0, brush=(255, 255, 255, 255))
        self.update_rate = int(0)
        # self.p.showAxis('bottom', False)
        # self.p.showAxis('left', False)

        """ update frequency """
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        # self.timer.start(10)

    """ get pattern ready (hist) """
    def pattern_gen_histogram_bw(self):
        self.y = np.zeros(1200)
        self.y[100::100] = 1
        self.x = np.arange(self.y.shape[0] + 1)

    def pattern_gen_square(self):
        self.x = np.linspace(0, 1, 500, endpoint=True)
        self.y = square(2 * np.pi * 5 * self.x)[:-1]
        self.y[self.y < 0] = 0

    def pattern_gen_square_noise(self):
        ## Create image to display
        self.arr = np.ones((400, 600), dtype=float)
        # self.arr[45:55, 45:55] = 0
        # self.arr[25, :] = 5
        # self.arr[:, 25] = 5
        # self.arr[75, :] = 5
        # self.arr[:, 75] = 5
        # self.arr[50, :] = 10
        # self.arr[:, 50] = 10
        self.arr += np.sin(np.linspace(0, 20, 600)).reshape(1, 600)
        self.arr += np.random.normal(size=(400, 600))
        self.arr = self.arr.T

    def update(self):
        # self.y = np.roll(self.y, self.speed)
        # self.curve.setData(self.x, self.y)

        self.arr = np.roll(self.arr, self.speed, axis=0)
        # self.p.setData(self.arr)
        self.w.setImage(self.arr)

class ProjectorControl(QtWidgets.QGroupBox):

    mutex = QtCore.QMutex()
    sig_start_capture = pyqtSignal()
    sig_stop_capture = pyqtSignal()
    sig_set_timestamp = pyqtSignal(object)
    sig_raise_error = pyqtSignal(object)
    sig_connection_error = pyqtSignal(list)
    sig_connection_successful = pyqtSignal(list)
    sig_land_speed = pyqtSignal(float)

    # displaytimer = QtCore.QTimer()

    def __init__(self, main, source, name):
        QtWidgets.QGroupBox.__init__(self, name)

        # generate layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.source = source

        # ##############################
        # self.name = name
        self.main = main
        self.wished_speed = 0

        #   information board
        self.connection_status = QtWidgets.QLabel()
        self.connection_status.setText("Status:\nNot synced")
        self.land_speed = QtWidgets.QLabel()
        self.land_speed.setText("Land speed:\n0 m/s")

        # remote buttons
        self.chkbox_sync = QtWidgets.QCheckBox("Sync with wind")
        self.button_connect = QtWidgets.QPushButton('empty')
        self.button_start_land = QtWidgets.QPushButton('Start')
        self.button_stop_land = QtWidgets.QPushButton('Stop')
        self.button_acc_major_land = QtWidgets.QPushButton('+ veliko')
        self.button_acc_minor_land = QtWidgets.QPushButton('+ malo')
        self.button_decc_minor_land = QtWidgets.QPushButton('- malo')
        self.button_decc_major_land = QtWidgets.QPushButton('- veliko')

        self.chkbox_sync.setMaximumHeight(50)
        self.button_connect.setMaximumHeight(50)
        self.button_connect.setMinimumWidth(120)
        self.button_start_land.setMaximumHeight(50)
        self.button_start_land.setMinimumWidth(120)
        self.button_stop_land.setMaximumHeight(50)
        self.button_stop_land.setMinimumWidth(120)
        self.button_acc_minor_land.setMaximumHeight(50)
        self.button_acc_minor_land.setMinimumWidth(120)
        self.button_decc_minor_land.setMaximumHeight(50)
        self.button_decc_major_land.setMaximumHeight(50)
        self.button_decc_major_land.setMinimumWidth(120)
        self.button_decc_minor_land.setMinimumWidth(120)
        self.button_acc_major_land.setMaximumHeight(50)
        self.button_acc_major_land.setMinimumWidth(120)
        # self.button_decc_minor_land.setDisabled(True)

        self.layout().addWidget(self.connection_status)
        self.layout().addWidget(self.land_speed)
        self.layout().addWidget(self.chkbox_sync)
        self.layout().addWidget(self.button_start_land)
        self.layout().addWidget(self.button_stop_land)
        self.layout().addWidget(self.button_acc_major_land)
        self.layout().addWidget(self.button_acc_minor_land)
        self.layout().addWidget(self.button_decc_minor_land)
        self.layout().addWidget(self.button_decc_major_land)

        # connect buttons
        self.button_stop_land.clicked.connect(self.clicked_stop_land)
        self.button_start_land.clicked.connect(self.clicked_start_land)
        self.button_acc_major_land.clicked.connect(self.clicked_acc_major_land)
        self.button_decc_major_land.clicked.connect(self.clicked_decc_major_land)
        self.button_acc_minor_land.clicked.connect(self.clicked_acc_minor_land)
        self.button_decc_minor_land.clicked.connect(self.clicked_decc_minor_land)

    def land_timestamp(self):

        timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        s = '{} \t {} \t {} \t{}'.format(timestamp, "Land speed: ", str(self.speed), " m/s")
        self.source.control.set_timestamp(s)

    def clicked_stop_land(self):
        self.main.projector.timer.stop()
        self.main.projector.speed = 0
        self.land_speed.setText("Land speed:\n0 m/s")
        print("stop")
        self.speed = 0
        timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        s = '{} \t {} \t {} \t{}'.format(timestamp, "Land: ", str(self.speed), " m/s")
        self.source.control.set_timestamp(s)

    def clicked_start_land(self):
        self.main.projector.speed = self.main.projector.step
        self.main.projector.timer.start(10)
        self.land_speed.setText("Land speed:\Yes")
        print("start")
        self.speed = 0
        timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        s = '{} \t {} \t {} \t{}'.format(timestamp, "Land speed: ", str(self.speed), " m/s")
        self.source.control.set_timestamp(s)

    def clicked_acc_major_land(self):

        if self.main.projector.speed + self.main.projector.step*5 > -100:
            self.main.projector.speed = self.main.projector.speed + self.main.projector.step*5
            self.land_speed.setText("landspeed: " + str(self.main.projector.speed) + " m/s")
            timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            s = '{} \t {} \t {} \t{}'.format(timestamp, "Land speed: ", str(self.main.projector.speed), " m/s")
            self.source.control.set_timestamp(s)

    def clicked_decc_major_land(self):

        if self.main.projector.speed <= self.main.projector.step*5:

            self.main.projector.speed = self.main.projector.speed - self.main.projector.step*5
            self.land_speed.setText("Land speed: " + str(self.main.projector.speed) + " m/s")
            timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            s = '{} \t {} \t {} \t{}'.format(timestamp, "Land speed: ", str(self.main.projector.speed), " m/s")
            self.source.control.set_timestamp(s)

    def clicked_decc_minor_land(self):

        if self.main.projector.speed <= self.main.projector.step:

            self.main.projector.speed = self.main.projector.speed - self.main.projector.step
            self.land_speed.setText("Land speed: " + str(self.main.projector.speed) + " m/s")
            timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
            s = '{} \t {} \t {} \t{}'.format(timestamp, "Land speed: ", str(self.main.projector.speed), " m/s")
            self.source.control.set_timestamp(s)

    def clicked_acc_minor_land(self):

        if self.main.projector.speed + self.main.projector.step > -100:

            if self.main.projector.speed < 100:
                self.main.projector.speed = self.main.projector.speed + self.main.projector.step * 5
                self.land_speed.setText("Land speed: " + str(self.main.projector.speed) + " m/s")
                timestamp = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
                s = '{} \t {} \t {} \t{}'.format(timestamp, "Land speed: ", str(self.main.projector.speed), " m/s")
                self.source.control.set_timestamp(s)

    def show_land_speed(self, value):

        self.land_speed.setText("Provisional_\n moving")

