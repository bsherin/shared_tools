from PySide.QtGui import QPushButton, QSizePolicy, QGroupBox, QFont, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout , QScrollArea, QFileDialog
from PySide.QtGui import QLineEdit, QLabel, QCheckBox, QRadioButton, QComboBox, QFrame, QTabWidget, QMessageBox, QAction, QKeySequence
from PySide import QtCore # @UnresolvedImport
from PySide import QtGui # @UnresolvedImport
from PySide.QtCore import Qt  # @UnresolvedImport
from montecarlo_package.monte_carlo import MonteSequence
import re, os
from xml.etree import ElementTree
from collections import OrderedDict

regular_font = QFont('SansSerif', 12)
regular_small_font = QFont('SansSerif', 10)

def show_message(text):
    msgBox = QMessageBox()
    msgBox.setText(text)
    msgBox.exec_()
    
def create_menu(mwindow, mbar, menu_name, command_list):
    new_menu =mbar.addMenu("&" + menu_name)
    for command in command_list:
        if len(command) == 4:
            new_action = QAction("&" + command[1], mwindow, shortcut = QKeySequence(command[3]))
        else:
            new_action = QAction("&" + command[1], mwindow)
        new_action.triggered.connect(command[0])
        new_menu.addAction(new_action)

def remove_trailing_slash(the_string):
    if the_string[-1] == "/":
        return the_string[0:-1]
    else:
        return the_string

def add_slash(the_string):
    if the_string[-1] != "/":
        return the_string + "/"
    else:
        return the_string

class QScroller(QVBoxLayout):
    
    def __init__(self, qpframe):
        QVBoxLayout.__init__(self)
        scroll = QScrollArea()
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidgetResizable(True)
        subWidget = QWidget()
        subWidget.setLayout(qpframe)
        scroll.setWidget(subWidget)
        self.addWidget(scroll)
        self.scroll = scroll
    
######
# qHotField does a lot of the magic work
#
# This creates a widget which is supposed to act just as if it contains a variable, in a naive realist sort of way.
# The only catch is that it is set and accessed using var_name.value
# Otherwise, once its set up, it should act just like a python variable.
# 
# Every time that any sort of value is passed, it can be specified as its native type, and will be returned in its native type.
# qHotField handles all of the inter-conversions to strings.
#
# It has special code for handling cases when there might be list of values. 
# It also can deal with a case in which the user specifies a fixed list to choose from. (It then displays as a popup list.)
# If it's a popup list, however, and we want to change the list, then we need a special call to repopulate the list.

