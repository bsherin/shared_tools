__author__ = 'bls910'
import sys
import matplotlib
matplotlib.use('Qt4Agg')
matplotlib.rcParams['backend.qt4']='PySide'
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.colors import Normalize as mpl_Normalize
from matplotlib.cm import get_cmap, ScalarMappable
from matplotlib.figure import Figure

import pylab

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas, NavigationToolbar2QTAgg as NavigationToolbar
from PySide.QtGui import QPixmap, QDialog, QVBoxLayout, QApplication
from mywidgets import qmy_button
from PySide import QtCore
from matplotlib.font_manager import FontProperties
import numpy as np
import sys

cdictyellow = {'red':[(0.0, 0.0, 1.0), (1.0,  1.0, 1.0)],
         'green': [(0.0, 0.0, 1.0), (1.0, 1.0, 1.0)],
         'blue': [(0.0, 0.0, 1.0), (1.0, 0.0, 0.0)]}
my_yellow_cmap = LinearSegmentedColormap("Yellows", cdictyellow)
pylab.register_cmap(cmap=my_yellow_cmap)


class MyNavToolbar(NavigationToolbar):
    def __init__(self, canvas, win):
        NavigationToolbar.__init__(self, canvas, win)

    def do_copy(self):
        pixmap = QPixmap.grabWidget(self.canvas)
        QApplication.clipboard().setPixmap(pixmap)

if sys.platform == "darwin":
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
        if sys.platform == "darwin": # The navivation toolbar doesn't seem to work on linux
            mynav = MyNavToolbar(self.canvas, self)
            lo.addWidget(mynav)
        else:
            qmy_button(lo, self.do_copy, "copy")
        lo.addWidget(self.canvas)

    def do_copy(self): # Need this in case there's no navigation toolbar.
        pixmap = QPixmap.grabWidget(self.canvas)
        QApplication.clipboard().setPixmap(pixmap)

def generalized_bar_chart(code_matrix, trans_names, code_names, show_it=True, show_trans_names=False, color_map = "jet", legend_labels = None, title=None, horizontal_grid = True):
    ldata = {}
    fig = pylab.figure(facecolor="white", figsize=(12, 4))
    fig.subplots_adjust(left=.05, bottom=.15, right=.98, top=.95)
    code_names = [c for c in range(code_matrix.shape[1])]
    for i, code in enumerate(range(len(code_names))):
        ldata[code] = [code_matrix[j, i] for j in range(len(trans_names))]
    ind = np.arange(len(trans_names))
    width = 1.0 / (len(code_names) + 1)
    traditional_colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'black', 'grey', 'cyan', 'coral']

    ax = fig.add_subplot(111)
    if title is not None:
        ax.set_title(title, fontsize=10)

    if color_map == "AA_traditional_":
        lcolors = traditional_colors
    else:
        cNorm = mpl_Normalize(vmin = 1, vmax = len(code_names))
        comap = get_cmap(color_map)
        scalar_map = ScalarMappable(norm = cNorm, cmap = comap)
        lcolors = [scalar_map.to_rgba(idx + 1) for idx in range(len(code_names))]

    the_bars = []

    for c in range(len(code_names)):
        new_bars = ax.bar(ind + (c + .5) * width, ldata[code_names[c]], width, color=lcolors[c % (len(lcolors))])
        the_bars.append(new_bars[0])
        # bar_groups.append(bars)
    if show_trans_names:
        ax.set_xticks(ind + .5)
        ax.set_xticklabels(trans_names, size="x-small", rotation= -45)
    else:
        ax.grid(b = horizontal_grid, which = "major", axis = 'y')
        ax.set_xticks(ind + .5)
        ax.set_xticklabels(ind + 1, size="x-small")
        for i in ind[1:]:
            ax.axvline(x = i, linestyle = "--", linewidth = .25, color = 'black')

    if legend_labels != None:
        fontP =FontProperties()
        fontP.set_size('small')
        box = ax.get_position()
        ax.set_position([box.x0, box.y0, box.width * 0.825, box.height])
        # Put a legend to the right of the current axis
        ax.legend(the_bars, legend_labels, loc='center left', bbox_to_anchor=(1, 0.5), prop = fontP)
    ax.set_xlim(right=len(trans_names))

    if show_it:
        fig.show()
    return fig

def multi_color_heatmap(code_matrix, row_labels, title=None, show_it=True):
    (ntopics, nsegments) = code_matrix.shape
    cmap_list = ['Reds', "Oranges", 'Greens', "Blues", 'Purples', "Greys"]
    fig, axes = pylab.subplots(nrows=ntopics, sharex=True, sharey=True, figsize=(8,1))
    fig.subplots_adjust(left=.15, bottom=.2, right=.98, top=.80)
    fig.set_facecolor("white")
    # pylab.figure(fig.number)
    ind = np.arange(nsegments)

    axes[-1].set_xticks(ind)
    axes[-1].get_xaxis().set_ticklabels(ind + 1, size="x-small")

    # pylab.xticks(ind, ind + 1, size="small")

    if title is not None:
        axes[0].set_title(title, fontsize=10)
    for topic in range(ntopics):
        ax = axes[topic]
        ax.set_yticks([])
        # pylab.sca(ax)
        ax.tick_params(length=0)
        for i in ind:
            ax.axvline(x=i+.5, linestyle = "-", linewidth = .25, color = 'black')
        for spine in ax.spines.itervalues():
            spine.set_visible(False)
        the_row = np.vstack((code_matrix[topic], code_matrix[topic]))
        ax.imshow(the_row, aspect = "auto", cmap=get_cmap(cmap_list[topic % (len(cmap_list))]), interpolation='nearest', vmin=0, vmax=1)
        if row_labels is not None:
            the_label = row_labels[topic]
        else:
            the_label = "Topic " + str(topic)
        ax.set_ylabel(the_label, rotation="horizontal", horizontalalignment='right', fontsize=8)
    return fig

# This is an old version
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