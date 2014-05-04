__author__ = 'bls910'
import sys
import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'

import pylab

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QTAgg as NavigationToolbar
from PySide.QtGui import QPixmap, QDialog, QVBoxLayout, QApplication
from mywidgets import qmy_button
from PySide import QtCore
from matplotlib.font_manager import FontProperties

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

def bar_chart(code_matrix, trans_names, code_names, show_it=True, show_trans_names=True):
        ldata = {}
        i = 0
        for code in code_names:
            ldata[code] = [code_matrix[j, i] for j in range(len(trans_names))]
            i += 1
        ind = pylab.arange(len(trans_names))
        width = 1.0 / (len(code_names) + 1)
        lcolors = ['red', 'green', 'blue']
        for c in range(len(code_names)):
            pylab.bar(ind + c * width, ldata[code_names[c]], width, color=lcolors[c])
        if show_trans_names:
            pylab.xticks(ind + .5, trans_names, size="x-small", rotation=-45)
        else:
            pylab.xticks(pylab.arange(len(trans_names)))
        pylab.xlim(xmax=len(trans_names))
        pylab.grid(True)
        if show_it:
            pylab.show()

def generalized_bar_chart(code_matrix, trans_names, code_names, show_it=True, show_trans_names=False, color_map = "jet", legend_labels = None, horizontal_grid = True):
    ldata = {}
    i = 0
    fig = pylab.gcf()
    fig.set_facecolor("white")
    code_names = [c for c in range(code_matrix.shape[1])]
    for code in range(len(code_names)):
        ldata[code] = [code_matrix[j, i] for j in range(len(trans_names))]
        i = i + 1
    ind = pylab.arange(len(trans_names))
    width = 1.0 / (len(code_names) + 1)
    traditional_colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'black', 'grey', 'cyan', 'coral']

    if color_map == "AA_traditional_":
        lcolors = traditional_colors
    else:
        cNorm = pylab.cm.colors.Normalize(vmin = 1, vmax = len(code_names))
        comap = pylab.cm.get_cmap(color_map)
        scalar_map = pylab.cm.ScalarMappable(norm = cNorm, cmap = comap)
        lcolors = [scalar_map.to_rgba(idx + 1) for idx in range(len(code_names))]

    the_bars = []

    for c in range(len(code_names)):
        new_bars = pylab.bar(ind + (c + .5) * width, ldata[code_names[c]], width, color=lcolors[c % (len(lcolors))])
        the_bars.append(new_bars[0])
        # bar_groups.append(bars)
    if show_trans_names:
        pylab.xticks(ind + .5, trans_names, size="x-small", rotation= -45)
    else:
        pylab.grid(b = horizontal_grid, which = "major", axis = 'y')
        ax = pylab.subplot(111)
        # pylab.minorticks_on()
        pylab.xticks(ind + .5, ind + 1)
        for i in ind[1:]:
            ax.axvline(x = i, linestyle = "--", linewidth = .25, color = 'black')

    if legend_labels != None:
        fontP =FontProperties()
        fontP.set_size('small')
        # pylab.figlegend(the_bars, legend_labels, "best")
        ax = pylab.subplot(111)
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.8, box.height *0.8])

        # Put a legend to the right of the current axis
        ax.legend(the_bars, legend_labels, loc='center left', bbox_to_anchor=(1, 0.5), prop = fontP)
    pylab.xlim(xmax=len(trans_names))
    # pylab.grid(True)
    if show_it:
        pylab.show()