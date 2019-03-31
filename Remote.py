import socket
from collections import deque

import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt

from calibrate import FitSpeed

__author__ = 'Janez Presern'


#TODO: enter the time stamp when wind velocity changes. Maybe as separate log??
#TODO: keep track of speed
#todo: transfer speed control from tunnel to here
#TODO: await confirmation from tunnel control



class RemoteDisplay(QtWidgets.QGroupBox):
    mutex = QtCore.QMutex()
    sig_start_capture = pyqtSignal()
    sig_stop_capture = pyqtSignal()
    sig_set_timestamp = pyqtSignal(object)
    sig_raise_error = pyqtSignal(object)
    sig_connection_error = pyqtSignal(list)
    sig_connection_successful = pyqtSignal(list)
    sig_wind_speed = pyqtSignal(float)

    # displaytimer = QtCore.QTimer()

    def __init__(self, main, source, name):
        QtWidgets.QGroupBox.__init__(self, name)

        self.calib_fn = "./calibrations/calibrationKV410.csv"
        self.calib = FitSpeed(self.calib_fn)

        # generate layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.source = source

        # ##############################

        self.name = name
        self.main = main

        self.speed = 0
        self.wished_speed = 0

        self.sig_set_timestamp.connect(main.control.set_timestamp)
        self.sig_raise_error.connect(main.control.raise_error)
        self.sig_connection_error.connect(self.connection_error)
        self.sig_connection_successful.connect(self.connection_ok)
        self.sig_wind_speed.connect(self.show_wind_speed)
        # self.sig_disconnection.successful()

        # # threads
        # self.threadRemote = QtCore.QThread()
        # self.rem_layout.moveToThread(self.threadRemote)
        # self.main.control.threads.append(self.threadRemote)
        # self.threadRemote.start()

        #   information board
        self.connection_status = QtWidgets.QLabel()
        self.connection_status.setText("Disconnected\n")
        self.wind_speed = QtWidgets.QLabel()
        self.wind_speed.setText("Wind speed: 0 m/s")

        # remote buttons
        self.button_connect = QtWidgets.QPushButton('Connect')
        self.button_disconnect = QtWidgets.QPushButton('Disconnect')
        # self.button_arm_wind = QtWidgets.QPushButton('Arm')
        self.button_start_wind = QtWidgets.QPushButton('Start')
        self.button_stop_wind = QtWidgets.QPushButton('Stop')
        self.button_accelerate_major = QtWidgets.QPushButton('+ 0.5 m/s')
        self.button_accelerate_minor = QtWidgets.QPushButton('+ 0.1 m/s')
        self.button_deccelerate_minor = QtWidgets.QPushButton('- 0.1 m/s')
        self.button_deccelerate_major = QtWidgets.QPushButton('- 0.5 m/s')

        self.button_connect.setMaximumHeight(50)
        self.button_connect.setMinimumWidth(150)
        self.button_disconnect.setMaximumHeight(50)
        self.button_disconnect.setMinimumWidth(150)
        # self.button_arm_wind.setMaximumHeight(50)
        # self.button_arm_wind.setMinimumWidth(150)
        self.button_start_wind.setMaximumHeight(50)
        self.button_start_wind.setMinimumWidth(150)
        self.button_stop_wind.setMaximumHeight(50)
        self.button_stop_wind.setMinimumWidth(150)
        self.button_accelerate_minor.setMaximumHeight(50)
        self.button_accelerate_minor.setMinimumWidth(150)
        self.button_deccelerate_minor.setMaximumHeight(50)
        self.button_deccelerate_major.setMinimumWidth(150)
        self.button_accelerate_major.setMaximumHeight(50)
        self.button_accelerate_major.setMinimumWidth(150)
        self.button_deccelerate_major.setMaximumHeight(50)
        self.button_deccelerate_major.setMinimumWidth(150)

        self.button_disconnect.setDisabled(True)
        # self.button_arm_wind.setDisabled(True)
        self.button_start_wind.setDisabled(True)
        self.button_stop_wind.setDisabled(True)
        self.button_accelerate_major.setDisabled(True)
        self.button_deccelerate_major.setDisabled(True)
        self.button_accelerate_minor.setDisabled(True)
        self.button_deccelerate_minor.setDisabled(True)

        self.layout().addWidget(self.connection_status, alignment=Qt.AlignLeft)
        self.layout().addWidget(self.wind_speed, alignment=Qt.AlignLeft)
        self.layout().addWidget(self.button_connect, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_disconnect, alignment=Qt.AlignHCenter)
        # self.layout().addWidget(self.button_arm_wind, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_start_wind, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_stop_wind, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_accelerate_major, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_accelerate_minor, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_deccelerate_minor, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_deccelerate_major, alignment=Qt.AlignHCenter)

        # connect buttons
        self.button_connect.clicked.connect(self.clicked_connect)
        self.button_disconnect.clicked.connect(self.clicked_disconnect)
        # self.button_arm_wind.clicked.connect(self.clicked_arm_wind)
        self.button_stop_wind.clicked.connect(self.clicked_stop_wind)
        self.button_start_wind.clicked.connect(self.clicked_start_wind)
        self.button_accelerate_major.clicked.connect(self.clicked_accelerate_major)
        self.button_deccelerate_major.clicked.connect(self.clicked_deccelerate_major)
        self.button_accelerate_minor.clicked.connect(self.clicked_accelerate_minor)
        self.button_deccelerate_minor.clicked.connect(self.clicked_deccelerate_minor)

        # self.threadDisp = QtCore.QThread()
        # self.datagrabber.moveToThread(self.threadDisp)
        # self.main.control.threads.append(self.threadDisp)
        # self.threadDisp.start()

    def clicked_connect(self):
        self.source.connect_remote()

    def clicked_disconnect(self, value):
        self.source.disconnect_remote()
        self.connection_status.setText("Disconnected\n")
        self.wind_speed.setText("Wind speed: 0 m/s")
        self.source.send_command("arm")

    def clicked_arm_wind(self):
        # self.source.send_command("arm")
        print("arm")

    def clicked_stop_wind(self):
        # self.source.send_command('stop')
        # self.control.stop_wind()
        print("stop")

    def clicked_start_wind(self):
        # self.source.send_command("start")
        print("start")

    def clicked_accelerate_major(self):
        # self.control.accelerate()
        # self.source.send_command("accelerate")
        # self.source.send_command("+0.5")
        self.wished_speed += 0.5
        print(self.calib.look_up_pwm(self.wished_speed))

    def clicked_deccelerate_major(self):
        # self.control.deccelerate()
        self.wished_speed -= 0.5

        print(self.calib.look_up_pwm(self.wished_speed))

    def clicked_accelerate_minor(self):
        # self.control.accelerate()
        self.source.send_command("")

    def clicked_deccelerate_minor(self):
        # self.control.deccelerate()
        self.source.send_command("decelerate")

    def connection_error(self, eMsg):
        self.connection_status.setText(eMsg[0])

    def connection_ok(self, eMsg):
        self.connection_status.setText("Connected to:\n" + eMsg[0])
        # self.button_arm_wind.setDisabled(False)
        self.button_connect.setDisabled(True)
        self.button_disconnect.setDisabled(False)

    def show_wind_speed(self, value):

        self.wind_speed.setText("Wind speed: "+ str(self.calib.look_up(value)) + " m/s")


