#! /usr/bin/python

#
# Qt example for VLC Python bindings
# Copyright (C) 2009-2010 the VideoLAN team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
#

import sys
import re
import user
import vlc
from PySide import QtGui, QtCore
from player_directories import SHARED_TOOLS_DIR, CURRENT_PROJECT_DIR

if __name__ == "__main__":
    sys.path = sys.path + [SHARED_TOOLS_DIR] + [CURRENT_PROJECT_DIR]

from standard_package.mywidgets import qHotField, qmy_button

JUMP_SIZE = 3
RATE_CHANGE_AMOUNT = .05

def convert_with_zero(the_val):
    result = str(the_val)
    if len(result) < 2:
        result = "0" + result
    return result

def convert_ms_to_timecode(ms):
    seconds = ms / 1000
    hours = seconds / 3600
    minutes = (seconds - hours * 3600) / 60
    remaining_seconds = seconds - hours * 3600 - minutes * 60
    hour_str = str(hours)
    return "%s:%s:%s" % (convert_with_zero(hours), convert_with_zero(minutes), convert_with_zero(remaining_seconds))

def convert_timecode_to_ms(timecode):
    m = re.search("(..)\:(..)\:(..)", timecode)
    return 1000 * (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3)))

class PlayerWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setCentralWidget(Player())

