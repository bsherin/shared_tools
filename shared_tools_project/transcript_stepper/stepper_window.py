__author__ = 'bls910'
from PySide.QtGui import QDialog, QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QFont, QMainWindow, QApplication, QShortcut, QKeySequence, QSlider, QMessageBox
from PySide import QtCore, QtGui
from PySide.QtCore import Qt
import sys

from stepper_directories import SHARED_TOOLS_DIR, CURRENT_PROJECT_DIR

if __name__ == "__main__":
    sys.path = sys.path + [SHARED_TOOLS_DIR] + [CURRENT_PROJECT_DIR]

from standard_package.mywidgets import qHotField, qmy_button, create_menu
from transcript_for_stepper import StepperTranscript
from vlcplayerproject.pyside_vlc_player import Player
import re, sys, os

def separate_turns(raw_text):
    return re.findall(r"(\w+?)\t(.*?)[\t\n\r]", raw_text)

class StepperWindow(QMainWindow):


    def __init__(self):
        QMainWindow.__init__(self)
        # filename = QFileDialog.getOpenFileName(self, "Open File")[0]
        # self.setWindowTitle(os.path.basename(filename))
        # self.transcript = StepperTranscript(filename)
        self.transcript = None
        self.outer_widget = QWidget()
        self.setCentralWidget(self.outer_widget)
        outer_layout = QHBoxLayout()
        self.outer_widget.setLayout(outer_layout)
        self.setLayout(outer_layout)
        left_layout = QVBoxLayout()
        outer_layout.addLayout(left_layout)

        display_widget = QWidget()
        left_layout.addWidget(display_widget)
        self.display_layout = QHBoxLayout()

        # self.turn = self.transcript.current_turn()
        self.time_field = qHotField("time", str, "00:00:00", min_size=75, max_size=75, pos="top", handler=self.update_time)
        self.display_layout.addWidget(self.time_field)
        self.speaker_field = qHotField("speaker", str, " ", min_size=75, max_size=75, pos="top", handler=self.update_speaker)
        self.display_layout.addWidget(self.speaker_field)
        self.utt_field = qHotField("utterance", str, " ", min_size=350, pos="top", handler=self.update_utterance, multiline=True)
        self.utt_field.setStyleSheet("font: 14pt \"Courier\";")
        # self.utt_field.efield.setFont(QFont('SansSerif', 12))
        self.display_layout.addWidget(self.utt_field)

        display_widget.setLayout(self.display_layout)
        self.display_layout.setStretchFactor(self.speaker_field, 0)
        self.display_layout.setStretchFactor(self.utt_field, 1)

        self.transcript_slider = QSlider(QtCore.Qt.Horizontal, self)
        self.display_layout.addWidget(self.transcript_slider)
        self.transcript_slider.setMaximum(100)
        self.connect(self.transcript_slider,
                     QtCore.SIGNAL("sliderMoved(int)"), self.position_transcript)
        left_layout.addWidget(self.transcript_slider)

        button_widget = TranscriptButtons(self)

        left_layout.addWidget(button_widget)
        left_layout.addWidget(QWidget())
        left_layout.setStretch(0, 0)
        left_layout.setStretch(1, 0)
        left_layout.setStretch(2, 0)
        left_layout.setStretch(3, 1)

        # video_buttons = VideoButtons(self)
        # outer_layout.addWidget(video_buttons)

        self.createKeypadButtons(self)
        left_layout.addWidget(self.keypadWidget)

        self.player = Player()
        outer_layout.addWidget(self.player)

        outer_layout.setStretch(0, 0)
        outer_layout.setStretch(1, 1)
        self.save_file_name = None

        command_list = [
            [self.open_video, "Open Video", {}, "Ctrl+o"],
            [self.open_transcript, "Open Transcript", {}, "Ctrl+t"],
            [self.play_or_pause, "Play/Pause", {}, Qt.CTRL + Qt.Key_P],
            [self.save_file, "Save", {}, "Ctrl+s"],
            [self.player.jump_video_backward, "Jump Back", {}, Qt.CTRL + Qt.Key_4],
            [self.player.jump_video_forward, "Jump Forward", {}, Qt.CTRL + Qt.Key_6],
            [self.go_to_previous_turn, "Previous", {}, "Ctrl+["],
            [self.go_to_next_turn, "Next", {}, "Ctrl+]"],
            ]

        menubar = self.menuBar()
        create_menu(self, menubar, "Stepper", command_list)

        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_0), self, self.play_or_pause)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_5), self, self.play_or_pause)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_7), self, self.go_to_previous_turn)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_9), self, self.go_to_next_turn)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_2), self, self.player.reset_rate)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_1), self, self.player.decrease_rate)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_3), self, self.player.increase_rate)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_G), self, self.sync_video_and_play)

    def createKeypadButtons(self, stepperWindow):

        self.keypadWidget = QtGui.QWidget()
        self.keypadWidget.setGeometry(QtCore.QRect(0, 0, 191, 101))
        self.keypadWidget.setMinimumSize(QtCore.QSize(191, 101))
        self.keypadWidget.setMaximumSize(QtCore.QSize(191, 101))
        self.keypadWidget.setObjectName("gridLayoutWidget")
        self.keypadGridLayout = QtGui.QGridLayout(self.keypadWidget)
        self.keypadGridLayout.setContentsMargins(0, 0, 0, 0)
        self.keypadGridLayout.setObjectName("keypadGridLayout")
        self.fasterbutton = QtGui.QPushButton(self.keypadWidget)
        self.fasterbutton.setObjectName("fasterbutton")
        self.keypadGridLayout.addWidget(self.fasterbutton, 2, 2, 1, 1)
        self.jumpforwardbutton = QtGui.QPushButton(self.keypadWidget)
        self.jumpforwardbutton.setObjectName("jumpforwardbutton")
        self.keypadGridLayout.addWidget(self.jumpforwardbutton, 1, 2, 1, 1)
        self.normalbutton = QtGui.QPushButton(self.keypadWidget)
        self.normalbutton.setObjectName("normalbutton")
        self.keypadGridLayout.addWidget(self.normalbutton, 2, 1, 1, 1)
        self.NextButton = QtGui.QPushButton(self.keypadWidget)
        self.NextButton.setObjectName("NextButton")
        self.keypadGridLayout.addWidget(self.NextButton, 0, 2, 1, 1)
        self.jumpbackbutton = QtGui.QPushButton(self.keypadWidget)
        self.jumpbackbutton.setObjectName("jumpbackbutton")
        self.keypadGridLayout.addWidget(self.jumpbackbutton, 1, 0, 1, 1)
        self.playButton = QtGui.QPushButton(self.keypadWidget)
        self.playButton.setObjectName("playButton")
        self.keypadGridLayout.addWidget(self.playButton, 1, 1, 1, 1)
        self.PreviousButton = QtGui.QPushButton(self.keypadWidget)
        self.PreviousButton.setObjectName("PreviousButton")
        self.keypadGridLayout.addWidget(self.PreviousButton, 0, 0, 1, 1)
        self.slowerbutton = QtGui.QPushButton(self.keypadWidget)
        self.slowerbutton.setObjectName("slowerbutton")
        self.keypadGridLayout.addWidget(self.slowerbutton, 2, 0, 1, 1)
        self.gotobutton = QtGui.QPushButton(self.keypadWidget)
        self.gotobutton.setObjectName("gotobutton")
        self.keypadGridLayout.addWidget(self.gotobutton, 0, 1, 1, 1)

        self.retranslateKeypadUi(stepperWindow)
        QtCore.QObject.connect(self.NextButton, QtCore.SIGNAL("clicked()"), stepperWindow.go_to_next_turn)
        QtCore.QObject.connect(self.PreviousButton, QtCore.SIGNAL("clicked()"), stepperWindow.go_to_previous_turn)
        QtCore.QObject.connect(self.gotobutton, QtCore.SIGNAL("clicked()"), stepperWindow.sync_video_and_play)
        QtCore.QObject.connect(self.jumpbackbutton, QtCore.SIGNAL("clicked()"), stepperWindow.jump_back)
        QtCore.QObject.connect(self.jumpforwardbutton, QtCore.SIGNAL("clicked()"), stepperWindow.jump_forward)
        QtCore.QObject.connect(self.slowerbutton, QtCore.SIGNAL("clicked()"), stepperWindow.slower)
        QtCore.QObject.connect(self.normalbutton, QtCore.SIGNAL("clicked()"), stepperWindow.normal_speed)
        QtCore.QObject.connect(self.fasterbutton, QtCore.SIGNAL("clicked()"), stepperWindow.faster)
        QtCore.QObject.connect(self.playButton, QtCore.SIGNAL("clicked()"), stepperWindow.play_or_pause)
        QtCore.QMetaObject.connectSlotsByName(stepperWindow)

    def retranslateKeypadUi(self, stepperWindow):
        stepperWindow.setWindowTitle(QtGui.QApplication.translate("stepperWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.fasterbutton.setText(QtGui.QApplication.translate("stepperWindow", "Faster", None, QtGui.QApplication.UnicodeUTF8))
        self.jumpforwardbutton.setText(QtGui.QApplication.translate("stepperWindow", "Jump+", None, QtGui.QApplication.UnicodeUTF8))
        self.normalbutton.setText(QtGui.QApplication.translate("stepperWindow", "Normal", None, QtGui.QApplication.UnicodeUTF8))
        self.NextButton.setText(QtGui.QApplication.translate("stepperWindow", "Next", None, QtGui.QApplication.UnicodeUTF8))
        self.jumpbackbutton.setText(QtGui.QApplication.translate("stepperWindow", "Jump-", None, QtGui.QApplication.UnicodeUTF8))
        self.playButton.setText(QtGui.QApplication.translate("stepperWindow", "Play", None, QtGui.QApplication.UnicodeUTF8))
        self.PreviousButton.setText(QtGui.QApplication.translate("stepperWindow", "Prev", None, QtGui.QApplication.UnicodeUTF8))
        self.slowerbutton.setText(QtGui.QApplication.translate("stepperWindow", "Slower", None, QtGui.QApplication.UnicodeUTF8))
        self.gotobutton.setText(QtGui.QApplication.translate("stepperWindow", "GoTo", None, QtGui.QApplication.UnicodeUTF8))

    def open_transcript(self):
        filename = QFileDialog.getOpenFileName(self, "Open File")[0]
        self.setWindowTitle(os.path.basename(filename))
        self.transcript = StepperTranscript(filename)
        self.display_current_turn()


    def position_transcript(self, position):
        self.transcript.move_to_position(1.0 * position / 100)
        self.display_current_turn()

    def go_to_next_turn(self):
        self.transcript.go_to_next()
        self.display_current_turn()

    def update_time(self):
        self.turn["time"] = self.time_field.value

    def update_speaker(self):
        self.turn["speaker"] = self.speaker_field.value

    def update_utterance(self):
        self.turn["utterance"] = self.utt_field.value

    def go_to_previous_turn(self):
        self.transcript.go_to_previous()
        self.display_current_turn()

    def display_current_turn(self):
        self.turn = self.transcript.current_turn()
        self.time_field.value = self.turn["time"]
        self.speaker_field.value = self.turn["speaker"]
        self.utt_field.value = self.turn["utterance"]

    def delete_current_turn(self):
        self.transcript.delete_current()
        self.display_current_turn()

    def save_file_as(self):
        filename = QFileDialog.getSaveFileName(self, "File name for save")[0]
        self.save_file_name = filename
        self.transcript.commit_all()
        self.transcript.save_as_csv(filename)

    def save_file(self):
        if self.save_file_name is None:
            self.save_file_as()
        else:
            self.transcript.commit_all()
            self.transcript.save_as_csv(self.save_file_name)

    def revert_current_and_redisplay(self):
        self.transcript.revert_current()
        self.display_current_turn()

    def open_video(self):
        # self.player = Player()
        # self.player.show()
        # self.player.resize(640, 480)
        self.player.OpenFile()

    def play_or_pause(self):
        self.player.PlayPause()

    def slower(self):
        self.player.decrease_rate()

    def faster(self):
        self.player.increase_rate()

    def normal_speed(self):
        self.player.reset_rate()

    def fill_time_code(self):
        self.time_field.value = self.player.getCurrentTimeCode()

    def sync_video_and_play(self):
        self.sync_video()
        if not self.player.mediaplayer.is_playing():
            self.play_or_pause()

    def jump_back(self):
        self.player.jump_video_backward()

    def jump_forward(self):
        self.player.jump_video_forward()

    def sync_video(self):
        self.player.setTimeCode(self.time_field.value)

    def insert_before(self):
        new_uid = self.transcript.insert_new(self.transcript.current_uid)
        self.display_current_turn()

    def insert_after(self):
        new_uid = self.transcript.insert_new(self.transcript.current_uid, "after")
        self.display_current_turn()

    def closeEvent(self, event):
        msgBox = QMessageBox()
        msgBox.setText("Do you want to save before quitting?")
        msgBox.setInformativeText("Do you want to save your changes?")
        msgBox.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Save)
        ret = msgBox.exec_()
        if ret == QMessageBox.Save:
            self.save_file()
            event.accept()
        elif ret == QMessageBox.Discard:
            event.accept()
        else:
            event.ignore()

    def commit(self):
        self.transcript.commit_current()

    def commit_all(self):
        self.transcript.commit_all()

class TranscriptButtons(QWidget):
    def __init__(self, stepper):
        QWidget.__init__(self)
        button_layout = QGridLayout()
        self.setLayout(button_layout)
        button_layout.setColumnStretch(0, 0)
        button_layout.setColumnStretch(1, 0)
        button_layout.setColumnStretch(3, 0)
        button_layout.setRowStretch(0, 0)
        button_layout.setRowStretch(1, 0)
        button_layout.setRowStretch(3, 0)
        button_layout.setRowStretch(4, 0)
        qmy_button(button_layout, stepper.go_to_previous_turn, "pre", the_row=0, the_col=0)
        qmy_button(button_layout, stepper.go_to_next_turn, "next", the_row=0, the_col=1)
        qmy_button(button_layout, stepper.insert_before, "ins before", the_row=1, the_col=0)
        qmy_button(button_layout, stepper.insert_after, "ins after", the_row=1, the_col=1)
        qmy_button(button_layout, stepper.delete_current_turn, "delete turn", the_row=1, the_col=2)
        qmy_button(button_layout, stepper.commit, "commit", the_row=2, the_col=0)
        qmy_button(button_layout, stepper.commit_all, "commit all", the_row=2, the_col=1)
        qmy_button(button_layout, stepper.revert_current_and_redisplay, "revert", the_row=2, the_col=2)
        qmy_button(button_layout, stepper.save_file, "save", the_row=3, the_col=0)
        qmy_button(button_layout, stepper.save_file_as, "save as ...", the_row=3, the_col=1)
        qmy_button(button_layout, stepper.fill_time_code, "fill time", the_row=4, the_col=0)
        qmy_button(button_layout, stepper.sync_video, "sync video", the_row=4, the_col=1)
        button_layout.addWidget(QWidget(), 2, 3)
        button_layout.addWidget(QWidget(), 5, 0)

class VideoButtons(QWidget):
    def __init__(self, stepper):
        QWidget.__init__(self)
        button_layout = QVBoxLayout()
        self.setLayout(button_layout)
        # qmy_button(button_layout, stepper.open_video, "Open Video")
        # qmy_button(button_layout, stepper.play_or_pause, "Play")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    stepper_win = StepperWindow()
    stepper_win.show()
    stepper_win.resize(640, 480)
    # player.OpenFile("/Users/bls910/PycharmProjects/vlcbind/examples/j3.mp4")
    sys.exit(app.exec_())