class qHotField(QWidget):
    def __init__(self, name, mytype, initial_value, value_list = None, pos = "left", help_text = None, help_instance = None, min_size = 0, max_size = None, handler = None):
        QWidget.__init__(self)
        if max_size == None:
            max_size = 300
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed) # Let it expand horizontally but not vertically
        self.name = name
        self.mytype = mytype
        self.setContentsMargins(1, 1, 1, 1)
        self.is_popup = (value_list != None)
        if self.is_popup:
            self.value_list = [str(v) for v in value_list] # It's possible the values won't be strings.
        if pos == "top":
            self.layout1 = QVBoxLayout()
        else:
            self.layout1=QHBoxLayout()
        self.layout1.setContentsMargins(1, 1, 1, 1)
        self.layout1.setSpacing(1)
        self.setLayout(self.layout1)
        if mytype == bool:
            self.cb = QCheckBox(name)
            self.cb.setFont(regular_small_font)
            self.layout1.addWidget(self.cb)
            self.cb.setChecked(initial_value)
            if handler != None:
                self.cb.toggled.connect(handler)
        else:
            if not self.is_popup:
                self.efield = QLineEdit("Default Text")
                self.efield.setText(str(initial_value))
                if handler != None:
                    self.efield.textChanged.connect(handler)
            else:
                self.efield = QComboBox()
                self.efield.addItems(value_list)
                if len(value_list) != 0:
                    self.efield.setCurrentIndex(value_list.index(initial_value))
                self.efield.setSizeAdjustPolicy(QComboBox.AdjustToContents)
                if handler != None:
                    self.efield.currentIndexChanged.connect(handler)
                self.layout1.setContentsMargins(5, 5, 5, 5) # Popups need a little more space
                self.layout1.setSpacing(2)
            self.efield.setFont(regular_small_font)
            self.label = QLabel(name)
            self.label.setFont(regular_small_font)
            if pos == "right":
                self.layout1.addWidget(self.efield)
                self.layout1.addWidget(self.label)
            else:
                self.layout1.addWidget(self.label)
                self.layout1.addWidget(self.efield)
            
            self.efield.setMaximumWidth(max_size)
            if min_size != 0:
                self.efield.setMinimumWidth(min_size)
        self.layout1.addStretch()
        if help_text != None:
            if (help_instance == None):
                print "No help instance specified."
            else:
                help_button_widget = help_instance.create_button(name, help_text)
                self.layout1.addWidget(help_button_widget)
                    
    def repopulate_list(self, initial_value, value_list):
        if not self.is_popup:
            print "This qHotField is not a popup list. So it can't be repopulated"
            return
        self.value_list = [str(v) for v in value_list] # It's possible the values won't be strings
        self.efield.clear()
        self.efield.addItems(value_list)
        self.efield.setCurrentIndex(value_list.index(initial_value))
        return
        
    def get_myvalue(self):
        if self.mytype == bool:
            return self.cb.isChecked()
        else:
            if self.is_popup:
                the_txt = self.efield.currentText()
            else:
                the_txt = self.efield.text()
            if (self.mytype == str) or (self.mytype == unicode):
                return (self.mytype)(the_txt)
            else: # if we have a numerical type, the user might have entered a list separated by spaces. Handle that specially
                the_val = re.findall(r"\S+", the_txt) # We might have a list of values separated by spaces if this is a numerical variable
                if len(the_val) == 1:  # it's just a single value
                    result = (self.mytype)(the_txt)
                else: # it's a list. We want to convert treat this as a monte sequence
                    res = []
                    for v in the_val:
                        res.append((self.mytype)(v))
                    result = MonteSequence(res)
                return result
        
    def set_myvalue(self, val):
        if self.mytype == bool:
            self.cb.setChecked(val)
        elif self.is_popup:
            self.efield.setCurrentIndex(self.value_list.index(val))
        else:
            if type(val) == list:
                result = ""
                for x in val:
                    result = result + str(x) + " "
                self.efield.setText(result)
            else:
                self.efield.setText(str(val))
    value = property(get_myvalue, set_myvalue)

#
# This is designed to serve as one of the parameter selection widgets
#
class FolderSelector(QWidget):
    def __init__(self, var_name, default_folder, project_root_dir = "", help_instance=None, handler=None):
        QWidget.__init__(self)
        self.project_root_dir = project_root_dir
        self.my_layout = QHBoxLayout()
        self.setLayout(self.my_layout)
        self.var_name = var_name
        self.current_value = default_folder
        self.full_path = project_root_dir + default_folder
        self.project_root_dir = project_root_dir

        self.handler=handler
        self.my_but = QPushButton(os.path.basename(remove_trailing_slash(default_folder)))
        self.my_but.setFont(regular_small_font)
        self.my_but.setStyleSheet("text-align: left")
        self.my_but.clicked.connect(self.set_folder)
        self.my_layout.addWidget(self.my_but)

        my_label = QLabel(var_name)
        my_label.setFont(regular_small_font)
        self.my_layout.addWidget(my_label)

    def set_folder(self):
        directions = "Select a folder for " + self.var_name
        new_value = QFileDialog.getExistingDirectory(self, directions, dir=os.path.dirname(self.full_path), options=QFileDialog.ShowDirsOnly)
        new_value = re.sub(self.project_root_dir, "", new_value)
        self.set_myvalue(new_value)
        if self.handler is not None:
            self.handler()

    def get_myvalue(self):
        return self.current_value

    def set_myvalue(self, new_value):
        if new_value != "":
            self.current_value = new_value
            self.full_path = add_slash(self.project_root_dir + new_value)
            self.my_but.setText(os.path.basename(remove_trailing_slash(self.current_value)))

    value = property(get_myvalue, set_myvalue)
#
# This is designed to serve as a parameter selection widget.
#

