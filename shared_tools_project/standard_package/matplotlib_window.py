__author__ = 'bls910'
import sys
import matplotlib
import pylab

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QTAgg as NavigationToolbar
from PySide.QtGui import QPixmap, QDialog, QVBoxLayout, QApplication
from mywidgets import qmy_button
from PySide import QtCore

class MyNavToolbar(NavigationToolbar):
    def __init__(self, canvas, win):
        NavigationToolbar.__init__(self, canvas, win)

    def do_copy(self):
        pixmap = QPixmap.grabWidget(self.canvas)
        QApplication.clipboard().setPixmap(pixmap)

MyNavToolbar.toolitems += (('Copy', 'Copy the figure', 'matplotlib', 'do_copy'),)

class MplWindow(QDialog):
    def __init__(self, fig):
        QDialog.__init__(self)
        self.canvas = FigureCanvas(fig)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(p)
        lo = QVBoxLayout()
        lo.setContentsMargins(0, 0, 0, 0)
        self.setLayout(lo)
        # mynav = NavigationToolbar(self.canvas, self)
        mynav = MyNavToolbar(self.canvas, self)
        lo.addWidget(mynav)
        # qmy_button(lo, self.do_copy, "copy")
        lo.addWidget(self.canvas)

