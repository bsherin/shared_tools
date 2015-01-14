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
from PySide.QtGui import QPixmap, QDialog, QVBoxLayout, QApplication, QHBoxLayout, QWidget, QFileDialog
from mywidgets import qmy_button, qHotField
from PySide import QtCore, QtGui
from matplotlib.font_manager import FontProperties
import numpy as np
import sys
import re
import os
import pickle

color_map_specs = [["Yellows", {'red':[(0.0, 0.0, 1.0), (1.0,  1.0, 1.0)],
                                 'green': [(0.0, 0.0, 1.0), (1.0, 1.0, 1.0)],
                                 'blue': [(0.0, 0.0, 1.0), (1.0, 0.0, 0.0)]}],
                   ["NeonPurples", {'red':[(0.0, 0.0, 1.0), (1.0, 1.0, 1.0)],
                                    'green': [(0.0, 0.0, 1.0), (1.0, 0.0, 1.0)],
                                    'blue': [(0.0, 0.0, 1.0), (1.0, 1.0, 0.0)]}],
                   ["LightBlues",{'red':[(0.0, 1.0, 1.0), (1.0,  0.0, 1.0)],
                                    'green': [(0.0, 1.0, 1.0), (1.0, 1.0, 1.0)],
                                    'blue': [(0.0, 1.0, 1.0), (1.0, 1.0, 0.0)]}],
                   ["NeonBlues",{'red':[(0.0, 1.0, 1.0), (1.0,  0.25, 1.0)],
                                    'green': [(0.0, 1.0, 1.0), (1.0, .25, 1.0)],
                                    'blue': [(0.0, 1.0, 1.0), (1.0, 1.0, 0.0)]}],
                   ["NeonGreens", {'red':[(0.0, 0.0, 1.0), (1.0,  .25, 1.0)],
                                   'green': [(0.0, 0.0, 1.0),(1.0, 1.0, 1.0)],
                                   'blue': [(0.0, 0.0, 1.0), (1.0, .25, 0.0)]}],
                   ["Browns", {'red':[(0.0, 0.0, 1.0), (1.0,  .7, 1.0)],
                               'green': [(0.0, 0.0, 1.0), (1.0, .45, 1.0)],
                               'blue': [(0.0, 0.0, 1.0), (1.0, .25, 0.0)]}]]

for spec in color_map_specs:
    pylab.register_cmap(cmap=LinearSegmentedColormap(spec[0], spec[1]))

class MyNavToolbar(NavigationToolbar):
    mytoolitems = (('Copy', 'Copy the figure', 'copy', 'do_copy'),
                   ('Annotate', 'Annotate a segment', 'annotation', 'do_annotate'),)

    def __init__(self, canvas, win):
        NavigationToolbar.__init__(self, canvas, win)
        self.win = win
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)
        imagedir = os.path.join(dir_path,'images')

        for text, tooltip_text, image_file, callback in self.mytoolitems:
            if text is None:
                self.addSeparator()
            else:
                a = self.addAction(QtGui.QIcon(os.path.join(imagedir, image_file + ".png")),
                                         text, getattr(self, callback))
                self._actions[callback] = a
                if callback in ['zoom', 'pan']:
                    a.setCheckable(True)
                if tooltip_text is not None:
                    a.setToolTip(tooltip_text)

    def do_copy(self):
        pixmap = QPixmap.grabWidget(self.canvas)
        QApplication.clipboard().setPixmap(pixmap)

    def do_annotate(self):
        self.win.do_annotate()


class MplWindow(QDialog):
    def __init__(self, fig):
        QDialog.__init__(self)
        self.fig = fig
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

    def do_annotate(self):
        self.fig.annotate_me()


class GeneralizedBarChart(Figure):
    def __init__(self, code_matrix, trans_names, code_names, show_it=True, show_trans_names=False, color_map = "jet", legend_labels = None, title=None, horizontal_grid = True):
        Figure.__init__(self, facecolor="white", figsize=(12, 4))
        ldata = {}
        self.subplots_adjust(left=.05, bottom=.15, right=.98, top=.95)
        code_names = [c for c in range(code_matrix.shape[1])]
        for i, code in enumerate(range(len(code_names))):
            ldata[code] = [code_matrix[j, i] for j in range(len(trans_names))]
        ind = np.arange(len(trans_names))
        width = 1.0 / (len(code_names) + 1)
        traditional_colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'black', 'grey', 'cyan', 'coral']

        ax = self.add_subplot(111)
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
            self.show()