class FileSelector(QWidget):
    def __init__(self, var_name, default_file, project_root_dir = None, help_instance=None):
        QWidget.__init__(self)
        self.project_root_dir = project_root_dir
        self.my_layout = QHBoxLayout()
        self.setLayout(self.my_layout)
        self.var_name = var_name
        self.current_value = default_file
        self.full_path = project_root_dir + default_file
        self.my_layout.setContentsMargins(1, 1, 1, 1)
        self.my_layout.setSpacing(3)

        self.my_but = QPushButton(os.path.basename(remove_trailing_slash(default_file)))
        self.my_but.setFont(regular_small_font)
        self.my_but.setStyleSheet("text-align: left")
        self.my_but.clicked.connect(self.set_file)
        self.my_layout.addWidget(self.my_but)

        my_label = QLabel(var_name)
        my_label.setFont(regular_small_font)
        self.my_layout.addWidget(my_label)

    def set_file(self):
        directions = "Select a file for " + self.var_name
        new_value = QFileDialog.getOpenFileName(self, directions, dir=os.path.dirname(self.full_path))[0]
        new_value = re.sub(self.project_root_dir, "", new_value)
        self.set_myvalue(new_value)

    def get_myvalue(self):
        return self.current_value

    def set_myvalue(self, new_value):
        if new_value != "":
            self.current_value = new_value
            self.my_but.setText(os.path.basename(remove_trailing_slash(self.current_value)))

    value = property(get_myvalue, set_myvalue)


class XMLFileSelector(QGroupBox):
    def __init__(self, var_name, default_folder, project_root_dir = "", help_instance=None):
        QGroupBox.__init__(self, "data selector")
        self.project_root_dir = project_root_dir
        self.setContentsMargins(1, 1, 1, 1)
        self.my_layout = QVBoxLayout()
        self.my_layout.setSpacing(1)
        self.setLayout(self.my_layout)
        self.var_name = var_name
        self.current_folder = default_folder
        self.my_folder_selector = FolderSelector(var_name, default_folder, project_root_dir, handler = self.new_folder_selected)
        self.my_layout.addWidget(self.my_folder_selector)
        self.concatenate = qHotField("concatenate", bool, False)
        self.my_layout.addWidget(self.concatenate)
        self.read_schema()
        self.check_group = CheckGroupNoParameters("body blocks", self.block_list, self.block_list[0])
        self.my_layout.addWidget(self.check_group)

    def read_schema(self):
        the_etree = None
        full_path = add_slash(self.project_root_dir + self.current_folder)
        f = open(full_path + "schema.xml")
        raw_text = f.read()
        f.close()
        raw_text = re.sub(r"\[.*?\]", r"", raw_text)
        the_etree = ElementTree.XML(raw_text)
        if the_etree is None:
            return
        else:
            bl = [subtree.tag for subtree in list(the_etree.find("{transcript}BODY"))]
            self.block_list = []
            for block_name in bl:
                self.block_list.append(re.search("\{transcript\}(.*)", block_name).group(1))

    def new_folder_selected(self):
        self.current_folder = self.my_folder_selector.value
        self.read_schema()
        self.check_group.recreate_check_boxes(self.block_list)

    def get_myvalue(self):
        return (self.my_folder_selector.value, self.check_group.value, self.concatenate.value)

    def set_myvalue(self, new_value):
        if new_value != "":
            self.my_folder_selector.value = add_slash(new_value[0])
            self.new_folder_selected()
            self.check_group.value = new_value[1]
            self.concatenate.value = new_value[2]

    value = property(get_myvalue, set_myvalue)

class RadioGroup(QGroupBox):
    def __init__(self, group_name, name_list, handler = None, help_instance = None):
        QGroupBox.__init__(self, group_name)
        the_layout = QGridLayout()
        self.setLayout(the_layout)
        self.widget_dict = {}
        rows = 0
        for txt in name_list:
            cb = QRadioButton(txt)
            the_layout.addWidget(cb, rows, 0)
            if handler != None:
                cb.toggled.connect(handler)
            self.widget_dict[txt] = cb
            rows += 1
        return
    
    @property
    def value(self):
        for (key, w) in self.widget_dict.items():
            if w.isChecked():
                return key
        return None
    
    def click_item(self, name):
        self.widget_dict[name].click()

