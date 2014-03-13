from standard_package.qanalysis_window_basics import QAnalysisWindowBase
from PySide.QtGui import QFileDialog # @UnresolvedImport
import shelve
import os

from montecarlo_package.monte_carlo import PP

class qmonte_carlo_window(QAnalysisWindowBase):
    def __init__(self, mcd, analysis_dict, analysis_window_dict, awin_list, runit = True, dbfilename = None):
        if runit:
            self.dbfile = mcd.run_me(analysis_dict, dbfilename)
        else:
            self.dbfile = dbfilename
        self.mcd = mcd
        self.analysis_dict = analysis_dict
        self.analysis_window_dict = analysis_window_dict
        self.awin_list = awin_list
        self.build_instance_name_list()
        self.build_field_name_list()
        # self.load_analysis_window = load_analysis_window
        QAnalysisWindowBase.__init__(self, mcd)
        self.reprint_report_list()
        # self._lframe.reprint_report_list()
        
    def build_field_name_list(self):
        db = shelve.open(self.dbfile, protocol=PP)
        entry = db[str(1)]
        self.field_name_list = entry.keys()
        db.close()

    def build_instance_name_list(self):
        instance_name_set = set([])
        db = shelve.open(self.dbfile, protocol=PP)
        for e in range(len(db.keys()) - 1):
            entry = db[str(e+1)]
            for k in entry.keys():
                try:
                    if entry[k].isrunnable:
                        instance_name_set.add(k)
                except AttributeError:
                    _ = 3
        self.instance_name_list = list(instance_name_set)
        db.close()

    def display_analysis_parameters(self):
        self._lcvsa = self.mcd
        super(qmonte_carlo_window, self).display_analysis_parameters(alt_params = self.mcd.param_instance._parameters)
       
    def set_up_left_frame(self):
        # self._lframe = self.monte_carlo_window_left_frame(main_frame, self)
        self.make_widgets()
                    
    def make_widgets(self):
        iter_list = [str(num + 1) for num in range(self.mcd.iterations)]
        command_list = [
                        [self.display_analysis_parameters, "Display Analysis Parameters", {}],
                        [self.runmcd, "Run or Rerun MCD", {}],
                        [self.reprint_report_list, "Reprint Report List", {}],
                        [self.print_result_table, "Display Report Table", {}],
                        [self.load_instance, "Load Analysis Instance", {"iter_num": iter_list, "instance_name": self.instance_name_list}],
                        [self.load_all_instances, "Load All Instances", {"instance_name": self.instance_name_list}],
                        [self.append_report, "Append Report", {}],
                        [self.append_folder_of_reports, "Append Folder of Reports", {}],
                        [self.print_confusion_matrix, "Display Confusion Matrix" , {"iter_num": iter_list, "field_name": self.field_name_list}]
                        ]
        self.tabWidget.add_command_tab(command_list, "Basic Commands")
                                   

    def print_confusion_matrix(self, iter_num=0, field_name = ""):
        i = iter_num
        db = shelve.open(self.dbfile, protocol=PP)
        for e in range(len(db.keys()) - 1):
            entry = db[str(e+1)]
            if entry["iter"] == i:
                cm = entry[field_name]
                self.gprint(cm.pp())
                db.close()
                return
        db.close()
        
    def print_result_table(self):
        result_table = [self.field_name_list]
        db = shelve.open(self.dbfile, protocol=PP)
        for e in range(len(db.keys()) - 1):
            entry = db[str(e+1)]
            row = []
            for k in self.field_name_list:
                try:
                    val = entry[k]
                    if isinstance(val, (str, int, float, long)):
                        row.append(val)
                    elif hasattr(val, "__tablerep__"):
                        row.append(val.__tablerep__)
                        
                    else:
                        row.append(" ")
                except AttributeError:
                    row.append(" ")
            result_table.append(row)
        self.display_table_from_array(result_table, header_rows = 1)
        db.close()
        
    def load_instance(self, iter_num=1, instance_name = ""):
        i = iter_num
        iname = instance_name
        db = shelve.open(self.dbfile, protocol=PP)
        for e in range(len(db.keys()) - 1):
            entry = db[str(e+1)]
            if entry["iter"] == i:
                analysis_instance = entry[iname]
                window_class = self.analysis_window_dict[entry[iname].display_window_name]
                awin = window_class(analysis_instance)
                awin.show()
                self.awin_list.append(awin)
                db.close()
                return
        db.close()
        
    def load_all_instances(self, instance_name = ""):
        iname = instance_name
        db = shelve.open(self.dbfile, protocol=PP)
        analysis_dict = {}
        for e in range(len(db.keys()) - 1):
            entry = db[str(e+1)]
            analysis_dict[entry[iname].__class__.__name__ + "_" + str(e+1)] = entry[iname]

        window_class = self.analysis_window_dict[entry[iname].display_window_name]
        awin = window_class(analysis_dict)
        awin.show()
        self.awin_list.append(awin)
        db.close()

    def runmcd(self):
        # self.dbfile = self.report_file_name.get()
        self.mcd.run_me(self.analysis_dict, self.dbfile)
        self.reprint_report_list()
        
