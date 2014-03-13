
"""
This module has a single class definition. Instances of this class hold the names of 
modules and classes that are needed in a number of locations.

- analysis_modules is a list of the names of modules that hold analysis classes
- analysis_window_module is the name of the module with window_classes
- The analysis root class and the window root class.

It walks through all of the modules listed in analysis_modules, and finds every class that is a subclass of AnalysisRootClass.
It puts these in analysis_dict and also makes a list of ordered keys:  self.ordered_analysis_keys

It also walks through the analysis_window_module and compiles a list of all of the classes that are subclasses of WindowRootClass.
It puts these in analysis_window_dict.

"""

import inspect

class SharedDictionaryClass():
    def __init__(self, analyses_modules, analysis_window_module, AnalysisRootClass, WindowRootClass):
        analysis_dict = {}
        for module in analyses_modules:
            for (key, the_class) in module.__dict__.items():
                if inspect.isclass(the_class):
                    if issubclass(the_class, AnalysisRootClass):
                        if the_class.runnable_analysis:
                            analysis_dict[key] = the_class
                    
        ordered_analysis_keys = analysis_dict.keys()
        ordered_analysis_keys.sort()
        analysis_window_dict = {}
        for (key, the_class) in analysis_window_module.__dict__.items():
            if inspect.isclass(the_class):
                if issubclass(the_class, WindowRootClass):
                    analysis_window_dict[key] = the_class
        self.analysis_dict = analysis_dict
        self.analysis_window_dict = analysis_window_dict
        self.ordered_analysis_keys = ordered_analysis_keys

        