class StructuredRadioGroup(QGroupBox):
    def __init__(self, group_name, name_dict, handler = None, help_instance = None):
        QGroupBox.__init__(self, group_name)
        the_layout = QVBoxLayout()
        self.setLayout(the_layout)
        self.widget_dict = {}
        rows = 0
        for module_name, name_list in name_dict.items():
            the_layout.addWidget(QLabel(module_name))
            for txt in name_list:
                cb = QRadioButton(txt)
                cb.setFont(regular_small_font)
                the_layout.addWidget(cb, rows, 0)
                if handler != None:
                    cb.toggled.connect(handler)
                self.widget_dict[txt] = cb
                rows += 1
        return

    @property
    def value(self):
        for (key, w) in self.widget_dict.items():
            if w.isChecked():
                return key
        return None

    def click_item(self, name):
        self.widget_dict[name].click()
    
class CheckGroup(QGroupBox):
    def __init__(self, text_list, group_name=None, handler = None):
        QGroupBox.__init__(self, group_name)
        the_layout = QVBoxLayout()
        self.setLayout(the_layout)
        self.widget_dict = OrderedDict([])
        for txt in text_list:
            cb = QCheckBox(txt)
            the_layout.addWidget(cb)
            if handler != None:
                cb.toggled.connect(handler)
            self.widget_dict[txt] = cb
        return

class CheckGroupNoParameters(QGroupBox):
    def __init__(self, group_name, name_list, default=None, help_instance=None, handler=None, help_dict=None):
        QGroupBox.__init__(self, group_name)
        self.handler = handler
        self.help_dict = help_dict
        self.help_instance = help_instance

        self.the_layout = QVBoxLayout()
        self.the_layout.setSpacing(5)
        self.the_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(self.the_layout)
        self.widget_dict = OrderedDict([])
        self.is_popup = False
        self.create_check_boxes(name_list)
        if default is not None:
            self.set_myvalue([default])
        return
    
    def reset(self):
        for cb in self.widget_dict.values():
            cb.setChecked(False)

    def create_check_boxes(self, name_list):
        for txt in name_list:
            qh = QHBoxLayout()
            cb = QCheckBox(txt)
            cb.setFont(regular_small_font)
            qh.addWidget(cb)
            qh.addStretch()
            self.the_layout.addLayout(qh)
            if self.handler != None:
                cb.toggled.connect(self.handler)
            self.widget_dict[txt] = cb
            if (self.help_dict != None) and (self.help_instance != None):
                if txt in self.help_dict:
                    help_button_widget = self.help_instance.create_button(txt, self.help_dict[txt])
                    qh.addWidget(help_button_widget)

    def recreate_check_boxes(self, new_name_list):
        for cb in self.widget_dict.values():
            cb.hide()
            cb.deleteLater()
            del cb
        self.widget_dict = {}
        self.create_check_boxes(new_name_list)
    
    # returns a list where each item is [name, parameter value]
    def get_myvalue(self):
        result = []
        for (fe, val) in self.widget_dict.items():
            if val.isChecked():
                result.append(fe)
        return result
    
    # Takes a lists where each item is [name, parameter value]
    def set_myvalue(self, true_items):
        self.reset()
        for fe in true_items:
            self.widget_dict[fe].setChecked(True)
    value = property(get_myvalue, set_myvalue)

