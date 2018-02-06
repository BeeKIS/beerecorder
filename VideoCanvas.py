import os
from PIL import Image
from datetime import datetime
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import Qt
from itertools import compress


class VideoTab(QtWidgets.QWidget):
    """This class creates the a Tab for Camera data"""
    def __init__(self, main, cam_name, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)
        #self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.cam_name = cam_name
        self.main = main

        # generate layout
        self.setLayout(QtWidgets.QHBoxLayout())

        self.canvas = VideoCanvas(self.main, parent=self)
        # self.layout().addStretch()    #### disable expanding
        self.layout().addWidget(self.canvas)
        # self.layout().addStretch()    #### disable expanding

        # options layout
        videoOptionLayout = QtWidgets.QVBoxLayout()
        self.layout().addLayout(videoOptionLayout)
        
        # framerate indicator
        self.framerate_counter = QtWidgets.QLabel('', self)
        font = self.framerate_counter.font()
        font.setPointSize(self.main.label_font_size)
        self.framerate_counter.setFont(font)
        videoOptionLayout.addWidget(self.framerate_counter)

        # checkbox for coarse and high display quality
        self.quality_checkbox = QtWidgets.QCheckBox('High Res display', self)
        videoOptionLayout.addWidget(self.quality_checkbox)
        self.quality_checkbox.stateChanged.connect(self.canvas.set_display_quality)
        # self.connect(self.quality_checkbox, QtCore.SIGNAL('toggled()'), self.canvas.set_display_quality)

        # checkbox for exclusion of cameras from recording
        self.exclude_cam_checkbox = QtWidgets.QCheckBox('Exclude camera', self)
        videoOptionLayout.addWidget(self.exclude_cam_checkbox, QtCore.Qt.AlignRight)
        self.exclude_cam_checkbox.stateChanged.connect(self.exclude_cam)

        # set framerate
        # ...

        # modify ROI button
        self.roi_button = QtWidgets.QPushButton('Modify ROI')
        videoOptionLayout.addWidget(self.roi_button)
        self.roi_button.clicked.connect(self.modify_roi)
        # connection

        # photo button
        self.photo_button = QtWidgets.QPushButton('Snapshot!')
        videoOptionLayout.addWidget(self.photo_button)
        self.photo_button.clicked.connect(self.canvas.save_photo)
        # connection

    def get_available_framerates(self):
        pass

    def set_framerate(self, val):
        pass

    def modify_roi(self):
        pass

    def exclude_cam(self):

        if self.main.control.cam_exclude[self.cam_name] == 0:
            self.main.control.cam_exclude[self.cam_name] = 1
            print('excluded camera: ', self.cam_name)
        else:
            self.main.control.cam_exclude[self.cam_name] = 0
            print('re-included camera: ', self.cam_name)


