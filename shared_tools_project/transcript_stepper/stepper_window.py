__author__ = 'bls910'
from PySide.QtGui import QDialog, QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout, QWidget, QFont, QMainWindow, QApplication, QShortcut, QKeySequence, QSlider
from PySide import QtCore
from PySide.QtCore import Qt
from standard_package.mywidgets import qHotField, qmy_button, create_menu
from transcript_for_stepper import StepperTranscript
from vlcplayerproject.pyside_vlc_player import Player
import re, sys, os

def separate_turns(raw_text):
    return re.findall(r"(\w+?)\t(.*?)[\t\n\r]", raw_text)

class StepperWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        filename = QFileDialog.getOpenFileName(self, "Open File")[0]
        self.setWindowTitle(os.path.basename(filename))
        self.transcript = StepperTranscript(filename)
        # file = open(filename, 'r')
        # rawtext = file.read()
        # file.close()
        # self.turns = separate_turns(rawtext)
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

        self.turn = self.transcript.current_turn()
        self.time_field = qHotField("time", str, self.turn["time"], min_size=75, max_size=75, pos="top", handler=self.update_time)
        self.display_layout.addWidget(self.time_field)
        self.speaker_field = qHotField("speaker", str, self.turn["speaker"], min_size=75, max_size=75, pos="top", handler=self.update_speaker)
        self.display_layout.addWidget(self.speaker_field)
        self.utt_field = qHotField("utterance", str, self.turn["utterance"], min_size=350, pos="top", handler=self.update_utterance, multiline=True)
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

        self.player = Player()
        outer_layout.addWidget(self.player)

        outer_layout.setStretch(0, 0)
        outer_layout.setStretch(1, 1)
        self.save_file_name = None

        command_list = [
            [self.open_video, "Open Video", {}, "Ctrl+o"],
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

    def fill_time_code(self):
        self.time_field.value = self.player.getCurrentTimeCode()

    def sync_video_and_play(self):
        self.sync_video()
        if not self.player.mediaplayer.is_playing():
            self.play_or_pause()

    def sync_video(self):
        self.player.setTimeCode(self.time_field.value)

    def insert_before(self):
        new_uid = self.transcript.insert_new(self.transcript.current_uid)
        self.display_current_turn()

    def insert_after(self):
        new_uid = self.transcript.insert_new(self.transcript.current_uid, "after")
        self.display_current_turn()

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
        qmy_button(button_layout, stepper.transcript.commit_current, "commit", the_row=2, the_col=0)
        qmy_button(button_layout, stepper.transcript.commit_all, "commit all", the_row=2, the_col=1)
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