class CheckGroupWithParameters(QGroupBox):
    def __init__(self, group_name, name_list, param_type = int, default_param = None, help_instance = None, handler = None, help_dict = None):
        QGroupBox.__init__(self, group_name)
        the_layout = QVBoxLayout()
        the_layout.setSpacing(5)
        the_layout.setContentsMargins(1, 1, 1, 1)
        self.setLayout(the_layout)
        self.widget_dict = OrderedDict([])
        self.mytype= param_type
        self.is_popup = False
        if default_param == None:
            default_param = ""
        self.default_param = default_param
        for txt in name_list:
            qh = QHBoxLayout()
            cb = QCheckBox(txt)
            cb.setFont(QFont('SansSerif', 12))
            efield = QLineEdit(str(default_param))
            efield.setFont(QFont('SansSerif', 10))
            efield.setMaximumWidth(25)
            qh.addWidget(cb)
            qh.addStretch()
            qh.addWidget(efield)
            the_layout.addLayout(qh)
            if handler != None:
                cb.toggled.connect(handler)
            self.widget_dict[txt] = [cb, efield]
            if (help_dict != None) and (help_instance != None):
                if txt in help_dict:
                    help_button_widget = help_instance.create_button(txt, help_dict[txt])
                    qh.addWidget(help_button_widget)
        return
    
    def reset(self):
        for [cb, efield] in self.widget_dict.values():
            cb.setChecked(False)
            efield.setText(str(self.default_param))
    
    # returns a list where each item is [name, parameter value]
    def get_myvalue(self):
        result = []
        for (fe, val) in self.widget_dict.items():
            if val[0].isChecked():
                result.append([fe, (self.mytype)(val[1].text())])
        return result
    
    # Takes a lists where each item is [name, parameter value]
    def set_myvalue(self, true_items):
        self.reset()
        for (fe, the_val) in true_items:
            self.widget_dict[fe][0].setChecked(True)
            self.widget_dict[fe][1].setText(str(the_val))
    
    value = property(get_myvalue, set_myvalue)
            
class qButtonWithArgumentsClass(QWidget):
    def __init__(self, display_text, todo, arg_dict, help_instance = None, max_field_size = None):
        super(qButtonWithArgumentsClass, self).__init__()
        self.todo = todo
        self.setContentsMargins(1, 1, 1, 1)
        newframe = QHBoxLayout()
        self.setLayout(newframe)
        newframe.setSpacing(1)
        newframe.setContentsMargins(1, 1, 1, 1)
        
        new_but = QPushButton(display_text)
        new_but.setContentsMargins(1, 1, 1, 1)
        new_but.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        new_but.setFont(regular_font)
        new_but.setAutoDefault(False)
        new_but.setDefault(False)
        newframe.addWidget(new_but)
        new_but.clicked.connect(self.doit)
        self.arg_hotfields = []
        for k in sorted(arg_dict.keys()):
            if isinstance(arg_dict[k], list):
                the_list = arg_dict[k]
                if len(the_list) == 0:
                    qe = qHotField(k, str, "", the_list, pos = "top", max_size = max_field_size)
                else:
                    qe = qHotField(k, type(arg_dict[k][0]), arg_dict[k][0], the_list, pos = "top", max_size = max_field_size)
            else:
                qe = qHotField(k, type(arg_dict[k]), arg_dict[k], pos = "top", max_size = max_field_size)
            newframe.addWidget(qe)
            newframe.setAlignment(qe, QtCore.Qt.AlignLeft)
            self.arg_hotfields.append(qe)
        newframe.addStretch()
        if hasattr(todo, "help_text"):
            if (help_instance == None):
                print "No help instance specified."
            else:
                help_button_widget = help_instance.create_button(display_text, todo.help_text)
                newframe.addWidget(help_button_widget)
                QtGui.QToolTip.setFont(regular_font)
                self.setToolTip(todo.help_text)
            
    def doit(self):
        if len(self.arg_hotfields) > 0:
            arg_dict = {}
            for qe in self.arg_hotfields:
                arg_dict[qe.name] = qe.value
            self.todo(**arg_dict)
        else:
            self.todo()

class CommandTabWidget(QTabWidget):
    def __init__(self, help_instance = None):
        QTabWidget.__init__(self)
        self.help_instance = help_instance
        
    def add_command_tab(self, command_list, tab_name = "Commands"):
        outer_widget = QWidget()
        outer_layout = QVBoxLayout()
        outer_widget.setLayout(outer_layout)
        outer_layout.setContentsMargins(2, 2, 2, 2)
        outer_layout.setSpacing(1)
        for c in command_list:
            new_command = qButtonWithArgumentsClass(c[1], c[0], c[2], self.help_instance, max_field_size = 100)
            outer_layout.addWidget(new_command)
            outer_layout.setAlignment(new_command,QtCore.Qt.AlignTop )
        outer_layout.addStretch()
        scroller = QScrollArea()
        scroller.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroller.setWidget(outer_widget)
        scroller.setWidgetResizable(True)
        self.addTab(scroller, tab_name)