#        def save_mcd(self):
#            fname = self.file_name.get()
#            # f = open(fname, 'w')
#            f = gzip.open(fname, 'wb')
#            cPickle.dump(self._swin.mcd, f)
#            f.close()
            
    def reprint_report_list(self):
        # self.dbfile = self.report_file_name.get()
        db = shelve.open(self.dbfile, protocol=PP)
        for i in range(len(db.keys()) - 1):
            item = db[str(i+1)]
            self.gprint(str(item))
            # self._rframe.append_html_table_from_dicts(item)
        db.close()
        
    def append_report(self):
        append_report_fname = QFileDialog.getOpenFileName(caption = "Select a Monte Carlo Report File to append")[0]
        self.append_one_report(append_report_fname)
    
    def append_one_report(self, append_report_fname):
        db = shelve.open(self.dbfile, protocol=PP)
        adb = shelve.open(append_report_fname, protocol=PP)
        current_item = len(db.keys())
        for i in range(len(adb.keys()) - 1):
            item = adb[str(i+1)]
            db[str(current_item)] = item
            current_item += 1
        adb.close()
        db.close()
        
    def append_folder_of_reports(self):
        fdirectoryname = QFileDialog.getExistingDirectory()
        all_files = os.listdir(fdirectoryname)
        for f in all_files:
            if f[0] != ".":
                self.append_one_report(fdirectoryname+ "/" + f)
                self.gprint("Appending report" + f)
#        db = shelve.open(self.dbfile)
#        adb = shelve.open(append_report_fname)
#        current_item = len(db.keys())
#        for i in range(len(adb.keys()) - 1):
#            item = adb[str(i+1)]
#            db[str(current_item)] = item
#            current_item += 1
#        adb.close()
#        db.close()
            
    def graph_report(self):
        self.mcd.graph_report_for_keys(self.xkey.get(), self.ykey.get())
        self.gimageprint()
            
#     def print_report_table(self):
#         xkey = self.xkey.get()
#         ykey = self.ykey.get()
#         self.gprint('\n')
#         self.gprint('%s\t%s' % (xkey, ykey))
#         db = shelve.open(self.dbfile, protocol=PP)
#         for i in range(len(db.keys()) - 1):
#             entry = db[str(i+1)]
#             xval = entry[xkey]
#             yval = entry[ykey]
#             if isinstance(xval, float):
#                 xval = round(xval, 2)
#             if isinstance(yval, float):
#                 yval = round(yval, 2)
#             self.gprint("%s\t%s" % (xval, yval))
#         db.close()
#         
    def create_empty_string_array(self, rows, cols):
        table_array = []
        for r in range(rows): #@UnusedVariable
            the_row = []
            for c in range(cols): #@UnusedVariable
                the_row.append("")
            table_array.append(the_row)
        return table_array
    
    def new_print_attribute_report_table(self, arg_dict):
        
        # This version uses the ability of the qnotebook to display a dictionary as a table
        rfname = self.mcd.report_function_name
        if (rfname == "correlation_by_clip_and_attribute_report") or (rfname == "correlation_by_clip_and_instance_report") or (rfname == 'correlation_by_ca_with_kappa_report'):
            topic = arg_dict["topic"]
            self.gprint('\n')
            self.gprint(topic)
            local_dict = {}
            db = shelve.open(self.dbfile, protocol=PP)
