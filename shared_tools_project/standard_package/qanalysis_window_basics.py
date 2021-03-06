
from PySide.QtGui import QHBoxLayout, QVBoxLayout, QFont, QDialog, QLineEdit
from PySide.QtGui import QWidget, QSizePolicy, QComboBox, QTableWidgetSelectionRange
from PySide.QtCore import QSize
from PySide.QtGui import QTableWidget, QTableWidgetItem, QColor, QBrush, QLabel, QClipboard, QFileDialog # @UnresolvedImport
from PySide import QtCore
from qnotebook import qNotebook
from montecarlo_package.monte_carlo import MonteCarloDescriptorClass
import numpy
from collections import OrderedDict
import cPickle

inline_images = True
import pylab
from mywidgets import qmy_button, CommandTabWidget, qHotField
from help_tools import helpForWindow
from qnotebook import ColorMapper
from matplotlib_window import MplWindow

analysis_window_dict = {}

# Decorator function used to register window classes in analysis_window_dict
def analysis_window(aw):
    analysis_window_dict[aw.__name__] = aw
    return aw

class QAnalysisWindowBase(QDialog):
    def __init__ (self, lcvsa_dict, parent = None):
        QDialog.__init__(self)
        
        if isinstance(lcvsa_dict, dict):
            self._lcvsa_dict = lcvsa_dict
        else:
            self._lcvsa_dict = {lcvsa_dict.__class__.__name__+ "_1": lcvsa_dict}
        self._lcvsa = self._lcvsa_dict[self._lcvsa_dict.keys()[0]]

        # Get the various color maps from pylab        
        self.color_maps=[m for m in pylab.cm.datad if not m.endswith("_r")]
        self.color_maps += ["AA_traditional_"]
        self.color_maps.sort()

        self.mplwin_list = [] # The list of matplotlib windows
        
        # Create the major frames.
        main_frame = QHBoxLayout()

        self._explorer_windows = []
        leftWidget = QWidget()
        leftWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setLayout(main_frame)
        main_frame.setContentsMargins(5, 5, 5, 5)
        left_frame = QVBoxLayout()
        left_frame.setContentsMargins(1, 1, 1, 1)
        left_frame.setSpacing(5)
        main_frame.addWidget(leftWidget)
        main_frame.setAlignment(leftWidget, QtCore.Qt.AlignTop)
        leftWidget.setLayout(left_frame)
        leftWidget.setMinimumSize(600, 750)
        leftWidget.setMaximumWidth(750)

        
        right_frame = qNotebook() # The right frame holds a qNotebook
        main_frame.addLayout(right_frame)
        self._lframe = left_frame
        self._main_frame = main_frame
        self._rframe = right_frame

        # Put a small frame at the top of the left frame to hold some checkboxes, and a pop list for selecting analyses
        self.top_left_frame = QVBoxLayout()
        left_frame.addLayout(self.top_left_frame)

        # Make the checkboxes
        self.inline = qHotField("Put images in the notebook", bool, False)
        self.top_left_frame.addWidget(self.inline)
        self.show_legends = qHotField("Show legends on charts", bool, True)
        self.top_left_frame.addWidget(self.show_legends)
        self.show_titles = qHotField("Show titles on charts", bool, True)
        self.top_left_frame.addWidget(self.show_titles)
        self.show_tables_in_explorer = qHotField("Show tables in explorer", bool, False)
        self.top_left_frame.addWidget(self.show_tables_in_explorer)

        # Create the popup list that allows the selection of an analysis, for the case in which there are multiple analyses.
        if not isinstance(self._lcvsa, MonteCarloDescriptorClass):
            self.analysis_popup_list = AnalysisSelector(self)
            self.top_left_frame.addWidget(self.analysis_popup_list)

        # create the instance of helpForWindow so we can display help
        self.help_instance = helpForWindow()

        # Make the commandTabWidget that will hold tabs with all of the commands
        self.tabWidget = CommandTabWidget(self.help_instance)
        self._lframe.addWidget(self.tabWidget)
        self.set_up_left_frame() # usually calls make_widgets which adds the commands to the tabs

        # Add the field for executing code.
        self.exec_frame = QHBoxLayout()
        left_frame.addLayout(self.exec_frame)
        qmy_button(self.exec_frame, self.execute_code, "Execute")
        self.code_field = QLineEdit("")
        self.code_field.setMaximumWidth(400)
        self.code_field.returnPressed.connect(self.execute_code)
        self.exec_frame.addWidget(self.code_field)
        # left_frame.addStretch()
        main_frame.setStretch(0,1)
        main_frame.setStretch(1, 2)
        
        if self._lcvsa.saved_notebook_html != None:
            right_frame.append_text(self._lcvsa.saved_notebook_html)
            # text_doc = self._rframe._teditor.document()
            for imageFileName in self._lcvsa.saved_image_data_dict.keys():
                self._rframe.add_image_data_resource(self._lcvsa.saved_image_data_dict[imageFileName], imageFileName)
            right_frame.image_counter = self._lcvsa.saved_image_counter
                # text_doc.addResources(QTextDocument.ImageResource, QUrl(imageFileName), self._lcvsa.saved_notebook_image_dict[imageFileName])
        else:
            self.gprint("\n<b>Base class is " + self._lcvsa.__class__.__name__ + "\n</b>")
            self.display_analysis_parameters()
            
    def execute_code(self):
        the_code = self.code_field.text()
        self.gprint(str(eval(the_code)))

    def set_up_left_frame(self):
        self.make_widgets()
        
    def display_table_from_array(self, the_table, precision=3, header_rows=0, cmap=None, click_handler=None, header_text=None, sort_column=0, sort_order=QtCore.Qt.AscendingOrder):
        # cmap = ColorMapper(max(value_list), min(value_list))
        if self.show_tables_in_explorer.value:
            eWindow = ExplorerWindow(the_table, header_rows, roundit=precision, cmap=cmap, click_handler=click_handler, header_text=header_text, sort_column=sort_column, sort_order=sort_order)
            eWindow.show()
            self._explorer_windows += [eWindow]
        else:
            self._rframe.append_html_table_from_array(the_table, header_rows=header_rows, cmap=cmap, precision = precision)
            
    def display_table_from_dict(self, the_dict, precision = 3, header_rows = 0, cmap = None, click_handler = None, header_text = None):
        # cmap = ColorMapper(max(value_list), min(value_list))
        the_table = self._rframe.convert_structured_dicts_to_array(the_dict)
        self.display_table_from_array(the_table, precision, header_rows, cmap, click_handler, header_text)
    
    def gprint(self, text, format_string = None):
        if format_string == None:
            self._rframe.append_text(text)
        else:
            self._rframe.append_text("<%s>%s</%s>" % (format_string, text, format_string))
            
    def gimageprint(self, fig=None):
        if fig is None:
            fig = pylab.gcf()
        if self.inline.value: # Put the image in the notebook
            newwin = MplWindow(fig) # I have to put it in a window in order for the saving to work
            self._rframe.append_image(fig)
            # The next line frees up the image. If it is not included
            # then if I ever execute pylab.show() later, all of the old images appear.
            pylab.close(fig)

        else:
            newwin = MplWindow(fig)
            self.mplwin_list.append(newwin)
            newwin.show()
            
    def save_analysis(self):
        fname = QFileDialog.getSaveFileName()[0]
        f = open(fname, 'w')
        text_doc = self._rframe._teditor.document()
        self._lcvsa.saved_notebook_html = text_doc.toHtml()
        self._lcvsa.saved_image_data_dict = self._rframe.image_data_dict
        self._lcvsa.saved_image_counter = self._rframe.image_counter
        cPickle.dump(self._lcvsa, f)
        f.close()
    save_analysis.help_text = ("Pickle the entire analysis class instance and save it to a file. You'll be prompted for the file name.\n\n")
        
    def explore_vocabulary(self):
        vocab = self._lcvsa._vocab
        the_table = vocab.vocab_data_table()
        # handler = ExploreClickHandler(self._lcvsa, self._explorer_windows)
        handler = ExploreClickHandler(self._lcvsa, self._explorer_windows)
        self.display_table_from_array(the_table, header_rows=1, click_handler = handler)

    def display_analysis_parameters(self, alt_params = None):
        
        if alt_params == None:
            try:
                self.gprint(self._lcvsa.date.strftime("%d/%m/%y-%H:%M"))
            except AttributeError:
                print ("No date attached to this analysis")
            parameters = self._lcvsa._params._parameters
            # xml_list = self._lcvsa._params._xml_list
        else:
            parameters = alt_params
            # ml_list = None
        
        
        #Create a dict to print as a table:
        psdict = OrderedDict()
        for key in parameters.keys():
            # if key in relevant_params:
            psdict[key] = {}
            psdict[key] = {"_name": key, "value":str(parameters[key])}

        self._rframe.append_html_table_from_dicts(psdict, title = "Parameters", sorted_keys =  None, precision = 999)
        self.gprint ("\n")
        #
        # if xml_list != None:
        #     self.gprint("Data Files")
        #     for fname in xml_list:
        #         self.gprint(fname)
        #     self.gprint ("\n\n")
    display_analysis_parameters.help_text = "Reprint the table of parameters that is printed right after an analysis is run."
                