class ScatterList(Figure):
    def __init__(self, x_list, y_list, title=None):
        Figure.__init__(self, facecolor="white")
        ax = self.add_subplot(111)
        if title is not None:
            ax.set_title(title, fontsize=10)
        ax.scatter(x_list, y_list)
        ind = np.arange(len(x_list)) + 1
        ax.set_xticks(ind)
        ax.set_xlim(left=0, right=len(x_list) + 1)

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

class AnnotationDialog(QDialog):
    def __init__(self, fig):
        QDialog.__init__(self)
        self.fig = fig
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        top_widget = QWidget()
        bottom_widget = QWidget()
        main_layout.addWidget(top_widget)
        main_layout.addWidget(bottom_widget)
        top_layout = QHBoxLayout()
        bottom_layout = QHBoxLayout()
        top_widget.setLayout(top_layout)
        bottom_widget.setLayout(bottom_layout)

        self.atext = qHotField("annotation", unicode, "the_text")
        top_layout.addWidget(self.atext)
        self.segment_number = qHotField("Segment", int, 1)
        top_layout.addWidget(self.segment_number)
        qmy_button(top_layout, self.annotate_it, "annotate")
        self.over = qHotField("over", int, -70)
        bottom_layout.addWidget(self.over)
        self.up = qHotField('up', int, 30)
        bottom_layout.addWidget(self.up)
        qmy_button(bottom_layout, self.remove_annotations, "remove all")
        qmy_button(bottom_layout, self.remove_last_annotation, "remove last")
        self.annotations = []

    def annotate_it(self):
        self.annotations.append(self.fig.create_annotation(self.atext.value, self.segment_number.value, self.over.value, self.up.value))
        self.fig.canvas.draw()

    def remove_annotations(self):
        for an in self.annotations:
            an.remove()
        self.fig.canvas.draw()

    def remove_last_annotation(self):
        self.annotations[-1].remove()
        self.annotations.pop()
        self.fig.canvas.draw()

class SegmentedHeatmap(Figure):
    def __init__(self, code_matrix, row_labels, title=None, show_it=True, gray_only=False, tailored_cmap_list=None):
        Figure.__init__(self, figsize=(8,1))
        self.dialogs = []
        (ntopics, nsegments) = code_matrix.shape
        if gray_only:
            cmap_list = ["Greys"]
        elif tailored_cmap_list is not None:
            cmap_list = tailored_cmap_list
        else:
            cmap_list = ['Reds', "Oranges", 'Greens', "Blues", 'Purples', "Greys"]
        axes = []
        for j in range(ntopics):
            axes.append(self.add_subplot(ntopics, 1, j + 1))
            if j < ntopics:
                axes[j].set_xticks([])
        self.subplots_adjust(left=.15, bottom=.2, right=.98, top=.80)
        self.set_facecolor("white")
        # pylab.figure(fig.number)
        ind = np.arange(nsegments)

        axes[-1].set_xticks(ind)
        axes[-1].get_xaxis().set_ticklabels(ind + 1, size="x-small")

        # pylab.xticks(ind, ind + 1, size="small")

        for the_row in range(ntopics):
            for the_seg in range(nsegments):
                if code_matrix[the_row, the_seg] < 0:
                    code_matrix[the_row, the_seg] = 0

        if title is not None:
            axes[0].set_title(title, fontsize=10)

        vmax = np.amax(code_matrix)
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
            ax.imshow(the_row, aspect = "auto", cmap=get_cmap(cmap_list[topic % (len(cmap_list))]), interpolation='nearest', vmin=0, vmax=vmax)
            if row_labels is not None:
                the_label = row_labels[topic]
            else:
                the_label = "Topic " + str(topic)
            ax.set_ylabel(the_label, rotation="horizontal", horizontalalignment='right', verticalalignment='center', fontsize=10)

    def annotate_me(self):
        adialog = AnnotationDialog(self)
        adialog.show()
        self.dialogs.append(adialog)

    def create_annotation(self, the_text, the_segment, over, up):
        ax = self.axes[0]
        the_text = re.sub(r"\\n", "\n", the_text)
        return ax.annotate(the_text,
                           xy=(the_segment, 0),
                           xycoords='data',
                           xytext=(over, up),
                           textcoords='offset points',
                           arrowprops=dict(arrowstyle="->",
                           connectionstyle="angle, angleA=0, angleB=-90, rad=5"),
                           fontsize=10)

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