class Remote(QtCore.QObject):
# class Remote(QtCore.QRunnable):
    # signals
    sig_connection_successful = pyqtSignal(bool)
    sig_disconnect = pyqtSignal()
    sig_received_response = pyqtSignal()

    dispdatachunks = deque()
    fileindex = 0
    display = None

    def __init__(self, control, debug=0, parent=None):
        """
        Initializes connection to RPi.

        Returns:

        """
        QtCore.QObject.__init__(self, parent)
        self.mutex = QtCore.QMutex()
        self.control = control
        self.debug = debug

        # timestamps
        # self.sig_set_timestamp.connect(self.control.set_timestamp)
        # self.sig_raise_error.connect(self.control.raise_error)
        self.to_ip = "127.0.0.1"
        # self.to_ip = "192.168.1.100"
        # self.to_ip = "192.168.1.101"
        self.to_port = 12345

        self.pwmDict = {60: [260, 276, 457],
                        100: [434, 481, 761],
                        400: [1736, 1954, 3047]
                        }
        self.pwmFreq = 60

    def connect_remote(self):
        self.mutex.lock()
        try:
            self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.soc.connect((self.to_ip, self.to_port))
            self.soc.send(bytes('pwmFreq'+str(self.pwmFreq), encoding='utf-8'))
            self.control.main.remote_layout.sig_connection_successful.emit([self.to_ip])
            result_bytes = self.soc.recv(4096).decode("utf-8")  # the number means how the response can be in bytes
            # result_int = int(result_bytes.decode("utf-8"))
            # self.control.main.remote_layout.sig_wind_speed.emit(result_bytes.lstrip('[ ').rstrip(']'))
            # self.control.main.remote_layout.sig_connection_successful.emit(result_bytes.lstrip('[').rstrip(']'))
            if result_bytes == 'armed':

                self.control.main.remote_layout.button_start_wind.setDisabled(False)
                self.control.main.remote_layout.button_stop_wind.setDisabled(False)
                self.control.main.remote_layout.button_disconnect.setDisabled(False)
                self.control.main.remote_layout.button_accelerate_major.setDisabled(False)
                self.control.main.remote_layout.button_deccelerate_major.setDisabled(False)
                self.control.main.remote_layout.button_accelerate_minor.setDisabled(False)
                self.control.main.remote_layout.button_deccelerate_minor.setDisabled(False)
                self.control.main.remote_layout.button_connect.setDisabled(True)
                self.control.main.remote_layout.sig_wind_speed.emit(0.)

        except ConnectionError as msg:
            print(self.to_ip + ":" + str(self.to_port) + " Connection error: {0}".format(msg))
            self.control.main.remote_layout.sig_connection_error.emit([format(msg)])
        self.mutex.unlock()

    def send_command(self, command='blabla'):

        self.mutex.lock()
        try:
            self.soc.send(bytes(command, encoding='utf-8'))
            self.control.main.remote_layout.sig_connection_successful.emit([self.to_ip])
            result_bytes = self.soc.recv(4096).decode("utf-8")  # the number means how the response can be in bytes
            # result_bytes = int(result_bytes.decode("utf-8"))
            if result_bytes == "armed":
                self.control.main.remote_layout.button_start_wind.setDisabled(False)
                self.control.main.remote_layout.button_stop_wind.setDisabled(False)
                self.control.main.remote_layout.button_disconnect.setDisabled(False)
                self.control.main.remote_layout.button_accelerate_major.setDisabled(False)
                self.control.main.remote_layout.button_deccelerate_major.setDisabled(False)
                self.control.main.remote_layout.button_accelerate_minor.setDisabled(False)
                self.control.main.remote_layout.button_deccelerate_minor.setDisabled(False)
                self.control.main.remote_layout.button_connect.setDisabled(True)
            else:
                self.control.main.remote_layout.sig_wind_speed.emit(np.round(float(result_bytes.lstrip('[ ').rstrip(']')), 2))

        except ConnectionError as msg:
            print("Connection error: {0}".format(msg))
            self.control.main.remote_layout.sig_connection_error.emit([format(msg)])
        self.mutex.unlock()

    def disconnect_remote(self):
        self.mutex.lock()
        self.soc.send(bytes("--ENDOFDATA--", encoding='utf-8'))
        self.soc.close()
        self.control.main.remote_layout.button_disconnect.setDisabled(True)
        self.control.main.remote_layout.button_connect.setDisabled(False)
        self.control.main.remote_layout.button_arm_wind.setDisabled(True)
        self.control.main.remote_layout.button_accelerate_major.setDisabled(True)
        self.control.main.remote_layout.button_deccelerate_major.setDisabled(True)
        self.control.main.remote_layout.button_accelerate_minor.setDisabled(True)
        self.control.main.remote_layout.button_deccelerate_minor.setDisabled(True)
        self.control.main.remote_layout.button_start_wind.setDisabled(True)
        self.control.main.remote_layout.button_stop_wind.setDisabled(True)
        self.control.main.remote_layout.sig_wind_speed.emit(0.)
        self.mutex.unlock()


