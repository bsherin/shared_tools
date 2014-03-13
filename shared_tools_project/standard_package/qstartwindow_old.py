"""
This module contains the class QStartWindow which creates the start window from which
analyses are performed. In order to populate the window, it uses the information in shared_dicts.

"""

import sys, pickle, cPickle, time, shelve
import parameter_management

from PySide.QtCore import QThread, Signal # @UnresolvedImport
from PySide.QtGui import QDialog, QFrame, QFormLayout, QFileDialog, QMessageBox, QHBoxLayout # @UnresolvedImport
from PySide.QtGui import QVBoxLayout, QComboBox, QCheckBox, QFont, QLineEdit, QGroupBox, QLayout, QWidgetItem # @UnresolvedImport

from montecarlo_package.monte_carlo import MonteCarloDescriptorClass, PP
from montecarlo_package.qmonte_carlo_window import qmonte_carlo_window
from mywidgets import qmy_button, qIntVar, qbutton_with_arguments, RadioGroup, CheckGroupWithParameters, Separator
from help_tools import helpForWindow, helpToggler
from va.feature_extractors import feature_extractor_dict, feature_extractor_help_dict

current_analysis_name = None
current_dimension = None
current_code = None
monte_carlo_report_name = None
current_reports_dict = None

analysis_instance_array = []

class AnalysisThreadClass(QThread):
    
    done_signal = Signal(int)
    
    def __init__(self, parent, AnalysisClass):
        super(AnalysisThreadClass, self).__init__()
        self.AnalysisClass = AnalysisClass
        self.parent = parent
        
    def run(self):
        print("I am entering run")
        self.analysis_instance = self.parent.run_current_analysis_without_display(self.AnalysisClass)
        analysis_instance_array.append(self.analysis_instance)
        self.done_signal.emit(len(analysis_instance_array) - 1)

