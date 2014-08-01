
from mywidgets  import qmy_button, qButtonWithArgumentsClass
from PySide.QtCore import QBuffer, QUrl  # @UnresolvedImport
from PySide.QtGui import QVBoxLayout, QTextEdit, QHBoxLayout, QImageReader, QTextImageFormat  # @UnresolvedImport
from PySide.QtGui import QTextDocument, QTextCursor, QTextFrameFormat, QTextTableFormat, QFileDialog, QImageWriter  # @UnresolvedImport
from matplotlib import pyplot
import StringIO, os

img_format = "png" # This is the only format that seems to work

image_width = 750
import numpy
from collections import OrderedDict

class ColorMapper():
    def __init__ (self, top_val, bottom_val):
        self.top_val = top_val
        self.bottom_val = bottom_val
        self.val_range = top_val - bottom_val
        self.mid_point = self.bottom_val + self.val_range / 2.0
        
    def rgb_to_hex(self, rgb):
        return '#%02x%02x%02x' % rgb
    
    def rgb_color_from_val(self, val):
        if val >= self.top_val:
            return (0, 255, 0)
        elif val <= self.bottom_val:
            return (255, 0, 0)
        else:
            if val >= self.mid_point:
                fract = 2 * (val - self.mid_point) / self.val_range
                green_part = 255
                red_part = int(255 * (1 - fract))
                blue_part = red_part
            else:
                fract = 2 * (self.mid_point - val) / self.val_range
                red_part = 255
                green_part = int(255 * (1 - fract))
                blue_part = green_part
            return (red_part, green_part, blue_part)
            
    def color_from_val(self, val):
        return self.rgb_to_hex(self.rgb_color_from_val(val))

class qNotebook(QVBoxLayout):
    def __init__(self):
        QVBoxLayout.__init__(self)
        self._teditor = QTextEdit()
        self._teditor.setMinimumWidth(500)
        self._teditor.setStyleSheet("font: 12pt \"Courier\";")
        button_layout = QHBoxLayout()
        self.addLayout(button_layout)
        self.clear_but = qmy_button(button_layout, self.clear_all, "clear")
        self.copy_but = qmy_button(button_layout, self._teditor.copy, "copy")
        qmy_button(button_layout, self._teditor.selectAll, "select all")
        qmy_button(button_layout, self._teditor.undo, "undo")
        qmy_button(button_layout, self._teditor.redo, "redo")
        search_button = qButtonWithArgumentsClass("search", self.search_for_text, {"search_text": ""})
        button_layout.addWidget(search_button)
        qmy_button(button_layout, self.save_as_html, "save notebook")
        
        self.addWidget(self._teditor)
        self._teditor.document().setUndoRedoEnabled(True)
        self.image_counter = 0
        self.image_dict = {}
        self.image_data_dict = {}
        
    def append_text(self, text):
        self._teditor.append(str(text))
        
    def search_for_text(self, search_text = " "):
        self._teditor.find(search_text)
        
    def clear_all(self):
        self._teditor.clear()
        self.image_dict = {}
        self.image_counter = 0
