"""
This module contains the class QStartWindow which creates the start window from which
analyses are performed. In order to populate the window, it uses the information in shared_dicts.

"""
import sys, os, pickle, cPickle, gzip, time, shelve
import parameter_management

from PySide.QtGui import QMainWindow, QWidget, QFileDialog, QHBoxLayout, QSizePolicy
from PySide.QtGui import QVBoxLayout 
from PySide.QtGui import QLayout, QWidgetItem
from PySide.QtCore import QThread, Signal, Qt # @UnresolvedImport

from montecarlo_package.monte_carlo import MonteCarloDescriptorClass, PP
from montecarlo_package.qmonte_carlo_window import qmonte_carlo_window
from mywidgets import  RadioGroup, CommandTabWidget, show_message, qHotField, create_menu, QScroller
from help_tools import helpForWindow, helpToggler
from collections import OrderedDict

current_analysis_name = None
current_analysis_class = None

analysis_instance_array = []

class AnalysisThreadClass(QThread):
    
    done_signal = Signal(int)
    
    def __init__(self, parent, AnalysisClass, param_instance):
        super(AnalysisThreadClass, self).__init__()
        self.AnalysisClass = AnalysisClass
        self.parent = parent
        self.param_instance = param_instance
        
    def run(self):
        print("I am entering run")
        self.analysis_instance = self.AnalysisClass(self.param_instance, running_in_thread=True)
        analysis_instance_array.append(self.analysis_instance)
        self.done_signal.emit(len(analysis_instance_array) - 1)

class QStartWindowClass(QMainWindow):
    def __init__(self, analysis_dict, analysis_window_dict, feature_extractor_dict = None, parent = None):
        QMainWindow.__init__(self)
        self.sww = QStartWindowWidget(analysis_dict, analysis_window_dict, feature_extractor_dict, self)
        self.setCentralWidget(self.sww)
        # self.statusBar().showMessage('Ready')