class Separator(QFrame):
    def __init__(self):
        QFrame.__init__(self)
        self.setFrameShape(QFrame.HLine)

#############
# This group of widgets have functionality that is covered by qHotField
#
# This has been superseded by qHotField.
class qLabeledCheck(QWidget): 
    def __init__(self, name, arg_dict, pos = "side", max_size = 200):
        QWidget.__init__(self)
        self.setContentsMargins(1, 1, 1, 1)
        if pos == "side":
            self.layout1=QHBoxLayout()
        else:
            self.layout1 = QVBoxLayout()
        self.layout1.setContentsMargins(1, 1, 1, 1)
        self.layout1.setSpacing(1)
        self.setLayout(self.layout1)
        self.cbox = QCheckBox()
        # self.efield.setMaximumWidth(max_size)
        self.cbox.setFont(QFont('SansSerif', 12))
        self.label = QLabel(name)
        # self.label.setAlignment(Qt.AlignLeft)
        self.label.setFont(QFont('SansSerif', 12))
        self.layout1.addWidget(self.label)
        self.layout1.addWidget(self.cbox)
        self.arg_dict = arg_dict
        self.name = name
        self.mytype = type(self.arg_dict[name])
        if self.mytype != bool:
            self.cbox.setChecked(bool(self.arg_dict[name]))
        else:
            self.cbox.setChecked(self.arg_dict[name])
        self.cbox.toggled.connect(self.when_modified)
        self.when_modified()
        
    def when_modified(self):
        self.arg_dict[self.name]  = self.cbox.isChecked()
        
    def hide(self):
        QWidget.hide(self)

# This has been superseded by qHotField
class qLabeledEntry(QWidget):
    def __init__(self, name, arg_dict, pos = "side", max_size = 200):
        QWidget.__init__(self)
        self.setContentsMargins(1, 1, 1, 1)
        if pos == "side":
            self.layout1=QHBoxLayout()
        else:
            self.layout1 = QVBoxLayout()
        self.layout1.setContentsMargins(1, 1, 1, 1)
        self.layout1.setSpacing(1)
        self.setLayout(self.layout1)
        self.efield = QLineEdit("Default Text")
        # self.efield.setMaximumWidth(max_size)
        self.efield.setFont(QFont('SansSerif', 12))
        self.label = QLabel(name)
        # self.label.setAlignment(Qt.AlignLeft)
        self.label.setFont(QFont('SansSerif', 12))
        self.layout1.addWidget(self.label)
        self.layout1.addWidget(self.efield)
        self.arg_dict = arg_dict
        self.name = name
        self.mytype = type(self.arg_dict[name])
        if self.mytype != str:
            self.efield.setText(str(self.arg_dict[name]))
            self.efield.setMaximumWidth(50)
        else:
            self.efield.setText(self.arg_dict[name])
            self.efield.setMaximumWidth(100)
        self.efield.textChanged.connect(self.when_modified)
        
    def when_modified(self):
        if self.mytype == int:
            if self.efield.text != None:
                self.arg_dict[self.name]  = int(self.efield.text())
        else:
            self.arg_dict[self.name]  = self.efield.text()
        
    def hide(self):
        QWidget.hide(self)

# This has been superseded by qHotField      
class qLabeledPopup(QWidget):
    def __init__(self, name, arg_dict, item_list, pos = "side", max_size = 200):
        QWidget.__init__(self)
        self.setContentsMargins(1, 1, 1, 1)
        if pos == "side":
            self.layout1=QHBoxLayout()
        else:
            self.layout1 = QVBoxLayout()
        self.layout1.setContentsMargins(1, 1, 1, 1)
        self.layout1.setSpacing(1)
        self.setLayout(self.layout1)
        
        self.item_combo = QComboBox()
        self.item_combo.addItems(item_list)
        self.item_combo.setFont(QFont('SansSerif', 12))
        self.label = QLabel(name)
        # self.label.setAlignment(Qt.AlignLeft)
        self.label.setFont(QFont('SansSerif', 12))
        self.layout1.addWidget(self.label)
        self.layout1.addWidget(self.item_combo)
        self.arg_dict = arg_dict
        self.name = name
        self.item_combo.textChanged.connect(self.when_modified)
        self.item_combo.currentIndexChanged.connect(self.when_modified)
        self.when_modified()
        
    def when_modified(self):
        self.arg_dict[self.name]  = self.item_combo.currentText()
        
    def hide(self):
        QWidget.hide(self)
 
