# 
# Tools for managing a set of parameters
# 
# The main class is initialized with a dictionary containing the parameters and their values.
# Optionally an ordered key list can be given that contains a preferred ordering of the parameters for purposes of display.
#
# Parameters can be accessed in a few ways:
#   param_class_instance.pname
#   param_class_instance.get_param("pname")
#   param_class_instance._parameters["pname"]
# 

class AnalysisParameters(object):
    def __init__(self, parameters, parameter_defaults, xml_list = None):
        self._parameters = parameters
        self.parameter_defaults = parameter_defaults
        self._xml_list = xml_list
        
        # Make it possible to also directly address the parameters as attributes
        for key, keyval in self._parameters.items():
            setattr(self, key, keyval)
    
    def set_param_widgets(self, param_widgets, exclude = []):
        for key in self.parameter_names:
            if not (key in exclude):
                param_widgets[key].value = self.get_param(key)
    
    @property
    def parameter_names(self):
        return self._parameters.keys()
    
    def get_param(self, pname):
        return self._parameters[pname]
    
    def set_param(self, pname, value):
        self._parameters[pname] = value
        
    def has_param(self, pname):
        return (pname in self._parameters.keys())
    