class Player(QtGui.QWidget):
    """A simple Media Player using VLC and Qt
    """
    def __init__(self, parent=None):

        if parent is None:
            QtGui.QWidget.__init__(self)
        else:
            QtGui.QWidget.__init__(self, parent)
        # self.setWindowTitle("Media Player")

        # creating a basic vlc instance
        self.instance = vlc.Instance()
        # creating an empty vlc media player
        self.mediaplayer = self.instance.media_player_new()

        self.createUI()
        self.isPaused = False

    def createUI(self):
        """Set up the user interface, signals & slots
        """
        # self.widget = QtGui.QWidget(self)
        # self.setCentralWidget(self.widget)

        # In this widget, the video will be drawn
        # if sys.platform == "darwin": # for MacOS
        #     self.videoframe = QtGui.QMacCocoaViewContainer(0)
        # else:
        self.videoframe = QtGui.QFrame()
        self.palette = self.videoframe.palette()
        self.palette.setColor (QtGui.QPalette.Window,
                               QtGui.QColor(0,0,0))
        self.videoframe.setPalette(self.palette)
        self.videoframe.setAutoFillBackground(True)

        self.positionslider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.positionslider.setToolTip("Position")
        self.positionslider.setMaximum(1000)
        self.connect(self.positionslider,
                     QtCore.SIGNAL("sliderMoved(int)"), self.setPosition)

        self.hbuttonbox = QtGui.QHBoxLayout()
        self.playbutton = QtGui.QPushButton("Play")
        self.hbuttonbox.addWidget(self.playbutton)
        self.connect(self.playbutton, QtCore.SIGNAL("clicked()"),
                     self.PlayPause)

        self.stopbutton = QtGui.QPushButton("Stop")
        self.hbuttonbox.addWidget(self.stopbutton)
        self.connect(self.stopbutton, QtCore.SIGNAL("clicked()"),
                     self.Stop)


        self.openbutton = QtGui.QPushButton("Open")
        self.hbuttonbox.addWidget(self.openbutton)
        self.connect(self.openbutton, QtCore.SIGNAL("clicked()"),
                     self.OpenFile)

        qmy_button(self.hbuttonbox, self.jump_video_backward, "<-")
        qmy_button(self.hbuttonbox, self.jump_video_forward, "->")

        self.hbuttonbox.addStretch(1)
        # self.volumeslider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        # self.volumeslider.setMaximum(100)
        # self.volumeslider.setValue(self.mediaplayer.audio_get_volume())
        # self.volumeslider.setToolTip("Volume")
        # self.hbuttonbox.addWidget(self.volumeslider)
        # self.connect(self.volumeslider,
        #              QtCore.SIGNAL("valueChanged(int)"),
        #              self.setVolume)

        self.rate_field = qHotField("rate", float, 1.0, pos="top", min_size=40, max_size=40)
        self.hbuttonbox.addWidget(self.rate_field)
        self.rateslider = QtGui.QSlider(QtCore.Qt.Horizontal, self)
        self.rateslider.setMaximum(200)
        self.rateslider.setValue(100)
        self.rateslider.setToolTip("Play Rate")
        self.hbuttonbox.addWidget(self.rateslider)
        self.connect(self.rateslider,
                     QtCore.SIGNAL("valueChanged(int)"),
                     self.setRate)

        self.current_time = qHotField("time", str, "0", min_size=75, max_size=75)
        self.hbuttonbox.addWidget(self.current_time)

        self.vboxlayout = QtGui.QVBoxLayout()
        self.vboxlayout.setContentsMargins(0, 0, 0, 0)
        self.vboxlayout.addWidget(self.videoframe)
        self.vboxlayout.addWidget(self.positionslider)
        self.vboxlayout.addLayout(self.hbuttonbox)

        self.setLayout(self.vboxlayout)

        open = QtGui.QAction("&Open", self)
        self.connect(open, QtCore.SIGNAL("triggered()"), self.OpenFile)
        exit = QtGui.QAction("&Exit", self)
        self.connect(exit, QtCore.SIGNAL("triggered()"), sys.exit)
        # menubar = self.menuBar()
        # filemenu = menubar.addMenu("&File")
        # filemenu.addAction(open)
        # filemenu.addSeparator()
        # filemenu.addAction(exit)

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(200)
        self.connect(self.timer, QtCore.SIGNAL("timeout()"),
                     self.updateUI)

    def jump_video_forward(self):
        self.mediaplayer.set_time(self.mediaplayer.get_time() + JUMP_SIZE * 1000)
        self.updateTime()

    def jump_video_backward(self):
        self.mediaplayer.set_time(self.mediaplayer.get_time() - JUMP_SIZE * 1000)
        self.updateTime()

    def PlayPause(self):
        """Toggle play/pause status
        """
        if self.mediaplayer.is_playing():
            self.mediaplayer.pause()
            self.playbutton.setText("Play")
            self.isPaused = True
        else:
            if self.mediaplayer.play() == -1:
                self.OpenFile()
                return
            self.mediaplayer.play()
            self.playbutton.setText("Pause")
            self.timer.start()
            self.isPaused = False

    def Stop(self):
        """Stop player
        """
        self.mediaplayer.stop()
        self.playbutton.setText("Play")

    def OpenFile(self, filename=None):
        """Open a media file in a MediaPlayer
        """
        if filename is None:
            # filename = QtGui.QFileDialog.getOpenFileName(self, "Open File", user.home)
            filename = QtGui.QFileDialog.getOpenFileName(self, "Open File")[0]
        if not filename:
            return

        # create the media
        self.media = self.instance.media_new(unicode(filename))
        # put the media in the media player
        self.mediaplayer.set_media(self.media)

        # parse the metadata of the file
        self.media.parse()
        # set the title of the track as window title
        self.setWindowTitle(self.media.get_meta(0))

        # the media player has to be 'connected' to the QFrame
        # (otherwise a video would be displayed in it's own window)
        # this is platform specific!
        # you have to give the id of the QFrame (or similar object) to
        # vlc, different platforms have different functions for this
        if sys.platform == "linux2": # for Linux using the X Server
            self.mediaplayer.set_xwindow(self.videoframe.winId())
        elif sys.platform == "win32": # for Windows
            self.mediaplayer.set_hwnd(self.videoframe.winId())
        elif sys.platform == "darwin": # for MacOS
            self.mediaplayer.set_nsobject(self.videoframe.winId())
        self.setPosition(1)

    def setVolume(self, Volume):
        """Set the volume
        """
        self.mediaplayer.audio_set_volume(Volume)
        # self.mediaplayer.set_rate(Volume)

    def setRate(self, rate):
        """Set the volume
        """
        self.mediaplayer.set_rate(1.0 * rate / 100)
        self.update_rate_field()

    def reset_rate(self):
        self.setRate(100)

    def increase_rate(self):
        self.change_rate(RATE_CHANGE_AMOUNT)

    def decrease_rate(self):
        self.change_rate(-1 * RATE_CHANGE_AMOUNT)

    def change_rate(self, amount):
        self.mediaplayer.set_rate(self.mediaplayer.get_rate() + amount)
        self.update_rate_field()

    def change_rate_from_field(self):
        self.change_rate(self.rate_field.value)

    def update_rate_field(self):
        self.rate_field.value = round(self.mediaplayer.get_rate(), 2)

    def setPosition(self, position):
        """Set the position
        """
        # setting the position to where the slider was dragged
        self.mediaplayer.set_position(position / 1000.0)
        self.updateUI()
        # the vlc MediaPlayer needs a float value between 0 and 1, Qt
        # uses integer variables, so you need a factor; the higher the
        # factor, the more precise are the results
        # (1000 should be enough)

    def setTimeCode(self, timecode):
        self.mediaplayer.set_time(convert_timecode_to_ms(timecode))
        self.updateUI()

    def updateTime(self):
        self.current_time.value = self.getCurrentTimeCode()

    def getCurrentTimeCode(self):
        return convert_ms_to_timecode(self.mediaplayer.get_time())

    def getPosition(self):
        return self.mediaplayer.get_time()

    def updateUI(self):
        """updates the user interface"""
        # setting the slider to the desired position
        self.positionslider.setValue(self.mediaplayer.get_position() * 1000)
        self.updateTime()
        self.update_rate_field()
        # self.rateslider.setValue(int(self.mediaplayer.get_rate() * 100))

        if not self.mediaplayer.is_playing():
            # no need to call this function if nothing is played
            self.timer.stop()
            if not self.isPaused:
                # after the video finished, the play button stills shows
                # "Pause", not the desired behavior of a media player
                # this will fix it
                self.Stop()


# if __name__ == "__main__":
#     app = QtGui.QApplication(sys.argv)
#     player_window = PlayerWindow()
#     player_window.show()
#     player_window.resize(640, 480)
#     # player.OpenFile("/Users/bls910/PycharmProjects/vlcbind/examples/j3.mp4")
#     # if sys.argv[1:]:
#     #     player.OpenFile(sys.argv[1])
#     sys.exit(app.exec_())