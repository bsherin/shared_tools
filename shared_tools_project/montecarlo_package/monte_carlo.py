import pylab
import shelve, gzip, os
from standard_package.parameter_management import AnalysisParameters

PP = 1 # Pickle protocol to use

def build_reports_dict(the_class):
    the_class.reports_dict = {}
    for name in dir(the_class):
        thing = getattr(the_class, name)
        if hasattr(thing, "isreport"):
            the_class.reports_dict[name] = thing
    the_parent = the_class.__bases__[0]
    if not (the_parent == ()):
        the_class.reports_dict.update(the_parent.reports_dict)
        
def zipify(fname, delete_original = False):
    f_in = open(fname, 'rb')
    f_out = gzip.open(fname+".gz", "wb")
    f_out.writelines(f_in)
    f_out.close()
    f_in.close()
    if delete_original == True:
        os.remove(fname)

class MonteSequence(object):
    def __init__(self, my_list):
        self.my_list = my_list
        self.short_length = len(my_list)
    def __getitem__(self, ind):
        if ind >= self.short_length:
            return self.my_list[-1]
        else:
            return self.my_list[ind]
    def __str__(self, iters = None):
        if iters == None:
            return str(self.my_list)
        else:
            result = [self.__get_item__[i] for i in range(iters)]
            return str(result)

class MonteCarloDescriptorClass(object):
    def __init__(self, analysis_name, param_instance, iterations = 1):
        self.iterations = iterations
        self.analysis_name = analysis_name
        self.report_function_name = param_instance.monte_carlo_report
        self.param_instance = param_instance

        self.saved_notebook_html = None
        # self.xml_list = xml_list
        
        # first create a dictionary in which every parameter is MonteSequence
        params = {}
        for key in param_instance.parameter_names:
            params[key] = param_instance.get_param(key)
            if not (isinstance(params[key], MonteSequence)):
                params[key] = MonteSequence([params[key]])
                
        # Now create a list of AnalysisParameter instances.
        # Each one of these instances will appropriately specify an analysis.
        self.parameters_instance_list= []
        for i in range(self.iterations):
            new_parameters_dict = {}
            for key in params.keys():
                new_parameters_dict[key] = params[key][i]
            self.parameters_instance_list += [AnalysisParameters(new_parameters_dict, param_instance.parameter_defaults)]
        self.report_list = []
        
    def run_me(self, analysis_dict, fname = "reportdb", zipit = False):
        # self.report_list = []
        print "Number of runs: ", len(self.parameters_instance_list)
        # Create the data portal
        # data_portal = data_portals.vaPortal()
        # parameter_management.reset_parameter_defaults(analysis_dict[self.analysis_name].relevant_parameters)
        AnalysisClass = analysis_dict[self.analysis_name]
        i = 1
        db = shelve.open(fname, protocol=PP)
        db['mcd'] = self
        for parameter_instance in self.parameters_instance_list:
            print "starting run: ", i
            analysis_instance = AnalysisClass(parameter_instance) # this used to have data_portal as an argument
            report = analysis_instance.reports_dict[self.report_function_name](analysis_instance)
            report["iter"] = str(i)
            # report["iter"] ={"all": {"all": {all: i }}}
            # self.report_list += [report]
            db[str(i)] = report
            i += 1
        db.close()
        if zipit:
            zipify(fname, delete_original=True)
        return fname
    
    def graph_report_for_keys(self, xkey, ykey):            
        # the_range = range(1, len(self.report_list) + 1)
        pylab.figure(figsize=(12, 5))
        x_values = [entry[xkey] for entry in self.report_list]
        y_values = [entry[ykey] for entry in self.report_list]
        pylab.subplots_adjust(left=.05, bottom=.15, right=.98, top=.95)
        pylab.plot(x_values, y_values, 'bo')
        # pylab.xticks(the_range + [the_range[-1] + 1])
        pylab.xlim(xmin=0, xmax = x_values[-1] + 10)
        pylab.grid(True)
        # pylab.show()
        