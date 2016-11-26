import os
from PIL import Image
from datetime import datetime
import numpy as np
from PIL import ImageQt as iqt
try:
    from PyQt4 import QtGui, QtCore, Qt
except Exception, details:
    print 'Unfortunately, your system misses the PyQt4 packages.'
    quit()


class VideoTab(QtGui.QWidget):
    """This class creates the a Tab for Camera data"""
    def __init__(self, main, cam_name, parent=None):
        QtGui.QWidget.__init__(self, parent)
        self.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)

        self.cam_name = cam_name
        self.main = main

        # generate layout
        self.setLayout(QtGui.QHBoxLayout())

        self.canvas = VideoCanvas(self.main, parent=self)
        self.layout().addStretch()
        self.layout().addWidget(self.canvas)
        self.layout().addStretch()

        # options layout
        videoOptionLayout = QtGui.QVBoxLayout()
        self.layout().addLayout(videoOptionLayout)
        
        # framerate indicator
        self.framerate_counter = QtGui.QLabel('', self)
        font = self.framerate_counter.font()
        font.setPointSize(self.main.label_font_size)
        self.framerate_counter.setFont(font)
        videoOptionLayout.addWidget(self.framerate_counter)

        # checkbox for coarse and high display quality
        self.quality_checkbox = QtGui.QCheckBox('High Res display', self)
        videoOptionLayout.addWidget(self.quality_checkbox)
        self.quality_checkbox.stateChanged.connect(self.canvas.set_display_quality)
        # self.connect(self.quality_checkbox, QtCore.SIGNAL('toggled()'), self.canvas.set_display_quality)

        # set framerate
        # ...

        # modify ROI button
        self.roi_button = QtGui.QPushButton('Modify ROI')
        videoOptionLayout.addWidget(self.roi_button)
        self.roi_button.clicked.connect(self.modify_roi)
        # connection

        # photo button
        self.photo_button = QtGui.QPushButton('Snapshot!')
        videoOptionLayout.addWidget(self.photo_button)
        self.photo_button.clicked.connect(self.canvas.save_photo)
        # connection

    def get_available_framerates(self):
        pass

    def set_framerate(self, val):
        pass

    def modify_roi(self):
        pass


class VideoCanvas(QtGui.QLabel):
    """This class creates the video-canvas-widget in the mainwindow by subclassing the QLabel-Widget"""
    def __init__(self, main, parent=None):
        QtGui.QLabel.__init__(self, parent)
        self.setAlignment(Qt.Qt.AlignVCenter | Qt.Qt.AlignHCenter)
        self.setSizePolicy(Qt.QSizePolicy.Expanding, Qt.QSizePolicy.Expanding)
        self.setFrameStyle(Qt.QFrame.Panel | Qt.QFrame.Sunken)
        
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
        self.focusfactors = [0.95**x for x in xrange(self.focuslevels+1)]

        # mouse event filter
        self.mousefilter = self.installEventFilter(self)

    def eventFilter(self, source, event):
        """ capture mouse events on the label """
        if (event.type() == QtCore.QEvent.MouseMove and source is self):
            pos = event.pos()
            # print('mouse move: (%d, %d)' % (pos.x(), pos.y()))
        elif (event.type() == QtCore.QEvent.Wheel and source is self):
            # print('mouse wheel: {}'.format(event.delta()))
            self.set_focus(event.delta(), event.pos())
        return QtGui.QWidget.eventFilter(self, source, event)

    def set_focus(self, delta, pos):
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
        # save the next frame to whereever
        self.mutex.lock()
        self.photo = True
        self.mutex.unlock()

    def setImage(self, frame):

        if self.photo:
            self.photo = False
            im = Image.fromarray(frame)
            now = datetime.now().strftime("%Y-%m-%d__%H-%M-%S.%f")[:-3]
            if self.main.save_dir == None:
                path = os.getcwd()
            else:
                path = self.main.save_dir
            fn = os.path.join(path, now+'.png')
            im.save(fn)

        # set zoom and display quality
        self.frame_y, self.frame_x = frame.shape
        right_x = self.frame_x -self.right_x
        bottom_y = self.frame_y-self.bottom_y
        frame = frame[self.top_y:bottom_y:self.video_skipstep, self.left_x:right_x:self.video_skipstep]

        # display frame
        pixmap = QtGui.QPixmap.fromImage(iqt.ImageQt(Image.fromarray(frame)))
        self.setPixmap(pixmap.scaled(self.size(), Qt.Qt.KeepAspectRatio))

    # def resizeEvent(self, QResizeEvent):
    #     """ override in-built Qt function """
    #     self.resizeImage()

    # def resizeImage(self):
    #     self.setPixmap(self.pixmap.scaled(self.size(), Qt.Qt.KeepAspectRatio))