#            for key in db.keys():
#                if key != "mcd":
#                    local_dict[key] = db[key][topic]
            skeys = []
            for i in range(len(db.keys()) - 1): 
                local_dict[str(i + 1)] = db[str(i+1)][topic]  
                skeys.append(str(i+1))
            self._rframe.append_html_table_from_dicts(local_dict, sorted_keys = skeys)
            db.close()
        else:
            print "print attribute report table doesn't work for this report"
        
    def print_attribute_report_table(self, arg_dict):
        rfname = self.mcd.report_function_name
        if (rfname == "correlation_by_clip_and_attribute_report") or (rfname == "correlation_by_clip_and_instance_report") or (rfname == 'correlation_by_ca_with_kappa_report'):
            topic = arg_dict["topic"]
            self.gprint('\n')
            self.gprint(topic)
            db = shelve.open(self.dbfile, protocol=PP)
            first_dict = db["1"][topic]
            clip_names = first_dict.keys()
            clip_names.sort()
            clip_names.remove('zall')
            anames = first_dict[clip_names[0]].keys()
            ncols = len(clip_names) * len(anames) * 2 + 2
            nrows = 3 + len(db.keys()) - 1
            table_array = self.create_empty_string_array(nrows, ncols)
            c = 0
            for clip_name in clip_names:
                table_array[0][c] = clip_name
                c = c + len(anames) * 2
            table_array[0][c] = "overall"
            
            c = 0
            for clip_name in clip_names:
                for aname in anames:
                    table_array[1][c] = aname
                    c += 2
            c = 0
            for clip_name in clip_names:
                for aname in anames:
                    table_array[2][c] = "pcorr"
                    table_array[2][c + 1] = "scorr"
                    c += 2
            
            the_row = 3
            for i in range(len(db.keys()) - 1):
                c = 0
                entry = db[str(i+1)]
                the_dict = entry[topic]
                for clip_name in clip_names:
                    for aname in anames:
                        val = the_dict[clip_name][aname]
                        table_array[the_row][c] = str(round(val['pcorr'], 3))
                        table_array[the_row][c + 1] = str(round(val['scorr'], 3))
                        c += 2
                val = the_dict['zall']
                table_array[the_row][c] = str(round(val['all1']['pcorr'], 3))
                table_array[the_row][c + 1] = str(round(val['all2']['scorr'], 3))
                the_row += 1
            self._rframe.append_html_table_from_array(table_array, header_rows = 1)
            db.close()
        else:
            print "print attribute report table doesn't work for this report"
      
    def oldprint_attribute_report_table(self):
        rfname = self.mcd.report_function_name
        if (rfname == "correlation_by_clip_and_attribute_report") or (rfname == "correlation_by_clip_and_instance_report"):
            topic = self.topic.get()
            self.gprint('\n')
            self.gprint(topic)
            db = shelve.open(self.dbfile, protocol=PP)
            first_dict = db["1"][topic]
            clip_names = first_dict.keys()
            clip_names.sort()
            clip_names.remove('all')
            anames = first_dict[clip_names[0]].keys()
            result_string = ""
            for clip_name in clip_names:
                    result_string += clip_name
                    for aname in anames:
                        result_string += '\t\t'
            result_string += 'overall'
            self.gprint(result_string)
            result_string = ""
            for clip_name in clip_names:
                for aname in anames:
                    result_string += aname
                    result_string += '\t\t'
            self.gprint(result_string)
            result_string = ""
            for clip_name in clip_names:
                for aname in anames:
                    result_string += 'pcorr\tscorr\t'
            self.gprint(result_string)
            for i in range(len(db.keys()) - 1):
                entry = db[str(i+1)]
                result_string = ''
                the_dict = entry[topic]
                for clip_name in clip_names:
                    for aname in anames:
                        val = the_dict[clip_name][aname]
                        result_string += str(round(val[0], 3)) + '\t'
                        result_string += str(round(val[1], 3)) + '\t'
                val = the_dict['all']
                result_string += str(round(val[0], 3)) + '\t'
                result_string += str(round(val[1], 3)) + '\t'
                self.gprint(result_string)
            db.close()
        else:
            print "print attribute report table doesn't work for this report"
                            
                    
            




            