class AnalysisSelector(QWidget):
    def __init__(self, my_parent, max_size = 200):
        QWidget.__init__(self)
        myframe = QHBoxLayout()
        self.setLayout(myframe)
        self.popup = QComboBox()
        self.popup.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        myframe.addWidget(self.popup)
        myframe.addStretch()
        self.my_parent = my_parent
        self.popup.addItems(self.my_parent._lcvsa_dict.keys())
        self.popup.setFont(QFont('SansSerif', 12))
        self.popup.currentIndexChanged.connect(self.when_modified)
        self.when_modified()
        
    def when_modified(self):
        self.my_parent._lcvsa  = self.my_parent._lcvsa_dict[self.popup.currentText()]
        self.my_parent.gprint("Working with analysis %s" % self.popup.currentText(), "h2")
        
    def hide(self):
        QWidget.hide(self)
        
QINT = 3
QFLOAT = 4
QSTRING = 2
QBOOL = 1
type_dict = {int:QINT, float:QFLOAT, numpy.float64: QFLOAT, str:QSTRING, unicode:QSTRING, bool:QBOOL}
inverse_type = dict((qt, t) for t, qt in type_dict.items())

class ExplorerTable(QTableWidget):
    def __init__(self, data_list, header_rows=0, roundit=None, cmap=None, click_handler=None, resize_columns=True, stretch_last=False, header_text=None, row_height=0, sort_column=0, sort_order=QtCore.Qt.AscendingOrder):
        self._data_list = data_list
        self._nrows = len(self._data_list)
        self._ncols = len(self._data_list[0])
        QTableWidget.__init__(self, self._nrows, self._ncols)
        self.setWordWrap(True) # I think it is already true by default
        if header_rows > 0:
            self.setHorizontalHeaderLabels(self._data_list[0])
            self._data_list = self._data_list[1:]
            self._nrows -= 1

        for r in range(self._nrows):
            for c in range(self._ncols):
                data_item = self._data_list[r][c]
                qtype = self.get_qtype(data_item)
                if (roundit != None) and (qtype == QFLOAT):  # @UndefinedVariable
                    data_item = round(data_item, roundit)
                if (r < header_rows - 1):
                    data_item = "_" + str(data_item) # do this so the header rows are sorted to the top
                # newItem = QTableWidgetItem(str(data_item))
                newItem = QTableWidgetItem(type=qtype)
                if type(data_item) == str:
                    newItem.setText(data_item)
                else:
                    newItem.setData(QtCore.Qt.DisplayRole, data_item)
                if r < header_rows - 1:
                    newItem.setFont(QFont("Helvetica", 12, QFont.Bold))
                else:
                    newItem.setFont(QFont("Helvetica", 12))
                    if (cmap != None) and (type(data_item) == float) and (r >= header_rows):
                        the_color = cmap.rgb_color_from_val(data_item)
                        newBrush = QBrush()
                        newBrush.setColor(QColor(the_color[0], the_color[1], the_color[2]))
                        newBrush.setStyle(QtCore.Qt.SolidPattern)
                        newItem.setBackground(newBrush)
                self.setItem(r, c, newItem)
        if resize_columns:
            self.resizeColumnsToContents()
        self.resizeRowsToContents()
        self.sortItems(0, order=QtCore.Qt.AscendingOrder)
        self.setSortingEnabled(True)
        if row_height != 0:
            vh = self.verticalHeader()
            vh.setDefaultSectionSize(row_height)
        if click_handler != None:
            self._click_handler = click_handler
            self.itemClicked.connect(self.item_click_action)
        if stretch_last:
            hh = self.horizontalHeader()
            hh.setStretchLastSection(True)
        self.roundit = roundit
        self.header_rows = header_rows

    def insert_row(self, row, list_of_data):
        self.insertRow(row)
        for c, data_item in enumerate(list_of_data):
            qtype = self.get_qtype(data_item)
            newItem = QTableWidgetItem(type=qtype)
            if type(data_item) == str:
                newItem.setText(data_item)
            else:
                newItem.setData(QtCore.Qt.DisplayRole, data_item)
            newItem.setFont(QFont("Helvetica", 12))
            self.setItem(row, c, newItem)

    def highlight_row(self, the_row):
        self.highlight_cells(the_row, 0, the_row, self.columnCount() - 1)
        self.scrollToItem(self.item(the_row, 0))

    def highlight_cells(self, top, left, bottom, right):
        self.setRangeSelected(QTableWidgetSelectionRange(0, 0, self.rowCount() - 1, self.columnCount() - 1), False)
        self.setRangeSelected(QTableWidgetSelectionRange(top, left, bottom, right), True)

    def inv_qtype(self,the_qtype):
        return inverse_type[the_qtype]

    def get_qtype(self, data):
        return type_dict[type(data)]

    def recolorold(self):
        cmap = ColorMapper(self.max_val.value, self.min_val.value)
        for r in range(self._nrows):
            for c in range(self._ncols):
                data_item = self._data_list[r][c]
                qtype = self.get_qtype(data_item)
                if (self.roundit != None) and (qtype == QFLOAT):  # @UndefinedVariable
                    data_item = round(data_item, self.roundit)
                # newItem = QTableWidgetItem(str(data_item))
                if (qtype > QSTRING) and (r >= self.header_rows - 1):
                    the_color = cmap.rgb_color_from_val(data_item)
                    newBrush = QBrush()
                    newBrush.setColor(QColor(the_color[0], the_color[1], the_color[2]))
                    newBrush.setStyle(QtCore.Qt.SolidPattern)
                    self.tableWidget.item(r, c).setBackground(newBrush)

    def recolor_cells(self, min_val, max_val):
        cmap = ColorMapper(max_val, min_val)
        the_items = self.get_all_table_items()
        for the_item in the_items:
            the_qtype = the_item.type()
            if the_qtype > QSTRING:
                data_item = (self.inv_qtype(the_qtype)(the_item.text()))
                the_color = cmap.rgb_color_from_val(data_item)
                newBrush = QBrush()
                newBrush.setColor(QColor(the_color[0], the_color[1], the_color[2]))
                newBrush.setStyle(QtCore.Qt.SolidPattern)
                the_item.setBackground(newBrush)

    def convert_explorer_table_to_tab(self, items):
        result_dict = {}
        row_list = []
        for item in items:
            the_row = item.row()
            if not (the_row in result_dict.keys()):
                result_dict[the_row] = ""
                row_list.append(the_row)
            else:
                result_dict[the_row] += "\t"
            result_dict[the_row] = result_dict[the_row] + item.text()
        result_text = ""
        for r in row_list:
            result_text =  result_text + result_dict[r] + "\n"
        return result_text

    def get_all_table_items(self):
        item_list = []
        for the_col in range(self.tableWidget.columnCount()):
            for the_row in range(self.rowCount()):
                the_item = self.item(the_row, the_col)
                if the_item:
                    item_list.append(the_item)
        return item_list

    def explorer_copy(self):
        # seems that selectedItems Goes down columns rather than across rows.
        result_text = self.convert_explorer_table_to_tab(self.selectedItems())
        clipboard = QClipboard()
        clipboard.setText(result_text)

    def explorer_save_as_tab(self):
        result_text = self.convert_explorer_table_to_tab(self.get_all_table_items())
        fname = QFileDialog.getSaveFileName()[0]
        f = open(fname, 'w')
        f.write(result_text)
        f.close()

    def item_click_action(self, the_item):
        self._click_handler.handle_click(the_item)


