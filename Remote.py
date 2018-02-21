import os
import numpy as np
import socket
from datetime import datetime
from collections import deque
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt


class RemoteDisplay(QtWidgets.QGroupBox):
    mutex = QtCore.QMutex()
    sig_start_capture = pyqtSignal()
    sig_stop_capture = pyqtSignal()
    sig_set_timestamp = pyqtSignal(object)
    sig_raise_error = pyqtSignal(object)
    sig_connection_error = pyqtSignal(list)
    sig_connection_successful = pyqtSignal(list)
    sig_wind_speed = pyqtSignal(int)

    # displaytimer = QtCore.QTimer()

    def __init__(self, main, source, name):
        QtWidgets.QGroupBox.__init__(self, name)

        # generate layout
        self.setLayout(QtWidgets.QVBoxLayout())
        self.source = source

        # ##############################

        self.name = name
        self.main = main

        self.sig_set_timestamp.connect(main.control.set_timestamp)
        self.sig_raise_error.connect(main.control.raise_error)
        self.sig_connection_error.connect(self.connection_error)
        self.sig_connection_successful.connect(self.connection_ok)
        self.sig_wind_speed.connect(self.show_wind_speed)

        #   information board
        self.connection_status = QtWidgets.QLabel()
        self.connection_status.setText("Not connected")
        self.wind_speed = QtWidgets.QLabel()
        self.wind_speed.setText("Wind speed: 0 m/s")

        # remote buttons
        self.button_connect = QtWidgets.QPushButton('Connect')
        self.button_arm_wind = QtWidgets.QPushButton('Arm')
        self.button_start_wind = QtWidgets.QPushButton('Start')
        self.button_stop_wind = QtWidgets.QPushButton('Stop')
        self.button_accelerate = QtWidgets.QPushButton('-')
        self.button_deccelerate = QtWidgets.QPushButton('+')

        self.button_connect.setMaximumHeight(50)
        self.button_connect.setMinimumWidth(100)
        self.button_arm_wind.setMaximumHeight(50)
        self.button_arm_wind.setMinimumWidth(100)
        self.button_start_wind.setMaximumHeight(50)
        self.button_start_wind.setMinimumWidth(100)
        self.button_stop_wind.setMaximumHeight(50)
        self.button_stop_wind.setMinimumWidth(100)
        self.button_accelerate.setMaximumHeight(50)
        self.button_accelerate.setMinimumWidth(100)
        self.button_deccelerate.setMaximumHeight(50)
        self.button_deccelerate.setMinimumWidth(100)

        self.button_arm_wind.setDisabled(True)
        self.button_start_wind.setDisabled(True)
        self.button_stop_wind.setDisabled(True)
        self.button_accelerate.setDisabled(True)
        self.button_deccelerate.setDisabled(True)

        self.layout().addWidget(self.connection_status, alignment=Qt.AlignLeft)
        self.layout().addWidget(self.wind_speed, alignment=Qt.AlignLeft)
        self.layout().addWidget(self.button_connect, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_arm_wind, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_start_wind, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_stop_wind, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_accelerate, alignment=Qt.AlignHCenter)
        self.layout().addWidget(self.button_deccelerate, alignment=Qt.AlignHCenter)

        # connect buttons
        self.button_connect.clicked.connect(self.clicked_connect)
        self.button_arm_wind.clicked.connect(self.clicked_arm_wind)
        self.button_stop_wind.clicked.connect(self.clicked_stop_wind)
        self.button_start_wind.clicked.connect(self.clicked_start_wind)
        self.button_accelerate.clicked.connect(self.clicked_accelerate)
        self.button_deccelerate.clicked.connect(self.clicked_deccelerate)


        # self.threadDisp = QtCore.QThread()
        # self.datagrabber.moveToThread(self.threadDisp)
        # self.main.control.threads.append(self.threadDisp)
        # self.threadDisp.start()
        #
        # # connections
        # self.main.sig_idle_screen.connect(self.set_idle_screen)
        # self.button_audio_plus.clicked.connect(self.audio_plus)
        # self.button_audio_minus.clicked.connect(self.audio_minus)
        # QtCore.QTimer().singleShot(0, self.beautify)

    def clicked_connect(self):
        self.source.connect_remote()

    def clicked_arm_wind(self):
        self.control.arm_wind()

    def clicked_stop_wind(self):
        self.control.stop_wind()

    def clicked_start_wind(self):
        self.control.start_wind()

    def clicked_accelerate(self):
        self.control.accelerate()

    def clicked_deccelerate(self):
        self.control.deccelerate()

    def connection_error(self, eMsg):
        self.connection_status.setText(eMsg[0])

    def connection_ok(self, eMsg):
        self.connection_status.setText("Connected to:" + eMsg[0])

    def show_wind_speed(self, value):
        self.wind_speed.setText(str(value))


class Remote(QtCore.QObject):
    # signals
    sig_set_timestamp = pyqtSignal(object)
    sig_raise_error = pyqtSignal(object)
    sig_exchange_finished = pyqtSignal()
    sig_new_data = pyqtSignal()


    mutex = QtCore.QMutex()
    dispdatachunks = deque()
    fileindex = 0
    display = None

    def __init__(self, main, debug=0, parent=None):
        """
        Initializes connection to RPi.

        Returns:

        """
        QtCore.QObject.__init__(self, parent)
        self.main = main
        self.debug = debug

        # timestamps
        self.sig_set_timestamp.connect(main.set_timestamp)
        self.sig_raise_error.connect(main.raise_error)

    def connect_remote(self, to_ip="127.0.0.1", to_port=12345):

        try:
            self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.soc.connect((to_ip, to_port))
            self.soc.send(bytes('blabla', encoding='utf-8'))
            self.main.main.remote_layout.sig_connection_successful.emit([to_ip])
            result_bytes = self.soc.recv(4096)  # the number means how the response can be in bytes
            result_int = int(result_bytes.decode("utf-8"))
            self.main.main.remote_layout.sig_wind_speed.emit(result_int)

        except ConnectionError as msg:
            print("Connection error: {0}".format(msg))
            self.main.main.remote_layout.sig_connection_error.emit([format(msg)])

    def disconnect_remote(self):
        self.soc.close()

        # result_bytes = soc.recv(4096)  # the number means how the response can be in bytes
        # result_string = result_bytes.decode("utf-8")
        #


    # for x, y in data:
    #     # send x and y separated by tab
    #     data = "{}\t{}".format(x,y)
    #     soc.sendall(data.encode("utf8"))
    #
    #     # wait for response from server, so we know
    #     # that server has enough time to process the
    #     # data. Without this it can make problems
    #
    #     if soc.recv(4096).decode("utf8") == "-":
    #         pass
    #
    # # end connection by sending this string
    # soc.send(b'--ENDOFDATA--')