# class Remote2(QtCore.QObject):
class Remote2(QtCore.QRunnable):
    # signals

    sig_connection_successful = pyqtSignal(bool)
    sig_disconnect = pyqtSignal()
    sig_received_response = pyqtSignal()
    sig_wind_speed = pyqtSignal(float)

    dispdatachunks = deque()
    fileindex = 0
    display = None

    def __init__(self, parent=None):
        super(Remote2, self).__init__()
        """
        Initializes connection to RPi.

        Returns:

        """
        self.mutex = QtCore.QMutex()
        # self.to_ip = "127.0.0.1"
        self.to_ip = "192.168.1.101"
        self.to_port = 12345

    @pyqtSlot()
    def connect_remote(self):
        self.mutex.lock()
        try:
            self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.soc.connect((self.to_ip, self.to_port))
            self.soc.send(bytes('blabla', encoding='utf-8'))
            self.sig_connection_successful.emit(True)
            result_bytes = self.soc.recv(4096)  # the number means how the response can be in bytes
            result_int = int(result_bytes.decode("utf-8"))
            self.sig_wind_speed.emit(result_int)

        except ConnectionError as msg:
            print(self.to_ip + ":" + str(self.to_port) + " Connection error: {0}".format(msg))
            self.sig_connection_error.emit([format(msg)])
        self.mutex.unlock()

    def send_command(self, command='blabla'):

        self.mutex.lock()
        try:
            self.soc.send(bytes(command, encoding='utf-8'))
            self.control.main.remote_layout.sig_connection_successful.emit([self.to_ip])
            result_bytes = self.soc.recv(4096).decode("utf-8")  # the number means how the response can be in bytes
            # result_bytes = int(result_bytes.decode("utf-8"))
            if result_bytes == "armed":
                self.control.main.remote_layout.button_start_wind.setDisabled(False)
                self.control.main.remote_layout.button_stop_wind.setDisabled(False)
                self.control.main.remote_layout.button_disconnect.setDisabled(False)
                self.control.main.remote_layout.button_accelerate.setDisabled(False)
                self.control.main.remote_layout.button_deccelerate.setDisabled(False)
                self.control.main.remote_layout.button_connect.setDisabled(True)
            else:
                self.control.main.remote_layout.sig_wind_speed.emit(int(result_bytes))

        except ConnectionError as msg:
            print("Connection error: {0}".format(msg))
            self.control.main.remote_layout.sig_connection_error.emit([format(msg)])
        self.mutex.unlock()

    def disconnect_remote(self):
        self.mutex.lock()
        self.soc.send(bytes("--ENDOFDATA--", encoding='utf-8'))
        self.soc.close()
        self.control.main.remote_layout.button_disconnect.setDisabled(True)
        self.control.main.remote_layout.button_connect.setDisabled(False)
        self.control.main.remote_layout.button_arm_wind.setDisabled(True)
        self.control.main.remote_layout.button_accelerate.setDisabled(True)
        self.control.main.remote_layout.button_deccelerate.setDisabled(True)
        self.control.main.remote_layout.button_start_wind.setDisabled(True)
        self.control.main.remote_layout.button_stop_wind.setDisabled(True)
        self.control.main.remote_layout.sig_wind_speed.emit(0.)
        self.mutex.unlock()