#        newdoc = QTextDocument()
#        self._teditor.setDocument(newdoc)
        
    def append_image(self, fig=None):
        #This assumes that an image is there waiting to be saved from matplotlib
        self.imgdata = StringIO.StringIO()
        if fig is None:
            pyplot.savefig(self.imgdata, transparent = False, format = img_format)
        else:
            fig.savefig(self.imgdata, transparent = False, format = img_format)
        self.abuffer = QBuffer()
        self.abuffer.open(QBuffer.ReadWrite)
        self.abuffer.write(self.imgdata.getvalue())
        self.abuffer.close()
        
        self.abuffer.open(QBuffer.ReadOnly)
        iReader = QImageReader(self.abuffer, img_format )
        the_image = iReader.read()
        # the_image = the_image0.scaledToWidth(figure_width)
        
        # save the image in a file
        imageFileName = "image" + str(self.image_counter) + "." + img_format
        self.image_data_dict[imageFileName] = self.imgdata
        
        self.image_counter +=1
        imageFormat = QTextImageFormat()
        imageFormat.setName(imageFileName)
        imageFormat.setWidth(image_width)
        self.image_dict[imageFileName] = the_image
        
        #insert the image in the text document
        text_doc = self._teditor.document()
        text_doc.addResource(QTextDocument.ImageResource, QUrl(imageFileName), the_image)
        cursor = self._teditor.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertImage(imageFormat)
        
    def add_image_data_resource(self, imgdata, imageFileName):
        
        self.abuffer = QBuffer()
        self.abuffer.open(QBuffer.ReadWrite)
        self.abuffer.write(imgdata.getvalue())
        self.abuffer.close()
        
        self.abuffer.open(QBuffer.ReadOnly)
        iReader = QImageReader(self.abuffer, img_format )
        the_image = iReader.read()
        # the_image = the_image0.scaledToWidth(figure_width)
        
        # save the image in a file
        # imageFileName = "image" + str(self.image_counter) + "." + img_format
        self.image_data_dict[imageFileName] = imgdata
        
        # self.image_counter +=1
        imageFormat = QTextImageFormat()
        imageFormat.setName(imageFileName)
        imageFormat.setWidth(image_width)
        self.image_dict[imageFileName] = the_image
        
        #insert the image in the text document
        text_doc = self._teditor.document()
        text_doc.addResource(QTextDocument.ImageResource, QUrl(imageFileName), the_image)
        
    
    def append_html_table_from_array(self, a, header_rows=0, precision = 3, caption = None, cmap = None):
        nrows = len(a)
        ncols = len(a[0])
        result_string = "<table border=\"1\" cellspacing=\"0\" cellpadding=\"2\">\n"
        if caption != None:
            result_string += "<caption>%s</caption>\n"  % caption
        r = 0
        while r < header_rows:
            result_string += "<tr>"
            for c in range(ncols):
                if a[r][c] != "":
                    # count following blank columns
                    count = 1
                    while ((c+count) < len(a[r])) and (a[r][c+count] == "") :
                        count += 1
                    val = a[r][c]
                    if (type(val) == numpy.float64) or (type(val) == float):  # @UndefinedVariable
                        if precision != 999:
                            val = round(val, precision)
                    if count > 1:
                        result_string +="<th colspan=%s>%s</th>"  % (count, val)
                    else:
                        result_string += "<th>%s</th>"  % val
            result_string +="</tr>\n"
            r += 1
        while r < nrows:
            result_string += "<tr>"
            for c in range(ncols):
                val = a[r][c]
                if (cmap == None):
                    fcolor = "#ffffff"
                elif (type(val) == int) or (type(val) == float) or (type(val) == numpy.float64):  # @UndefinedVariable
                    fcolor = cmap.color_from_val(val)
                else:
                    fcolor = "#ffffff"
      
                if (val != "") or (c == 0):
                    if (type(val) == numpy.float64) or (type(val) == float): # @UndefinedVariable
                        if precision != 999:
                            val = round(val, precision)
                    count = 1
                    while ((c+count) < len(a[r])) and (a[r][c+count] == "") :
                        count += 1
                    if count > 1:
                        result_string +="<td colspan=%s bgcolor=%s>%s</td>"  % (count, fcolor, val)
                    else:
                        result_string += "<td bgcolor=%s>%s</td>" % (fcolor, val)
            result_string +="</tr>\n"
            r += 1
        result_string += "</table>\n"
        self.append_text(result_string)
        
    def create_empty_string_array(self, rows, cols):
        table_array = []
        for r in range(rows): #@UnusedVariable
            the_row = []
            for c in range(cols): #@UnusedVariable
                the_row.append("")
            table_array.append(the_row)
        return table_array
    
    def recurse_on_dict_headers(self, sdict, r, c, sorted_headers = None):
        if ((type(sdict) != dict) and (type(sdict) != OrderedDict)):
            return c + 1
        else:
            if sorted_headers != None:
                sheaders = sorted_headers
            else:
                sheaders = sorted(sdict.keys())
            for k in sheaders:
                self.table_array[r][c] = k
                c = self.recurse_on_dict_headers(sdict[k], r + 1, c)
            return c
        
    def recurse_to_find_size(self, sdict, r, c):
        
        if ((type(sdict) != dict) and (type(sdict) != OrderedDict)):
            return r, c + 1
        else:
            rbiggest = r
            for k in sorted(sdict.keys()):
                rnew, c = self.recurse_to_find_size(sdict[k], r + 1, c)
                if rnew > rbiggest:
                    rbiggest = rnew
            return rbiggest, c
                
    def recurse_on_dict(self, sdict, r, c, sorted_headers = None):
        if ((type(sdict) != dict) and (type(sdict) != OrderedDict)):
            self.table_array[r][c] = sdict
            return c + 1
        else:
            if sorted_headers != None:
                sheaders = sorted_headers
            else:
                sheaders = sorted(sdict.keys())
            for k in sheaders:
                c = self.recurse_on_dict(sdict[k], r, c)
            return c
    
    def convert_structured_dicts_to_array(self, sdict, sorted_keys = None, sorted_headers = None):
        header_levels, ncols = self.recurse_to_find_size(sdict[sdict.keys()[0]], 0, 0)
        nrows = header_levels + len(sdict.keys())
        self.table_array = self.create_empty_string_array(nrows, ncols)
        self.recurse_on_dict_headers(sdict[sdict.keys()[0]], 0, 0, sorted_headers)
        if sorted_keys != None:
            key_list = sorted_keys
        else:
            key_list = sdict.keys()
        r = header_levels
        for entry in key_list:
            c = 0
            self.table_array[r][0] = entry
            self.recurse_on_dict(sdict[entry], r, c, sorted_headers = sorted_headers)
            r += 1
        return self.table_array
            
    def append_html_table_from_dicts(self, sdict, header_rows = 1, title = None, sorted_keys = None, precision = 3, cmap = None, sorted_headers = None):
        the_array = self.convert_structured_dicts_to_array(sdict, sorted_keys, sorted_headers = sorted_headers)
        self.append_html_table_from_array(the_array, header_rows, caption = title, precision = precision, cmap = cmap)
    
    def append_table(self, rows, cols, border_style = QTextFrameFormat.BorderStyle_Solid):
        tformat = QTextTableFormat()
        tformat.setBorderStyle(border_style)
        cursor= self._teditor.textCursor()
        cursor.movePosition(QTextCursor.End)
        table = cursor.insertTable(rows, cols, tformat)
        return table
    
    def fill_table_cell(self, row, col, table, text):
        cptr = table.cellAt(row, col).firstCursorPosition()
        cptr.insertText(text)
        
    def save_as_html(self):
        fname = QFileDialog.getSaveFileName()[0]
        fdirectoryname = os.path.dirname(fname)
        # fdirectoryname = QFileDialog.getExistingDirectory()
        # print fdirectoryname
        # fname = fdirectoryname + "/report.html"
        text_doc = self._teditor.document()
        f = open(fname, 'w')
        f.write(text_doc.toHtml())
        f.close()
        for imageFileName in self.image_dict.keys():
            full_image_path = fdirectoryname + "/" + imageFileName
            iWriter = QImageWriter(full_image_path, img_format)
            iWriter.write(self.image_dict[imageFileName])
        
        