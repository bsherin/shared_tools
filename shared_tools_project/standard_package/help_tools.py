# Some tools for handling help.
#
# The main class is helpForWindow. It is designed to be associated with a single window.
# It can create help buttons (class helpButton), which look like little question marks and display text in a message box when clicked.
# It maintains a list of these buttons, and can show and hide them all.
# A helpToggler button can be used to show and hide the buttons associated with a helpForWindow
#
###

from PySide.QtGui import QPushButton, QSizePolicy, QMessageBox, QFont # @UnresolvedImport

class helpForWindow(object):
    def __init__(self):
        self._button_list = []
        self._shown = True
        
    def create_button(self, title_text, informative_text = None):
        hb = helpButton(self, title_text, informative_text)
        self._button_list.append(hb)
        return(hb)
    
    def remove_button(self, the_button):
        self._button_list.remove(the_button)
    
    def show_all_help_buttons(self):
        self._shown = True
        for hb in self._button_list:
            hb.show()
            
    def hide_all_help_buttons(self):
        self._shown = False
        for hb in self._button_list:
            hb.hide()
        
class helpButton(QPushButton):
    # help_text: This is a bold title-ish things that appears at first in the message box
    # informative text: This is unbold text that appears below.
    def __init__(self, help_instance, help_text, informative_text = None):
        QPushButton.__init__(self, "?")
        self.setFont(QFont('SansSerif', 12))
        self.setFlat(True)
        self.setFixedWidth(15)
        self.setFixedHeight(20)
        self.help_text = help_text
        self.informative_text = informative_text
        self.help_instance = help_instance
        self.clicked.connect(self.show_message)
        self.destroyed.connect(lambda: help_instance.remove_button(self)) # This uses a trick to send an extra parameter.
        
    def show_message(self):
        msgBox = QMessageBox()
        msgBox.setText(self.help_text + "                                     ") # The spaces keep the window from being too narrow.
        msgBox.setInformativeText(self.informative_text)
        msgBox.adjustSize()

        msgBox.exec_()
    
        
class helpToggler(QPushButton):
    def __init__(self, help_instance):
        QPushButton.__init__(self, "Toggle Help")
        self.setContentsMargins(1, 1, 1, 1)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setFont(QFont('SansSerif', 12))
        self.setAutoDefault(False)
        self.setDefault(False)
        self.help_instance = help_instance
        self.clicked.connect(self.toggle_help)
    
    def toggle_help(self):
        if self.help_instance._shown:
            self.help_instance.hide_all_help_buttons()
            self.help_instance._shown = False
        else:
            self.help_instance.show_all_help_buttons()
            self.help_instance._shown = True
            