class VideoCanvas(QtWidgets.QLabel):
    """This class creates the video-canvas-widget in the mainwindow by subclassing the QLabel-Widget"""
    def __init__(self, main, parent=None):
        QtWidgets.QLabel.__init__(self, parent)
        self.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setFrameStyle(QtWidgets.QFrame.Panel | QtWidgets.QFrame.Sunken)
        
        self.mutex = QtCore.QMutex()
        self.photo = False
        self.main = main

        self.video_skipstep_coarse = 4
        self.video_skipstep = self.video_skipstep_coarse  # sets display quality: display only every nth pixel
        self.left_x = 0
        self.right_x = 0
        self.top_y = 0
        self.bottom_y = 0
        self.focusindex = 0
        self.focus = 1.0
        self.focuslevels = 100
        self.focusfactors = [0.95**x for x in range(self.focuslevels+1)]

        # mouse event filter
        self.mousefilter = self.installEventFilter(self)

    def eventFilter(self, source, event):
        """ capture mouse events on the label """
        if (event.type() == QtCore.QEvent.MouseMove and source is self):
            pos = event.pos()
            # print('mouse move: (%d, %d)' % (pos.x(), pos.y()))
        elif (event.type() == QtCore.QEvent.Wheel and source is self):
            # print('mouse wheel: {}'.format(event.delta()))
            self.mutex.lock()
            self.set_focus(event.angleDelta(), event.pos())
            self.mutex.unlock()
            # self.set_focus(event.delta(), event.pos())
        return QtWidgets.QWidget.eventFilter(self, source, event)

    def set_focus(self, delta, pos):
        delta = delta.y()
        index = delta / 120
        xm, ym = 1.*pos.x()/self.width(), 1.*pos.y()/self.height()  # relative position
        if index > 0 and self.focusindex < self.focuslevels:
            # zoom in
            self.focusindex += index
            if self.focusindex > self.focuslevels: 
                self.focusindex = self.focuslevels
            self.focus = self.focusfactors[self.focusindex]

        elif index < 0 and self.focusindex > 0:
            # zoom out
            self.focusindex += index
            if self.focusindex < 0: 
                self.focusindex = 0
            self.focus = self.focusfactors[self.focusindex]
        else:
            return

        # mouse position in image coordinates
        xma = int(xm*self.frame_x)
        yma = int(ym*self.frame_y)

        # set the new view size (i.e. half of it)
        xwidth = int(self.frame_x*self.focus)/2
        ywidth = int(self.frame_y*self.focus)/2

        # correct mouse position in respoect to image
        if xma - xwidth < 0: xma = xwidth
        if xma + xwidth > self.frame_x: xma = self.frame_x - xwidth
        if yma - ywidth < 0: yma = ywidth
        if yma + ywidth > self.frame_y: yma = self.frame_y - ywidth

        # offsets
        # x0 = xma - xwidth
        # x1 = xma + xwidth
        # y0 = yma - ywidth
        # y1 = yma + ywidth
        # print x0, x1, x1-x0
        # print y0, y1, y1-y0
        # print
        self.left_x = xma - xwidth
        self.right_x = self.frame_x - (xma+xwidth)
        self.top_y = yma - ywidth
        self.bottom_y = self.frame_y - (yma+ywidth)

    def move_focus(self):
        pass

    def set_display_quality(self, val):
        self.mutex.lock()
        if val:
            self.video_skipstep = 1
        else:
            self.video_skipstep = self.video_skipstep_coarse
        self.mutex.unlock()

    def save_photo(self):
        # save the next frame to where ever
        self.mutex.lock()
        self.photo = True
        self.mutex.unlock()

    def setImage(self, frame):

        if self.photo:
            self.photo = False
            im = Image.fromarray(frame)
            now = datetime.now().strftime("%Y-%m-%d__%H-%M-%S.%f")[:-3]
            if self.main.control.save_dir == None:
                path = os.getcwd()
            else:
                path = self.main.control.save_dir
            fn = os.path.join(path, now+'.png')
            im.save(fn)

        # set zoom and display quality
        self.frame_y, self.frame_x = frame.shape[0:2]
        right_x = self.frame_x -self.right_x
        bottom_y = self.frame_y-self.bottom_y

        # frame = frame[self.top_y:bottom_y:self.video_skipstep, self.left_x:right_x:self.video_skipstep]
        self.mutex.lock()
        frame = frame[self.top_y:bottom_y,:]
        frame = frame[::self.video_skipstep,:]
        frame = frame[:, self.left_x:right_x]
        frame = frame[:, ::self.video_skipstep]
        self.mutex.unlock()

        if len(frame.shape) == 2:
            form = QtGui.QImage.Format_Indexed8
        elif len(frame.shape) != 2:
            form = QtGui.QImage.Format_RGB888
        else:
            return

        # a note for later:
        # COLORTABLE=[]
        # for i in range(256): COLORTABLE.append(QtGui.qRgb(i/4,i,i/2))
        # image.setColorTable(COLORTABLE)

        # display frame
        image = QtGui.QImage(frame.ravel(), frame.shape[1],frame.shape[0], form)
        pixmap = QtGui.QPixmap(image)

        self.setPixmap(pixmap.scaled(self.size(), Qt.KeepAspectRatio))


