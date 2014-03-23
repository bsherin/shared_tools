'''
Created on Nov 27, 2013

@author: bls910
'''
import csv
from standard_package import xmltodict

# Base class for my file loaders
class baseFileLoader():
    def get_headers(self):
        return self.headers
    
    def get_all_data(self):
        return self.data_list

class csvFileLoader(baseFileLoader):
# This loads a csv file into a list of dictionaries. One dictionary is for each row of the data.
# It assumes that the first row contains the headers. It assumes that these headers are unique

    def __init__(self, fn):
        with open(fn, "rU") as csvfile:
            csv_reader = csv.reader(csvfile, dialect='excel')
            self.headers = csv_reader.next()
            self.data_list = []
            for row in csv_reader:
                row_dict = {}
                counter = 0
                for k in self.headers:
                    row_dict[k] = row[counter]
                    counter += 1
                self.data_list.append(row_dict)
                
class xmlFileLoader(baseFileLoader):
# This loads an xml file into a dictionary. 
# It would be best if it extracted the headers. It doesn't do that yet. Also, it's not clear how I should handle nested structure.
    def __init__(self, fn):
        f = open(fn)
        raw_text = f.read()
        f.close()
        self.data_dict = xmltodict.parse(raw_text)
        
        # The next through lines try to extract the data as a list of rows, each of which is represented by a dict
        # It makes some assumptions about what the above lines will produced.
        # The root dict will have just one key, which will itself have one key, for which the item is a list of the rows.
        root_key = self.data_dict.keys()[0]
        row_key = self.data_dict[root_key].keys()[0]
        self.data_list = self.data_dict[root_key][row_key]