class QStartWindowWidget(QWidget):
    def __init__(self, analysis_dict, analysis_window_dict, feature_extractor_dict, parent_window):
        QWidget.__init__(self)
        
        self.analysis_dict = analysis_dict
        self.ordered_analysis_keys = self.analysis_dict.keys()
        self.ordered_analysis_keys.sort()
        self.analysis_window_dict = analysis_window_dict
        self.feature_extractor_dict = feature_extractor_dict
        self.parent_window = parent_window
        self.setAcceptDrops(True)
        
        # Create a help instance
        self.help_instance = helpForWindow()
        
        # Make one big outer layout
        layout = QHBoxLayout()
        self.setLayout(layout)
        
        # just create the param frame so I have it available to reference when creating the left frame
        qpframe = self.QParamFrameClass(self)
        
        # Create the left frame
        # Put it in a widget so I can control it's size.
        qlframe = self.QLeftFrameClass(qpframe, self)
        qlwidget = QWidget()
        layout.addWidget(qlwidget)
        layout.setAlignment(qlwidget, Qt.AlignTop)
        qlwidget.setLayout(qlframe)
        qlwidget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lframe = qlframe
        
        # Create the right hand frame frame. This has the list of defining parameters plus a popup list of report names
        # Initially there isn't much in the parameter list.
        # Put it in a widget so I can control the size.
        qpwidget = QWidget()
        qpwidget.setMinimumWidth(400)
        layout.addWidget(qpwidget)
        self.right_pane = QScroller(qpframe)
        qpwidget.setLayout(self.right_pane)
        
        # Display some info about the current running environment.
        print sys.version
        print "am I running in 64 bit?"
        print("%x" % sys.maxsize, sys.maxsize > 2 ** 32)


    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            self.lframe.open_general(fullname=path)

    class QParamFrameClass(QVBoxLayout):
        """
        QParamFrameClass creates the right frame of the start window.
        It displays all of the relevant parameters associate with an analysis. 
        It makes use of special parameter display widgets.
        When it's initially created, there isn't much in it.
        """
        def __init__(self, swclass):
            QVBoxLayout.__init__(self)
            self.swclass = swclass
            self.make_widgets()

        def make_widgets(self):
            if current_analysis_name == None:
                return;
            self.param_widgets = OrderedDict()
            current_analysis = self.swclass.analysis_dict[current_analysis_name]
            help_instance = self.swclass.help_instance
            if hasattr(current_analysis, "parameters_help"):
                help_dict = current_analysis.parameters_help
            else:
                help_dict = {}
            
            # Create all of the parameter displaying widgets. Mostly this is done with qHotField
            display_ws = current_analysis.display_widgets
            current_parameter_defaults = current_analysis_class.relevant_parameters
            for (key, the_val) in current_parameter_defaults.items():
                if key in help_dict:
                    help_text = help_dict[key]
                else:
                    help_text = None
                if key in display_ws:  # If a special parameter display widget has been specified, use it. The rest will use qHotField.
                    self.param_widgets[key] = display_ws[key][0](key, the_val, help_instance = help_instance, **(display_ws[key][1]))
                elif type(the_val) == list: # 
                    self.param_widgets[key] = qHotField(key, type(the_val[0]), the_val[0],  value_list = the_val, pos = "right", help_text = help_text, help_instance = help_instance, min_size = 200)
                else:
                    self.param_widgets[key] = qHotField(key, type(the_val), the_val, pos = "right", help_text = help_text, help_instance = help_instance, min_size = 200)
                self.addWidget(self.param_widgets[key])
                
            self.addStretch()
                
        def recreate_param_widgets(self):
            self.make_widgets()
                    
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
            self.make_widgets()
            self.awin_list = []
            self.thread_array = []
            self.code_group = None
    
        def make_widgets(self):
            
            # Make a group radio buttons, one for each analysis
            self.analysis_group = RadioGroup("Analysis", self.swclass.analysis_dict.keys(), self.analysis_press, 
                                                            help_instance = self.swclass.help_instance)
            self.addWidget(self.analysis_group)
            
            self.iterations = qHotField("iterations", int, 1) # Number of iterations for monte carlo runs
            self.addWidget(self.iterations)
            
            self.run_in_thread = qHotField("run in thread", bool, False)
            self.addWidget(self.run_in_thread)
            
            # Create tabs that will hold buttons for launching analysis, etc.
            self.tabWidget = CommandTabWidget(self.swclass.help_instance)
            self.addWidget(self.tabWidget)
            command_list = [
                [self.run_analysis, "Run Analysis", {}, "Ctrl+r"],
                [self.open_general, "Open...", {}, "Ctrl+o"],
                [self.load_analysis, "Load a Saved Analysis...", {}, "Ctrl+a"],
                [self.create_monte_carlo_descriptor, "Save Settings...", {}, "Ctrl+s"],
                [self.load_mcd, "Load Saved Settings...", {}, "Ctrl+l"],
                [self.run_monte_carlo, "Run Monte", {}],
                [self.load_report, "Load Monte Carlo Report", {}],
                [self.restore_defaults, "Restore Defaults",{}],
                ]
            self.tabWidget.add_command_tab(command_list, "Do Stuff")
            self.addStretch()
            help_toggler = helpToggler(self.swclass.help_instance)
            self.addWidget(help_toggler)
            
            menubar = self.swclass.parent_window.menuBar()
            create_menu(self.swclass.parent_window, menubar, "File", command_list)
                
        def analysis_press(self, tvar):
            global current_analysis_name, current_analysis_class, current_parameter_defaults
            if tvar:
                current_analysis_name = self.analysis_group.value
                print "current analysis is ", current_analysis_name
            
            current_analysis_class = self.swclass.analysis_dict[current_analysis_name]
            self.pframe.delete_param_widgets()
            self.pframe.recreate_param_widgets()
        
        def create_monte_carlo_descriptor(self,  save_file=True):
            global current_analysis_name, current_analysis_class

            iterations = self.iterations.value
            params = parameter_management.AnalysisParameters(self.build_param_dict(), current_analysis_class.relevant_parameters)
            mcd = MonteCarloDescriptorClass(current_analysis_name, params, iterations)
            if save_file:
                fname = QFileDialog.getSaveFileName(caption = "Pick a Save File for the Monte Carlo Descriptor")[0]
                f = open(fname, 'w')
                cPickle.dump(mcd, f)
                f.close()
            return mcd
        create_monte_carlo_descriptor.help_text = ("Creates a settings file. This is also sometimes called a monte carlo descriptor(MCD) file. " 
                                                                               "It can be loaded later or used as an input for headless runs.")
        
        # This grabs the parameter values out of the parameter widgets.
        # It counts on each of the parameter widgets having a .value property.
        def build_param_dict(self):
            result = OrderedDict()
            for (key, w) in self.pframe.param_widgets.items():
                result[key] = w.value
            return result
        
        def run_analysis_separate_thread(self):
         
            param_instance = parameter_management.AnalysisParameters(self.build_param_dict(), current_analysis_class.relevant_parameters)
            new_thread = AnalysisThreadClass(self, current_analysis_class, param_instance)
            self.thread_array.append(new_thread)
            new_thread.done_signal.connect(self.display_window_for_analysis)
            new_thread.start()
            
        def display_window_for_analysis(self, index):
            analysis_instance = analysis_instance_array[index]
            awin = self.swclass.analysis_window_dict[analysis_instance.display_window_name](analysis_instance) 
            awin.show()
            self.awin_list.append(awin)
        
        def run_analysis(self):
            """ 
            This is the method that is called first when the user clicks the Run Analysis button.
            It then calls run_current_analysis_in_main_thread
            Otherwise it creates an AnalysisThreadClass instance.
            """
            print "entering run analysis"
            if current_analysis_name == None:
                show_message("You have to select an analysis first.")
                return
            
            if self.run_in_thread.value:
                self.run_analysis_separate_thread()
            else:
                start_time = time.time()
                param_instance = parameter_management.AnalysisParameters(self.build_param_dict(), current_analysis_class.relevant_parameters)
                analysis_instance = current_analysis_class(param_instance)
                awin = self.swclass.analysis_window_dict[current_analysis_class.display_window_name](analysis_instance) 
                awin.show()
                self.awin_list.append(awin)
                print "it took", time.time() - start_time, "seconds."
        run_analysis.help_text = "Runs the currently selected analysis one time, then shows the result in an analysis window for exploration."
        
        def load_analysis(self, fname = None):
            if fname is None:
                fname = QFileDialog.getOpenFileName()[0]
            f = open(fname, 'r')
            analysis_instance = pickle.load(f) # I changed this to Pickle to see if a memory error goes away
            awin =  self.swclass.analysis_window_dict[analysis_instance.display_window_name](analysis_instance)
            awin.show()
            self.awin_list.append(awin)
            f.close()
        load_analysis.help_text = ("Load a saved (pickled) analysis and opens an analysis window to explore it. "
                                                "This is a little kludgy at present. Since pickle can't deal with ElementTrees, the data_portal has to be"
                                                 " recreated.")

        def open_general(self, fullname = None):
            if fullname is None:
                fullname = QFileDialog.getOpenFileName()[0]
            _, fextension = os.path.splitext(fullname)
            if fextension == ".anl":
                self.load_analysis(fname = fullname)
            elif fextension == ".out":
                self.load_report(fname = fullname)
            else:
                self.load_mcd(fname = fullname)
        
        def load_mcd(self, fname = None):
            if fname is None:
                fname = QFileDialog.getOpenFileName(caption = "Select MCD File")[0]
            f = open(fname, 'r')
            mcd = cPickle.load(f)
            f.close()
            self.analysis_group.click_item(mcd.analysis_name)
            self.iterations.value = mcd.iterations
            mcd.param_instance.set_param_widgets(self.pframe.param_widgets)

        load_mcd.help_text = "Loads  a saved settings/MCD file."
            
        def load_report(self, fname = None):
            if fname is None:
                fname = QFileDialog.getOpenFileName(caption = "Select a Monte Carlo Report File")[0]
            db = shelve.open(fname, protocol = PP)
            mcd = db['mcd']
            db.close()
            awin = qmonte_carlo_window(mcd, self.swclass.analysis_dict , self.swclass.analysis_window_dict, self.awin_list, runit=False, dbfilename=fname)
            awin.show()
            self.awin_list.append(awin)
        load_report.help_text = "Loads a monte carlo report from a file. The monte carlo report is the file produced by a monte carlo run."
            
        def run_monte_carlo(self):
            mcd = self.create_monte_carlo_descriptor(save_file=False)
            report_fname = QFileDialog.getSaveFileName(caption = "Pick a Save File for the Report")[0]
            self.run_mc_analysis(mcd, report_fname)
        run_monte_carlo.help_text = ("Run the selected analysis the number of times specified in the iterations field."
                                                         " The parameter fields can contain a list of numbers separated by spaces."
                                                         " These will be used sequentially in each run. If the number of entries in a list is less than the number of iterations,"
                                                         " then the last number in the list will be used.")
                
        def run_mc_analysis(self, mcd, report_fname):
            awin = qmonte_carlo_window(mcd, self.swclass.analysis_dict , self.swclass.analysis_window_dict, self.awin_list, runit=True, dbfilename=report_fname)
            awin.show()
            self.awin_list.append(awin)
                
        def restore_defaults(self):
            self.pframe.delete_param_widgets()
            self.pframe.recreate_param_widgets()
        restore_defaults.help_text = "Reset all parameters to their defaults for the selected analysis."
        
        def get_file_list(self):
            return [fn for fn in self.xml_list if self._folder_check_vars[fn].get()]
    

