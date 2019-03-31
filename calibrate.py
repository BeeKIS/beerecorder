import numpy as np
import pandas as pd
from PyQt5 import QtCore
from scipy.interpolate import UnivariateSpline as us

__author__ = 'Janez Presern'


class FitSpeed(QtCore.QObject):

    def __init__(self, table_fn, parent=None):
        QtCore.QObject.__init__(self, parent)
        self.calib_data = pd.read_csv(table_fn)
        self.spl = us(self.calib_data.pwm, self.calib_data.speed, s=0, k=3)
        self.pwm_range = np.arange(min(self.calib_data.pwm), max(self.calib_data.pwm) + 1, 1)
        self.y = self.spl(self.pwm_range)

    def look_up(self, pwm):

        return self.y[self.pwm_range == pwm]

    def look_up_pwm(self, speed):
        idx = (np.abs(self.y - speed)).argmin()
        return self.pwm_range[idx]

#
# if __name__ == "__main__":
#
#     fs = FitSpeed("./calibrations/calibrationKV410.csv")
#     fs.look_up(500)