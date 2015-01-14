from PySide.QtGui import QTextCursor, QFileDialog, QHBoxLayout, QWidget, QMainWindow, QApplication, QShortcut, QKeySequence, QSlider, QMessageBox, QSplitter, QFrame
from PySide import QtCore, QtGui
from PySide.QtCore import Qt
import sys

from stepper_directories import SHARED_TOOLS_DIR, CURRENT_PROJECT_DIR

if __name__ == "__main__":
    sys.path = sys.path + [SHARED_TOOLS_DIR] + [CURRENT_PROJECT_DIR]

from standard_package.mywidgets import qHotField, qmy_button, create_menu
from transcript_for_stepper import StepperTranscript
from vlcplayerproject.pyside_vlc_player import Player
from standard_package.qanalysis_window_basics import ExplorerTable
import re, sys, os

class StepperWindow(QMainWindow):

    def __init__(self):
        QMainWindow.__init__(self)
        filename = QFileDialog.getOpenFileName(self, "Open File")[0]
        self.setWindowTitle(os.path.basename(filename))
        self.transcript = StepperTranscript(filename)

        self.setupUi(self)


        self.save_file_name = None
        self.display_current_turn()
        # file = open(filename, 'r')

    def position_transcript(self, position):
        self.transcript.move_to_position(1.0 * position / 100)
        self.display_current_turn()

    def show_transcript_in_explorer(self):
        transcript_array = self.transcript.get_transcript_as_array()
        self.click_handler = ExploreClickHandler(self)
        self.explorer_table = ExplorerTable(transcript_array, click_handler=self.click_handler)
        self.big_splitter.addWidget(self.explorer_table)
        # self.outer_layout.setStretch(2, 1)
        self.explorer_table.highlight_row(self.transcript.current_index())

    def go_to_next_turn(self):
        self.transcript.go_to_next()
        self.display_current_turn()

    def update_time(self):
        self.turn["time"] = self.time_field.value
        if self.explorer_table is not None:
            table_item = self.explorer_table.item(self.transcript.current_index(), 1)
            table_item.setText(self.time_field.value)

    def update_speaker(self):
        self.turn["speaker"] = self.speaker_field.value
        if self.explorer_table is not None:
            table_item = self.explorer_table.item(self.transcript.current_index(), 2)
            table_item.setText(self.speaker_field.value)

    def update_utterance(self):
        self.turn["utterance"] = self.utt_field.value
        if self.explorer_table is not None:
            table_item = self.explorer_table.item(self.transcript.current_index(), 3)
            table_item.setText(self.utt_field.value)

    def go_to_previous_turn(self):
        self.transcript.go_to_previous()
        self.display_current_turn()

    def go_to_row(self, the_row):
        self.transcript.go_to_index(the_row)
        self.display_current_turn()

    def display_current_turn(self):
        self.turn = self.transcript.current_turn()
        self.time_field.value = self.turn["time"]
        self.speaker_field.value = self.turn["speaker"]
        self.utt_field.value = self.turn["utterance"]
        if self.explorer_table is not None:
            self.explorer_table.highlight_row(self.transcript.current_index())
        self.utt_field.efield.setFocus()
        self.utt_field.efield.moveCursor(QTextCursor.Start, mode=QTextCursor.MoveAnchor)

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

    def open_video(self, filename=None):
        # self.player = Player()
        # self.player.show()
        # self.player.resize(640, 480)
        self.player.OpenFile(filename)

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
        if self.explorer_table is not None:
            self.explorer_table.insert_row(self.transcript.current_index(), [new_uid, "", "", ""])
        self.display_current_turn()

    def insert_after(self):
        new_uid = self.transcript.insert_new(self.transcript.current_uid, "after")
        if self.explorer_table is not None:
            self.explorer_table.insert_row(self.transcript.current_index(), [new_uid, "", "", ""])
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

    def go_to_next_word(self):
        c = self.utt_field.efield.textCursor()
        if c.selectedText() != "": # If nothing is selected, select the current word
            self.utt_field.efield.moveCursor(QTextCursor.NextWord, QTextCursor.MoveAnchor)
        self.utt_field.efield.moveCursor(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
        c = self.utt_field.efield.textCursor()
        if c.selectedText() == "": # this addresses the case where I'm in front of a blank space
            self.utt_field.efield.moveCursor(QTextCursor.NextWord, QTextCursor.MoveAnchor)
            self.utt_field.efield.moveCursor(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)

    def go_to_previous_word(self):
        c = self.utt_field.efield.textCursor()
        pos = c.position()
        self.utt_field.efield.moveCursor(QTextCursor.StartOfWord, QTextCursor.MoveAnchor)
        self.utt_field.efield.moveCursor(QTextCursor.PreviousWord, QTextCursor.MoveAnchor)
        self.utt_field.efield.moveCursor(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)
        c = self.utt_field.efield.textCursor()
        if c.position() == pos:
            self.utt_field.efield.moveCursor(QTextCursor.StartOfWord, QTextCursor.MoveAnchor)
            self.utt_field.efield.moveCursor(QTextCursor.PreviousWord, QTextCursor.MoveAnchor)
            self.utt_field.efield.moveCursor(QTextCursor.PreviousWord, QTextCursor.MoveAnchor)
            self.utt_field.efield.moveCursor(QTextCursor.EndOfWord, QTextCursor.KeepAnchor)

    def setupUi(self, stepperWindow):
        stepperWindow.setObjectName("stepperWindow")
        self.outer_widget = QtGui.QWidget(stepperWindow)
        # sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        # sizePolicy.setHorizontalStretch(0)
        # sizePolicy.setVerticalStretch(0)
        # sizePolicy.setHeightForWidth(self.outer_widget.sizePolicy().hasHeightForWidth())
        # self.outer_widget.setSizePolicy(sizePolicy)
        self.outer_widget.setObjectName("outer_widget")
        self.outer_layout = QtGui.QHBoxLayout(self.outer_widget)
        self.outer_layout.setContentsMargins(0, 0, 0, 0)
        self.outer_layout.setObjectName("outer_layout")
        self.big_splitter = QSplitter()
        self.outer_layout.addWidget(self.big_splitter)
        self.left_layout = QtGui.QVBoxLayout()
        self.left_layout.setObjectName("left_layout")
        self.left_widget = QWidget()
        self.left_widget.setLayout(self.left_layout)
        self.big_splitter.addWidget(self.left_widget)

        self.player = Player()
        self.left_layout.addWidget(self.player)
        self.left_layout.setStretch(0, 1)

        self.createDisplayFields()

        # Add all of the buttons
        self.allbuttonslayout = QtGui.QHBoxLayout()
        self.allbuttonslayout.setSizeConstraint(QtGui.QLayout.SetNoConstraint)
        self.allbuttonslayout.setObjectName("allbuttonslayout")
        self.gridbuttonlayout = QtGui.QGridLayout()
        self.gridbuttonlayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.gridbuttonlayout.setVerticalSpacing(1)
        self.gridbuttonlayout.setObjectName("gridbuttonlayout")
        self.DeleteButton = QtGui.QPushButton(self.outer_widget)
        self.DeleteButton.setObjectName("DeleteButton")
        self.gridbuttonlayout.addWidget(self.DeleteButton, 0, 2, 1, 1)
        self.InsertAfterButton = QtGui.QPushButton(self.outer_widget)
        self.InsertAfterButton.setObjectName("InsertAfterButton")
        self.gridbuttonlayout.addWidget(self.InsertAfterButton, 0, 1, 1, 1)
        self.SaveAsButton = QtGui.QPushButton(self.outer_widget)
        self.SaveAsButton.setObjectName("SaveAsButton")
        self.gridbuttonlayout.addWidget(self.SaveAsButton, 1, 1, 1, 1)
        self.CommitAllButton = QtGui.QPushButton(self.outer_widget)
        self.CommitAllButton.setObjectName("CommitAllButton")
        self.gridbuttonlayout.addWidget(self.CommitAllButton, 2, 1, 1, 1)
        self.CommitButton = QtGui.QPushButton(self.outer_widget)
        self.CommitButton.setObjectName("CommitButton")
        self.gridbuttonlayout.addWidget(self.CommitButton, 2, 0, 1, 1)
        self.InsertBeforeButton = QtGui.QPushButton(self.outer_widget)
        self.InsertBeforeButton.setObjectName("InsertBeforeButton")
        self.gridbuttonlayout.addWidget(self.InsertBeforeButton, 0, 0, 1, 1)
        self.SaveButton = QtGui.QPushButton(self.outer_widget)
        self.SaveButton.setObjectName("SaveButton")
        self.gridbuttonlayout.addWidget(self.SaveButton, 1, 0, 1, 1)
        self.RevertButton = QtGui.QPushButton(self.outer_widget)
        self.RevertButton.setObjectName("RevertButton")
        self.gridbuttonlayout.addWidget(self.RevertButton, 2, 2, 1, 1)
        self.allbuttonslayout.addLayout(self.gridbuttonlayout)
        self.keypadGridLayout = QtGui.QGridLayout()
        self.keypadGridLayout.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.keypadGridLayout.setObjectName("keypadGridLayout")
        self.SlowerButton = QtGui.QPushButton(self.outer_widget)
        self.SlowerButton.setObjectName("SlowerButton")
        self.keypadGridLayout.addWidget(self.SlowerButton, 2, 0, 1, 1)
        self.FasterButton = QtGui.QPushButton(self.outer_widget)
        self.FasterButton.setObjectName("FasterButton")
        self.keypadGridLayout.addWidget(self.FasterButton, 2, 2, 1, 1)
        self.NormalButton = QtGui.QPushButton(self.outer_widget)
        self.NormalButton.setObjectName("NormalButton")
        self.keypadGridLayout.addWidget(self.NormalButton, 2, 1, 1, 1)
        self.JumpBackButton = QtGui.QPushButton(self.outer_widget)
        self.JumpBackButton.setObjectName("JumpBackButton")
        self.keypadGridLayout.addWidget(self.JumpBackButton, 1, 0, 1, 1)
        self.NextButton = QtGui.QPushButton(self.outer_widget)
        self.NextButton.setObjectName("NextButton")
        self.keypadGridLayout.addWidget(self.NextButton, 0, 2, 1, 1)
        self.JumpForward = QtGui.QPushButton(self.outer_widget)
        self.JumpForward.setObjectName("JumpForward")
        self.keypadGridLayout.addWidget(self.JumpForward, 1, 2, 1, 1)
        self.PlayButton = QtGui.QPushButton(self.outer_widget)
        self.PlayButton.setObjectName("PlayButton")
        self.keypadGridLayout.addWidget(self.PlayButton, 1, 1, 1, 1)
        self.PreviousButton = QtGui.QPushButton(self.outer_widget)
        self.PreviousButton.setObjectName("PreviousButton")
        self.keypadGridLayout.addWidget(self.PreviousButton, 0, 0, 1, 1)
        self.GotoButton = QtGui.QPushButton(self.outer_widget)
        self.GotoButton.setObjectName("GotoButton")
        self.keypadGridLayout.addWidget(self.GotoButton, 0, 1, 1, 1)
        self.SyncButton = QtGui.QPushButton(self.outer_widget)
        self.SyncButton.setObjectName("SyncButton")
        self.keypadGridLayout.addWidget(self.SyncButton, 3, 2, 1, 1)
        self.FillButton = QtGui.QPushButton(self.outer_widget)
        self.FillButton.setObjectName("FillButton")
        self.keypadGridLayout.addWidget(self.FillButton, 3, 0, 1, 1)
        self.allbuttonslayout.addLayout(self.keypadGridLayout)

        self.ExplorerButton = QtGui.QPushButton(self.outer_widget)
        self.ExplorerButton.setObjectName("ExplorerButton")
        self.gridbuttonlayout.addWidget(self.ExplorerButton, 1, 2, 1, 1)

        # Change made by hand here

        self.left_layout.addLayout(self.allbuttonslayout)
        self.left_layout.setStretch(1, 0)
        self.left_layout.setStretch(2, 0)

        # self.splitter = QSplitter()
        # self.splitter.addWidget(self.player)
        # self.outer_layout.addWidget(self.splitter)
        # self.outer_layout.setStretch(1, 1)

        stepperWindow.show_transcript_in_explorer()
        if stepperWindow.transcript.video_file_name != None:
            self.open_video(stepperWindow.transcript.video_file_name)
        stepperWindow.setCentralWidget(self.outer_widget)

        self.menubar = QtGui.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1500, 22))
        self.menubar.setObjectName("menubar")
        stepperWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(stepperWindow)
        self.statusbar.setObjectName("statusbar")
        stepperWindow.setStatusBar(self.statusbar)

        self.retranslateUi(stepperWindow)
        QtCore.QObject.connect(self.GotoButton, QtCore.SIGNAL("clicked()"), stepperWindow.sync_video_and_play)
        QtCore.QObject.connect(self.JumpForward, QtCore.SIGNAL("clicked()"), stepperWindow.jump_forward)
        QtCore.QObject.connect(self.PlayButton, QtCore.SIGNAL("clicked()"), stepperWindow.play_or_pause)
        QtCore.QObject.connect(self.SyncButton, QtCore.SIGNAL("clicked()"), stepperWindow.sync_video)
        QtCore.QObject.connect(self.FillButton, QtCore.SIGNAL("clicked()"), stepperWindow.fill_time_code)
        QtCore.QObject.connect(self.NextButton, QtCore.SIGNAL("clicked()"), stepperWindow.go_to_next_turn)
        QtCore.QObject.connect(self.CommitButton, QtCore.SIGNAL("clicked()"), stepperWindow.commit)
        QtCore.QObject.connect(self.InsertBeforeButton, QtCore.SIGNAL("clicked()"), stepperWindow.insert_before)
        QtCore.QObject.connect(self.JumpBackButton, QtCore.SIGNAL("clicked()"), stepperWindow.jump_back)
        QtCore.QObject.connect(self.SlowerButton, QtCore.SIGNAL("clicked()"), stepperWindow.slower)
        QtCore.QObject.connect(self.FasterButton, QtCore.SIGNAL("clicked()"), stepperWindow.faster)
        QtCore.QObject.connect(self.NormalButton, QtCore.SIGNAL("clicked()"), stepperWindow.normal_speed)
        QtCore.QObject.connect(self.PreviousButton, QtCore.SIGNAL("clicked()"), stepperWindow.go_to_previous_turn)
        QtCore.QObject.connect(self.SaveButton, QtCore.SIGNAL("clicked()"), stepperWindow.save_file)
        QtCore.QObject.connect(self.SaveAsButton, QtCore.SIGNAL("clicked()"), stepperWindow.save_file_as)
        QtCore.QObject.connect(self.RevertButton, QtCore.SIGNAL("clicked()"), stepperWindow.revert_current_and_redisplay)
        QtCore.QObject.connect(self.DeleteButton, QtCore.SIGNAL("clicked()"), stepperWindow.delete_current_turn)
        QtCore.QObject.connect(self.InsertAfterButton, QtCore.SIGNAL("clicked()"), stepperWindow.insert_after)
        QtCore.QObject.connect(self.CommitAllButton, QtCore.SIGNAL("clicked()"), stepperWindow.commit_all)

        # Added this line by hand
        QtCore.QObject.connect(self.ExplorerButton, QtCore.SIGNAL("clicked()"), stepperWindow.show_transcript_in_explorer)

        QtCore.QMetaObject.connectSlotsByName(stepperWindow)

        # The following menu and shortcut stuff added by hand
        command_list = [
            [self.open_video, "Open Video", {}, "Ctrl+v"],
            [self.play_or_pause, "Play/Pause", {}, Qt.CTRL + Qt.Key_K],
            [self.save_file, "Save", {}, "Ctrl+s"],
            [self.player.jump_video_backward, "Jump Back", {}, Qt.CTRL + Qt.Key_J],
            [self.player.jump_video_forward, "Jump Forward", {}, Qt.CTRL + Qt.Key_L],
            [self.go_to_previous_turn, "Previous Turn", {}, "Ctrl+u"],
            [self.go_to_next_turn, "Next Turn", {}, "Ctrl+o"],
            [self.go_to_previous_word, "Previous Word", {}, "Ctrl+n"],
            [self.go_to_next_word, "Next Word", {}, "Ctrl+m"]
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
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_I), self, self.sync_video_and_play)
        QShortcut(QKeySequence(Qt.CTRL + Qt.Key_8), self, self.sync_video_and_play)

    def retranslateUi(self, stepperWindow):
        stepperWindow.setWindowTitle(QtGui.QApplication.translate("stepperWindow", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.DeleteButton.setText(QtGui.QApplication.translate("stepperWindow", "Delete", None, QtGui.QApplication.UnicodeUTF8))
        self.InsertAfterButton.setText(QtGui.QApplication.translate("stepperWindow", "Ins After", None, QtGui.QApplication.UnicodeUTF8))
        self.SaveAsButton.setText(QtGui.QApplication.translate("stepperWindow", "Save As ...", None, QtGui.QApplication.UnicodeUTF8))
        self.CommitAllButton.setText(QtGui.QApplication.translate("stepperWindow", "Commit all", None, QtGui.QApplication.UnicodeUTF8))
        self.CommitButton.setText(QtGui.QApplication.translate("stepperWindow", "Commit", None, QtGui.QApplication.UnicodeUTF8))
        self.InsertBeforeButton.setText(QtGui.QApplication.translate("stepperWindow", "Ins Before", None, QtGui.QApplication.UnicodeUTF8))
        self.SaveButton.setText(QtGui.QApplication.translate("stepperWindow", "Save", None, QtGui.QApplication.UnicodeUTF8))
        self.RevertButton.setText(QtGui.QApplication.translate("stepperWindow", "Revert", None, QtGui.QApplication.UnicodeUTF8))
        self.SlowerButton.setText(QtGui.QApplication.translate("stepperWindow", "Slower", None, QtGui.QApplication.UnicodeUTF8))
        self.FasterButton.setText(QtGui.QApplication.translate("stepperWindow", "Faster", None, QtGui.QApplication.UnicodeUTF8))
        self.NormalButton.setText(QtGui.QApplication.translate("stepperWindow", "Normal", None, QtGui.QApplication.UnicodeUTF8))
        self.JumpBackButton.setText(QtGui.QApplication.translate("stepperWindow", "Jump-", None, QtGui.QApplication.UnicodeUTF8))
        self.NextButton.setText(QtGui.QApplication.translate("stepperWindow", "Next", None, QtGui.QApplication.UnicodeUTF8))
        self.JumpForward.setText(QtGui.QApplication.translate("stepperWindow", "Jump+", None, QtGui.QApplication.UnicodeUTF8))
        self.PlayButton.setText(QtGui.QApplication.translate("stepperWindow", "Play", None, QtGui.QApplication.UnicodeUTF8))
        self.PreviousButton.setText(QtGui.QApplication.translate("stepperWindow", "Prev", None, QtGui.QApplication.UnicodeUTF8))
        self.GotoButton.setText(QtGui.QApplication.translate("stepperWindow", "GoTo", None, QtGui.QApplication.UnicodeUTF8))
        self.SyncButton.setText(QtGui.QApplication.translate("stepperWindow", "Sync Vid", None, QtGui.QApplication.UnicodeUTF8))
        self.FillButton.setText(QtGui.QApplication.translate("stepperWindow", "Fill Time", None, QtGui.QApplication.UnicodeUTF8))

        self.ExplorerButton.setText(QtGui.QApplication.translate("stepperWindow", "Explorer", None, QtGui.QApplication.UnicodeUTF8))

    def createDisplayFields(self):
        display_widget = QFrame()
        display_widget.setFrameStyle(QtGui.QFrame.Panel | QtGui.QFrame.Sunken)
        self.left_layout.addWidget(display_widget)
        self.display_layout = QHBoxLayout()

        self.turn = self.transcript.current_turn()
        self.time_field = qHotField("time", str, self.turn["time"], min_size=75, max_size=75, pos="top", handler=self.update_time)
        self.display_layout.addWidget(self.time_field)
        self.speaker_field = qHotField("speaker", str, self.turn["speaker"], min_size=75, max_size=75, pos="top", handler=self.update_speaker)
        self.display_layout.addWidget(self.speaker_field)
        self.utt_field = qHotField("utterance", str, self.turn["utterance"], min_size=350, max_size=500, pos="top", handler=self.update_utterance, multiline=True)
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
        self.left_layout.addWidget(self.transcript_slider)

class ExploreClickHandler():
    def __init__(self, stepper):
        self._stepper = stepper

    def handle_click(self, item):
        self._stepper.go_to_row(item.row())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    stepper_win = StepperWindow()
    stepper_win.show()
    stepper_win.resize(1250, 1000)
    # player.OpenFile("/Users/bls910/PycharmProjects/vlcbind/examples/j3.mp4")
    sys.exit(app.exec_())