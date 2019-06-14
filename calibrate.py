import numpy as np
import pandas as pd
from PyQt5 import QtCore
from scipy.interpolate import UnivariateSpline as us

__author__ = 'Janez Presern'


class FitSpeed(QtCore.QObject):

    def __init__(self, table_fn, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.calib_data = pd.read_csv(table_fn)
        self.spl = us(self.calib_data.pw, self.calib_data.speed, s=0, k=3)
        self.pw_range = np.arange(min(self.calib_data.pw), max(self.calib_data.pw) + 1, 1)
        # self.speed_range = np.arange(min(self.calib_data.speed), max(self.calib_data.speed) + 1, 0.01)
        self.speed_range = np.round(self.spl(self.pw_range), 2)
        print("\n## Name of the wind ##")
        print("Wind calibration lookup-table precomputed and loaded")

    def look_up(self, pw):

        return self.y[self.pw_range == pw]

    def look_up_pw(self, speed):

        idx = (np.abs(self.speed_range - speed)).argmin()
        return self.pw_range[idx]

    def look_up_pwm(self):
        return int(self.calib_data.loc[0, "pwm"])

    def look_up_arm(self):
        return int(self.calib_data.loc[0, "arm"])

    def look_up_min_pw(self):
        return int(self.calib_data.loc[0, "pw"])

    def look_up_max_pw(self):
        return int(self.calib_data.tail(1)["pw"])

    def look_up_speed(self, pw):

        idx = (np.abs(self.pw_range - pw)).argmin()
        return self.speed_range[idx]

    def look_up_max_speed(self):

        return self.calib_data.tail(1)["speed"].values[0]

    def look_up_min_speed(self):

        return self.calib_data.loc[0, "speed"]