class ExplorerWindow(QDialog):

    def __init__ (self, data_list, header_rows=0, roundit=None, cmap=None, click_handler=None, resize_columns=True, stretch_last=False, header_text=None, row_height=0, sort_column=0, sort_order=QtCore.Qt.AscendingOrder):
        QDialog.__init__(self)
        self.resize(800, 500)
        self.tableWidget = ExplorerTable(data_list, header_rows, roundit, cmap, click_handler, resize_columns, stretch_last, header_text, row_height, sort_column, sort_order=QtCore.Qt.AscendingOrder)
        main_frame = QVBoxLayout()
        top_frame = QHBoxLayout()
        self.setLayout(main_frame)
        main_frame.addLayout(top_frame)
        qmy_button(top_frame, self.tableWidget.explorer_copy, "Copy Selected")
        qmy_button(top_frame, self.tableWidget.explorer_save_as_tab, "Save to TAB file")
        self.min_val = qHotField("Min Value", float, -10, pos="top")
        self.max_val = qHotField("Max Value", float, 10, pos="top")
        top_frame.addWidget(self.min_val)
        top_frame.addWidget(self.max_val)
        qmy_button(top_frame, self.tableWidget.recolor, "Color Cells")
        if header_text != None:
            top_text = QLabel(header_text)
            top_text.setFont(QFont('SansSerif', 14))
            main_frame.addWidget(top_text)
        main_frame.addWidget(self.tableWidget)

    def recolor(self):
        self.tableWidge.recolor_cells(self.min_val.value, self.max_val.value)

        # self._data_list = data_list
        # self._nrows = len(self._data_list)
        # self._ncols = len(self._data_list[0])
        # tableWidget = QTableWidget(self._nrows, self._ncols, self)
        # tableWidget.setWordWrap(True) # I think it is already true by default
        # if header_rows > 0:
        #     tableWidget.setHorizontalHeaderLabels(self._data_list[0])
        #     self._data_list = self._data_list[1:]
        #     self._nrows -= 1
        #
        # for r in range(self._nrows):
        #     for c in range(self._ncols):
        #         data_item = self._data_list[r][c]
        #         qtype = self.get_qtype(data_item)
        #         if (roundit != None) and (qtype == QFLOAT):  # @UndefinedVariable
        #             data_item = round(data_item, roundit)
        #         if (r < header_rows - 1):
        #             data_item = "_" + str(data_item) # do this so the header rows are sorted to the top
        #         # newItem = QTableWidgetItem(str(data_item))
        #         newItem = QTableWidgetItem(type=qtype)
        #         if type(data_item) == str:
        #             newItem.setText(data_item)
        #         else:
        #             newItem.setData(QtCore.Qt.DisplayRole, data_item)
        #         if r < header_rows - 1:
        #             newItem.setFont(QFont("Helvetica", 12, QFont.Bold))
        #         else:
        #             newItem.setFont(QFont("Helvetica", 12))
        #             if (cmap != None) and (type(data_item) == float) and (r >= header_rows):
        #                 the_color = cmap.rgb_color_from_val(data_item)
        #                 newBrush = QBrush()
        #                 newBrush.setColor(QColor(the_color[0], the_color[1], the_color[2]))
        #                 newBrush.setStyle(QtCore.Qt.SolidPattern)
        #                 newItem.setBackground(newBrush)
        #         tableWidget.setItem(r, c, newItem)
        # if resize_columns:
        #     tableWidget.resizeColumnsToContents()
        # tableWidget.resizeRowsToContents()
        # tableWidget.sortItems(0, order=QtCore.Qt.AscendingOrder)
        # tableWidget.setSortingEnabled(True)
        # if row_height != 0:
        #     vh = tableWidget.verticalHeader()
        #     vh.setDefaultSectionSize(row_height)
        # if click_handler != None:
        #     self._click_handler = click_handler
        #     tableWidget.itemClicked.connect(self.item_click_action)
        # if stretch_last:
        #     hh = tableWidget.horizontalHeader()
        #     hh.setStretchLastSection(True)


def get_item_column_header(item):
    qt_widget = item.tableWidget()
    return qt_widget.horizontalHeaderItem(item.column()).text()

class ExploreClickHandler():
    def __init__(self, lcvsa, ewindows):
        self._lcvsa = lcvsa
        self._ewindows = ewindows

    def handle_click(self, item):
        header_text = get_item_column_header(item)
        if header_text != "Word":
            return
        txt = item.text()
        if type(txt) != str and type(txt) != unicode:
            return
        use_list = self._lcvsa._transcript_set.find_word_uses(txt)
        eWindow = ExplorerWindow(use_list,
                                 header_rows=0,
                                 resize_columns=False,
                                 stretch_last=True,
                                 row_height=50)
        eWindow.show()
        self._ewindows += [eWindow]
