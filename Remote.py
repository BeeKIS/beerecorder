import os
import numpy as np
import socket
from datetime import datetime
from collections import deque
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSignal


class RemoteDisplay(QtWidgets.QGroupBox):
    mutex = QtCore.QMutex()
    sig_start_connection = pyqtSignal()
    sig_stop_connection = pyqtSignal()
    sig_set_timestamp = pyqtSignal(object)
    sig_raise_error = pyqtSignal(object)

    def __init__(self, main, source, name):
        QtWidgets.QGroupBox.__init__(self, name)  # , parent=None)

        # generate layout
        # self.setLayout(QtWidgets.QHBoxLayout())
        self.source = source

        # ##############################

        self.name = name
        self.main = main
        self.source.display = self
        self.debug = self.main.debug
        # self.idle_screen = False
        # self.disp_samplerate = 200

        self.sig_set_timestamp.connect(main.control.set_timestamp)
        self.sig_raise_error.connect(main.control.raise_error)
        # optionLayout = QtWidgets.QHBoxLayout()
        # self.layout().addLayout(optionLayout)

        # remote buttons
        self.button_arm = QtWidgets.QPushButton('Arm')
        self.button_start = QtWidgets.QPushButton('Start')
        self.button_stop = QtWidgets.QPushButton('Stop')
        self.button_accelerate = QtWidgets.QPushButton('-')
        self.button_deccelerate = QtWidgets.QPushButton('+')

        # self.main.remote_base_layout.addStretch(5)
        #
        self.main.main_layout.addWidget(self.button_arm)
        self.main.main_layout.addWidget(self.button_start)
        self.main.main_layout.addWidget(self.button_stop)
        self.main.main_layout.addWidget(self.button_accelerate)
        self.main.main_layout.addWidget(self.button_deccelerate)
        #
        # self.main.remote_base_layout.addWidget(self.button_arm)
        # self.main.remote_base_layout.addWidget(self.button_start)
        # self.main.remote_base_layout.addWidget(self.button_stop)
        # self.main.remote_base_layout.addWidget(self.button_accelerate)
        # self.main.remote_base_layout.addWidget(self.button_deccelerate)

        # optionLayout.addWidget(self.button_arm)
        # optionLayout.addWidget(self.button_accelerate)
        # optionLayout.addWidget(self.button_deccelerate)
        # optionLayout.addWidget(self.button_stop)
        # optionLayout.addWidget(self.button_start)

        xy = 50
        self.button_arm.setMinimumHeight(xy)
        # self.button_arm.setMaximumWidth(xy)
        self.button_start.setMinimumHeight(xy)
        # self.button_start.setMaximumWidth(xy)
        self.button_stop.setMinimumHeight(xy)
        # self.button_stop.setMaximumWidth(xy)
        self.button_accelerate.setMinimumHeight(xy)
        # self.button_accelerate.setMaximumWidth(xy)
        self.button_deccelerate.setMinimumHeight(xy)
        # self.button_deccelerate.setMaximumWidth(xy)

        # ##############################

        # connections
        # self.button_arm.clicked.connect(self.arm)
        # self.button_start.clicked.connect(self.start)
        # self.button_stop.clicked.connect(self.stop)
        # self.button_accelerate.clicked.connect(self.accelerate)
        # self.button_deccelerate.clicked.connect(self.deccelerate)


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
        self.playing = False
        self.main = main
        self.debug = debug
        self.remotecontroler = RemoteControler()

        # timestamps
        self.sig_set_timestamp.connect(main.set_timestamp)
        self.sig_raise_error.connect(main.raise_error)
        # self.sig_remote_connect()
        # self.connect(self, QtCore.SIGNAL('set timestamp (PyQt_PyObject)'), main.set_timestamp)
        # self.connect(self, QtCore.SIGNAL('Raise Error (PyQt_PyObject)'), main.raise_error)

    def start_server(self):
        self.remotecontroler.start_server()


class RemoteControler(QtCore.QObject):
    """ very basic wav-file reader """

    # server.py

    def do_some_stuffs_with_input(input_string):
        """
        This is where all the processing happens.

        Let's just read the string backwards
        """

        print("Processing that nasty input!")
        return input_string[::-1]

    def input_process(self, conn, ip, port, MAX_BUFFER_SIZE=4096):

        # the input is in bytes, so decode it
        input_from_client_bytes = conn.recv(MAX_BUFFER_SIZE)

        # MAX_BUFFER_SIZE is how big the message can be
        # this is test if it's sufficiently big
        import sys
        siz = sys.getsizeof(input_from_client_bytes)
        if siz >= MAX_BUFFER_SIZE:
            print("The length of input is probably too long: {}".format(siz))

        # decode input and strip the end of line
        input_from_client = input_from_client_bytes.decode("utf8").rstrip()
        res = self.do_some_stuffs_with_input(input_from_client)
        print("Result of processing {} is: {}".format(input_from_client, res))

        vysl = res.encode("utf8")  # encode the result string
        conn.sendall(vysl)  # send it to client
        conn.close()  # close connection
        print('Connection ' + ip + ':' + port + " ended")

    def start_server(self, ip="127.0.0.1"):

        soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # this is for easy starting/killing the app
        soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        print('Socket created')

        try:
            soc.bind((ip, 12345))
            print('Socket bind complete')
        except socket.error as msg:
            import sys
            print('Bind failed. Error : ' + msg.strerror + str(sys.exc_info()))
            sys.exit()

        # Start listening on socket
        soc.listen(10)
        print('Socket now listening')

        while True:
            conn, addr = soc.accept()
            ip, port = str(addr[0]), addr[1]
            print('Accepting connection from ' + ip + ':' + port)
            try:
                self.input_process(conn, ip, port).start()
            except:
                print("Terible error!")
                import traceback
                traceback.print_exc()

        soc.close()