# This has been superseded by qHotField
class CheckWithHelp(QHBoxLayout):
    def __init__(self, the_text, help_dict = None, help_instance = None):
        QHBoxLayout.__init__(self)
        # new_layout = QHBoxLayout()
        self.cb = QCheckBox(the_text)
        self.cb.setFont(QFont('SansSerif', 12))
        self.addWidget(self.cb)
        if help_dict != None:
            if the_text in help_dict.keys():
                if (help_instance == None):
                    print "No help instance specified."
                else:
                    help_button_widget = help_instance.create_button(the_text, help_dict[the_text])
                    self.addWidget(help_button_widget)

# This has been superseded by qHotField
class FieldWithHelp(QHBoxLayout):
    def __init__(self, the_text, help_dict = None, help_instance = None):
        QHBoxLayout.__init__(self)
        cb = QLineEdit("")
        cb.setMinimumWidth(50)
        cb.setMinimumWidth(200)
        self.addWidget(cb)
        if help_dict != None:
            if the_text in help_dict.keys():
                if (help_instance == None):
                    print "No help instance specified."
                else:
                    help_button_widget = help_instance.create_button(the_text, help_dict[the_text])
                    self.addWidget(help_button_widget)
        cb.setFont(QFont('SansSerif', 12))
        self.cb = cb   

#############
# The widgets below here seem to be old and no longer used.

class oldRadioGroup(QGroupBox):
    def __init__(self, text_list, group_name=None, handler = None, help_dict = None, help_instance = None):
        QGroupBox.__init__(self, group_name)
        the_layout = QVBoxLayout()
        self.setLayout(the_layout)
        self.widget_dict = {}
        for txt in text_list:
            cb = QRadioButton(txt)
            the_layout.addWidget(cb)
            if handler != None:
                cb.toggled.connect(handler)
            self.widget_dict[txt] = cb
            if help_dict != None:
                if help_instance == None:
                    print "No help instance specified along with help_dict"
                else:
                    the_layout.addWidget(help_instance.create_button(help_dict[txt][0], help_dict[txt][1]))
        return
    
class qOldButtonWithArgumentsClass(QWidget):
    def __init__(self, display_text, todo, arg_dict, help_instance = None):
        super(qOldButtonWithArgumentsClass, self).__init__()
        self.todo = todo
        self.arg_dict = arg_dict
        # self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setContentsMargins(1, 1, 1, 1)
        newframe = QHBoxLayout()
        self.setLayout(newframe)
        newframe.setSpacing(1)
        newframe.setContentsMargins(1, 1, 1, 1)
        
        new_but = QPushButton(display_text)
        new_but.setContentsMargins(1, 1, 1, 1)
        new_but.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        new_but.setFont(QFont('SansSerif', 12))
        new_but.setAutoDefault(False)
        new_but.setDefault(False)
        newframe.addWidget(new_but)
        new_but.clicked.connect(self.doit)
        for k in sorted(arg_dict.keys()):
            if isinstance(self.arg_dict[k], list):
                the_list = self.arg_dict[k]
                self.arg_dict[k] = ""
                qe = qLabeledPopup(k, self.arg_dict, the_list, "top")
            elif isinstance(self.arg_dict[k], bool):
                qe = qLabeledCheck(k, self.arg_dict, "top")
            else:
                qe = qLabeledEntry(k, self.arg_dict,  "top")
            newframe.addWidget(qe)
        newframe.addStretch()
        if hasattr(todo, "help_text"):
            if (help_instance == None):
                print "No help instance specified."
            else:
                help_button_widget = help_instance.create_button(display_text, todo.help_text)
                newframe.addWidget(help_button_widget)
            
    def doit(self):
        if len(self.arg_dict.keys()) > 0:
            self.todo(**self.arg_dict)
        else:
            self.todo()