class QStartWindowClass(QDialog):
    def __init__(self, shared_dicts, data_portal, preferred_parameter_ordering = None, parent = None):
        super(QStartWindowClass, self).__init__(parent)
        
        self.data_portal =data_portal
        
        # First extract the defining parameters from shared_dicts
        self.shared_dicts = shared_dicts
        self.analysis_dict = shared_dicts.analysis_dict
        self.ordered_analysis_keys = shared_dicts.ordered_analysis_keys
        self.analysis_window_dict = shared_dicts.analysis_window_dict
        self.help_instance = helpForWindow()
        self.preferred_parameter_ordering = preferred_parameter_ordering
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # just create the param frame so I have it available.
        qpframe = self.QParamFrameClass(self)
        
        # Create and add the left frame
        qlframe = self.QLeftFrameClass(qpframe, self)
        layout.addLayout(qlframe)
        vline = QFrame()
        vline.setFrameShape(QFrame.VLine)
        layout.addWidget(vline)

        
        # Create the right hand frame frame. This has the list of defining parameters plus a popup list of report names
        # Initially there isn't much in the parameter list.
        self.right_pane = QVBoxLayout()
        layout.addLayout(self.right_pane)
        
        # We wrap the list of parameters ina group box just for visual appeal.
        param_group = QGroupBox("Parameters")
        self.right_pane.addWidget(param_group)
        param_group.setLayout(qpframe)
        
        # Create the report names popup list.
        self.report_names_combo = QComboBox()
        self.report_names_combo.currentIndexChanged.connect(self.report_selected)
        self.right_pane.addWidget(self.report_names_combo)
        self.report_selected()
        
        # Display some info about the current running environment.
        print sys.version
        print "am I running in 64 bit?"
        print("%x" % sys.maxsize, sys.maxsize > 2 ** 32)
        
    def populate_report_list(self):
        global current_reports_dict
        self.report_names_combo.clear()
        current_reports_dict = self.analysis_dict [current_analysis_name].reports_dict
        self.report_names_combo.addItems(current_reports_dict.keys())
        self.report_selected()
        
    def report_selected(self):
        global monte_carlo_report_name
        monte_carlo_report_name = self.report_names_combo.currentText()
        print "current report is ", monte_carlo_report_name

    class QParamFrameClass(QFormLayout):
        """
        QParamFrameClass creates the left frame of the start window.
        It's a list of parameters followed up a popup list of reports.
        When it's initially created, there isn't much in it.
        """
        def __init__(self, swclass):
            QFormLayout.__init__(self)
            self.swclass = swclass
            self.make_widgets()

        def make_widgets(self):
            self.params = {}
            checkbox_counter = 0
            for key in parameter_management.ordered_key_list:
                thetype = type(parameter_management.parameter_defaults[key])
                new_layout = QHBoxLayout()
                if thetype == bool:
                    cb = QCheckBox(key)
                    cb.setFont(QFont('SansSerif', 12))
                    new_layout.addWidget(cb)
                    self.insertRow(checkbox_counter, new_layout)
                    checkbox_counter += 1
                    if parameter_management.parameter_defaults[key]:
                        cb.setChecked(True)
                else:
                    cb = QLineEdit("")
                    self.addRow(key,cb)
                    theLabel=self.labelForField(cb)
                    theLabel.setFont(QFont('SansSerif', 12))
                    cb.setFont(QFont('SansSerif', 12))
                    if (thetype == int) or (thetype == float):
                        cb.setText(str(parameter_management.parameter_defaults[key]))
                    else:
                        cb.setText(parameter_management.parameter_defaults[key])
                self.params[key] = cb
                
        def recreate_param_widgets(self):
            self.make_widgets()

        def grab_values(self):
            grabbed_param_dict = {}
            for key in self.params.keys():
                if type(parameter_management.parameter_defaults[key]) == type(True):
                    grabbed_param_dict[key] = self.params[key].isChecked()
                else:
                    grabbed_param_dict[key] = self.params[key].text()
            return grabbed_param_dict
        
        def delete_param_widgets(self):
            self.recursive_delete(self)
        
        def recursive_delete(self, item):
            if issubclass(type(item), QLayout):
                while item.count() > 0:
                    child = item.takeAt(0)
                    self.recursive_delete(child)
                    if type(child) == QWidgetItem:
                    # del child
                        w = child.widget()
                        w.hide()
                        w.deleteLater()
                    del child
            
        def olddelete_param_widgets(self):
            for w in self.params.keys():
                cb = self.params[w]
                if type(parameter_management.parameter_defaults[w]) != type(True):
                    the_label = self.labelForField(cb)
                    the_label.hide()
                    the_label.deleteLater()
                cb.hide()
                cb.deleteLater()

    class QLeftFrameClass(QVBoxLayout):
        """
        QLeftFrameClass creates the right frame of the start window.
        It uses information in swclass.ordered_analysis_keys to know what analyses to offer.
        
        When the Run Analysis button is pressed then an analysis is begun. 
        It users the current analysis class, by pulling the class from analysis_dict.
        Note that each analysis knows which window to use to display it.
        """
        def __init__(self, pframe, swclass):
            QVBoxLayout.__init__(self)
            self.swclass = swclass
            self.pframe = pframe
            self.analysis_widgets = {}
            self.dimension_widgets = {}
            self.code_widgets = {}
            self.fe_widgets = {}

            self.make_widgets()
            self.awin_list = []
            self.thread_array = []
            self.code_group = None
    
        def make_widgets(self):
            
            # Make radio buttons, one for each analysis
            analysis_group = RadioGroup(self.swclass.ordered_analysis_keys, "Analysis", self.analysis_press, 
                                                            help_dict = self.swclass.shared_dicts.analysis_help_dict, help_instance = self.swclass.help_instance)
            self.addWidget(analysis_group)
            self.analysis_widgets = analysis_group.widget_dict
            
            # Layout for holding Code selector stuff
            self.code_selector_layout = QHBoxLayout()
            self.addLayout(self.code_selector_layout)
            
            # Make radio buttons, one for each dimension from the dataportal
            dimension_group = RadioGroup(self.swclass.data_portal.segment_dict.keys(), "Dimension", self.dimension_press)
            self.code_selector_layout.addWidget(dimension_group)
            self.dimension_widgets = dimension_group.widget_dict
            
            # Make check boxes, one for each feature extractor
            # fe_group = CheckGroup(feature_extractor_dict, "Feature Extractors", None)

            fe_group = CheckGroupWithParameters(feature_extractor_dict, default_param = 1, group_name = "Feature Extractors", 
                                                                            handler = None, help_dict = feature_extractor_help_dict, help_instance = self.swclass.help_instance)
            self.addWidget(fe_group)
            self.fe_widgets = fe_group.widget_dict

            self.addWidget(Separator())
            
            # Create the buttons for launching analyses, etc.
            self.run_button_layout = QHBoxLayout()
            self.addLayout(self.run_button_layout)
            
            qmy_button(self.run_button_layout, self.run_analysis, "Run Analysis")

            self.debug_check = QCheckBox("debug")
            self.debug_check.setChecked(True)
            self.run_button_layout.addWidget(self.debug_check)

            qmy_button(self, self.load_analysis, "Load a Saved Analysis")
            
            self.forced_iterations = qIntVar()
            self.forced_iterations.set(2)
            arglist = [[self.forced_iterations, "forced iters"]]
            monte_help_text = ["Monte Carlo Runs", "Run the analysis the given number of times"]
            qbutton_with_arguments(self, self.run_monte_carlo, "Run Monte", arglist, help_text = monte_help_text, help_instance = self.swclass.help_instance)
            
            create_mcd_help_text = ["Create MCD", "Creates an MCD descriptor file"]
            arglist = [[self.forced_iterations, "forced iters"]]
            qbutton_with_arguments(self, self.create_monte_carlo_descriptor, "Create MCD", arglist, help_text = create_mcd_help_text, help_instance = self.swclass.help_instance)
            
            # load_mcd_help_text = ["Load MCD", "Loads a monte carlo descriptor file"]
            qmy_button(self, self.load_mcd, "Load MCD")
            # load_report_help_text = ["Load MCD report", "Loads a saved report from a monte carlo run."]
            qmy_button(self, self.load_report, "Load Report" )
            self.addWidget(Separator())
            qmy_button(self, self.restore_defaults, 'Restore Defaults')
            help_toggler = helpToggler(self.swclass.help_instance)
            self.addWidget(help_toggler)
        
        def check_all_files(self):
            for fn in self._folder_check_vars.keys():
                self._folder_check_widgets[fn].setChecked(True)
                
        def uncheck_all_files(self):
            for fn in self._folder_check_vars.keys():
                self._folder_check_widgets[fn].setChecked(False)
                
        def grab_fes(self):
            grabbed_fe_dict = {}
            grabbed_fe_weight_dict = {}
            for fe in self.fe_widgets.keys():
                grabbed_fe_dict[fe] = self.fe_widgets[fe][0].isChecked()
                grabbed_fe_weight_dict[fe] = self.fe_widgets[fe][1].text()
            return grabbed_fe_dict, grabbed_fe_weight_dict

        def analysis_press(self, tvar):
            global current_analysis_name
            if tvar:
                for analysis in self.swclass.ordered_analysis_keys:
                    if self.analysis_widgets[analysis].isChecked():
                        current_analysis_name = analysis
                        break;
                print "current analysis is ", current_analysis_name
                
            self.pframe.delete_param_widgets()
            parameter_management.reset_parameter_defaults(self.swclass.analysis_dict[current_analysis_name].relevant_parameters, self.swclass.preferred_parameter_ordering)
            self.pframe.recreate_param_widgets()
            self.swclass.populate_report_list()
            
        def dimension_press(self, tvar):
            global current_dimension
            if tvar:
                for dimension in self.swclass.data_portal.segment_dict:
                    if self.dimension_widgets[dimension].isChecked():
                        current_dimension = dimension
                        break;
                print "current dimension is ", current_dimension
                if self.code_group != None:
                    self.code_selector_layout.removeWidget(self.code_group)
                    self.code_group.hide()
                    self.code_group.deleteLater()
                self.code_list = [c.name for c in self.swclass.data_portal.codes_dict[dimension]]
                self.code_group = RadioGroup(self.code_list, "Code", self.code_press)
                self.code_widgets = self.code_group.widget_dict
                self.code_selector_layout.addWidget(self.code_group)
                
        def code_press(self, tvar):
            global current_code
            if tvar:
                for cod in self.code_list:
                    if self.code_widgets[cod].isChecked():
                        current_code = cod
                        break;
                print "current code is", current_code
        
        def create_monte_carlo_descriptor(self, save_file=True):
            current_analysis_name = self.get_analysis_name()
            xml_list = self.get_file_list()
            mcd = MonteCarloDescriptorClass(current_analysis_name, self.pframe.grab_values(), xml_list, monte_carlo_report_name, parameter_management.parameter_defaults, self.forced_iterations.get())
            if save_file:
                fname = QFileDialog.getSaveFileName(caption = "Pick a Save File for the Monte Carlo Descriptor")[0]
                f = open(fname, 'w')
                cPickle.dump(mcd, f)
                f.close()
            return mcd
        
        def get_analysis_name(self):
            for analysis in self.swclass.ordered_analysis_keys:
                if self.analysis_widgets[analysis].isChecked():
                    analysis_name = analysis
                    break
            return analysis_name
        
        def run_analysis(self):
            """ 
            This is the method that is called first when the user clicks the Run Analysis button.
            It then calls run_current_analysis, if we are in debug mode. 
            Otherwise it creates an AnalysisThreadClass instance.
            """
            print "entering run analysis"
            current_analysis_name = self.get_analysis_name()
            AnalysisClass = self.swclass.analysis_dict[current_analysis_name]
            if self.debug_check.isChecked():
                start_time = time.time()
                self.run_current_analysis(AnalysisClass)
                print "it took", time.time() - start_time, "seconds."
            else:
                new_thread = AnalysisThreadClass(self, AnalysisClass)
                self.thread_array.append(new_thread)
                new_thread.done_signal.connect(self.display_window_for_analysis)
                new_thread.start()
                print "I mead it beyond the start"
                
        def run_current_analysis(self, AnalysisClass):
            """
            This is used in debug mode. It creates an instance of the AnalysisClass, then creates the appropriate
            window and passes the analysis instance. 
            """
            params = self.pframe.grab_values()
            fe_dict, fe_weights = self.grab_fes()
            analysis_instance = AnalysisClass(self.swclass.data_portal, current_dimension, current_code, fe_dict, fe_weights, params)
            awin = self.swclass.analysis_window_dict[AnalysisClass.display_window_name](analysis_instance) 
            awin.show()
            self.awin_list.append(awin)
            
        def run_current_analysis_without_display(self, AnalysisClass):
            params = self.pframe.grab_values()
            fe_dict, fe_weights = self.grab_fes()
            analysis_instance = AnalysisClass(self.swclass.data_portal, current_dimension, current_code, fe_dict, fe_weights, params)
            return analysis_instance
            
        def display_window_for_analysis(self, index):
            analysis_instance = analysis_instance_array[index]
            awin = self.swclass.analysis_window_dict[analysis_instance.display_window_name](analysis_instance) 
            awin.show()
            self.awin_list.append(awin)
        
        def get_file_list(self):
            return [fn for fn in self.xml_list if self._folder_check_vars[fn].get()]
        
        def load_analysis(self):
            fname = QFileDialog.getOpenFileName()[0]
            f = open(fname, 'r')
            analysis_instance = pickle.load(f) # I changed this to Pickle to see if a memory error goes away
            parameter_management.reset_parameter_defaults(analysis_instance.relevant_parameters, self.swclass.preferred_parameter_ordering)
            awin =  self.swclass.analysis_window_dict[analysis_instance.display_window_name](analysis_instance)
            awin.show()
            self.awin_list.append(awin)
            f.close()
            
        def load_mcd(self):
            fname = QFileDialog.getOpenFileName(caption = "Select MCD File")[0]
            f = open(fname, 'r')
            mcd = cPickle.load(f)
            f.close()
            dbname = QFileDialog.getSaveFileName(caption = "Pick a Save File for the Report")[0]
            awin= qmonte_carlo_window(mcd, self.swclass.analysis_dict , self.swclass.analysis_window_dict, self.awin_list, dbfilename=dbname, runit=True)
            awin.show()
            self.awin_list.append(awin)
            
        def load_report(self):
            report_fname = QFileDialog.getOpenFileName(caption = "Select a Monte Carlo Report File")[0]
            db = shelve.open(report_fname, protocol = PP)
            mcd = db['mcd']
            db.close()
            awin = qmonte_carlo_window(mcd, self.swclass.analysis_dict , self.swclass.analysis_window_dict, self.awin_list, runit=False, dbfilename=report_fname)
            awin.show()
            self.awin_list.append(awin)
            
        def run_monte_carlo(self):
            mcd = self.create_monte_carlo_descriptor(save_file=False)
            report_fname = QFileDialog.getSaveFileName(caption = "Pick a Save File for the Report")[0]
            self.run_mc_analysis(mcd, report_fname)
                
        def run_mc_analysis(self, mcd, report_fname):
            if monte_carlo_report_name == None:
                print "No report is specified"
                msgBox = QMessageBox()
                msgBox.setText("No report specified.")
                msgBox.exec_()
            else:
                awin = qmonte_carlo_window(mcd, self.swclass.analysis_dict , self.swclass.analysis_window_dict, self.awin_list, runit=True, dbfilename=report_fname)
                awin.show()
                self.awin_list.append(awin)
                
        def restore_defaults(self):
            self.pframe.delete_param_widgets()
            parameter_management.reset_parameter_defaults(self.swclass.analysis_dict[current_analysis_name].relevant_parameters, self.swclass.preferred_parameter_ordering)
            self.pframe.recreate_param_widgets()
            self.swclass.populate_report_list()
    