class aMyCheck(QCheckBox):
    def __init__(self, var, text, state = False):
        QCheckBox.__init__(self, text)
        self.setFont(QFont('SansSerif', 12))
        self.setChecked(state)
        self.var = var
        self.toggled.connect(self.when_modified)
        
    def when_modified(self):
        self.var.set(self.isChecked())
        
def qbutton_with_arguments(parent, todo, button_display_text, argument_list):
    cWidget = QWidget()
    parent.addWidget(cWidget)
    cWidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    cWidget.setContentsMargins(1, 1, 1, 1)
    newframe = QHBoxLayout()
    cWidget.setLayout(newframe)
    newframe.setSpacing(1)
    newframe.setContentsMargins(1, 1, 1, 1)
    qmy_button(newframe, todo, button_display_text)
    for entry in argument_list:
        # entry[0] is the variable, entry[1] is the text to display
        if len(entry) == 2:
            qe = qlabeled_entry(entry[0], entry[1], "top")
            qe.efield.returnPressed.connect(todo)
            
            var_val = entry[0].get()
            if type(var_val) == int:
                qe.efield.setText(str(var_val))
                qe.efield.setMaximumWidth(50)
            else:
                qe.efield.setText(var_val)
                qe.efield.setMaximumWidth(100)
            
            newframe.addWidget(qe)
        else:
            qp = aLabeledPopup(entry[0], entry[1], entry[2], "top")
            newframe.addWidget(qp)
    return

class aLabeledPopup(QWidget):
    def __init__(self, var, text, item_list, pos = "side", max_size = 200):
        QWidget.__init__(self)
        self.setContentsMargins(1, 1, 1, 1)
        if pos == "side":
            self.layout1=QHBoxLayout()
        else:
            self.layout1 = QVBoxLayout()
        self.layout1.setContentsMargins(1, 1, 1, 1)
        self.layout1.setSpacing(1)
        self.setLayout(self.layout1)
        
        self.item_combo = QComboBox()
        self.item_combo.addItems(item_list)
        self.item_combo.setFont(QFont('SansSerif', 12))
        self.label = QLabel(text)
        # self.label.setAlignment(Qt.AlignLeft)
        self.label.setFont(QFont('SansSerif', 12))
        self.layout1.addWidget(self.label)
        self.layout1.addWidget(self.item_combo)
        self.var = var
        self.item_combo.textChanged.connect(self.when_modified)
        self.item_combo.currentIndexChanged.connect(self.when_modified)
        self.when_modified()
        
    def when_modified(self):
        self.var.set(self.item_combo.currentText())
        
    def hide(self):
        QWidget.hide(self)
        
class qlabeled_entry(QWidget):
    def __init__(self, var, text, pos = "side", max_size = 200):
        QWidget.__init__(self)
        self.setContentsMargins(1, 1, 1, 1)
        if pos == "side":
            self.layout1=QHBoxLayout()
        else:
            self.layout1 = QVBoxLayout()
        self.layout1.setContentsMargins(1, 1, 1, 1)
        self.layout1.setSpacing(1)
        self.setLayout(self.layout1)
        self.efield = QLineEdit("Default Text")
        # self.efield.setMaximumWidth(max_size)
        self.efield.setFont(QFont('SansSerif', 12))
        self.label = QLabel(text)
        # self.label.setAlignment(Qt.AlignLeft)
        self.label.setFont(QFont('SansSerif', 12))
        self.layout1.addWidget(self.label)
        self.layout1.addWidget(self.efield)
        self.var = var        
        self.efield.textChanged.connect(self.when_modified)
        
    def when_modified(self):
        self.var.set(self.efield.text())
        
    def hide(self):
        QWidget.hide(self)
        
def qmy_button(parent, todo, display_text, dummy1 = "x", dummy2 = "x"):
    new_but = QPushButton(display_text)
    new_but.setContentsMargins(1, 1, 1, 1)
    new_but.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
    new_but.setFont(QFont('SansSerif', 12))
    new_but.setAutoDefault(False)
    new_but.setDefault(False)
    parent.addWidget(new_but)
    new_but.clicked.connect(todo)
    return new_but
