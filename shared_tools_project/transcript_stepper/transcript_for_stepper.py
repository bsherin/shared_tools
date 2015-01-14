__author__ = 'bls910'

import xlrd
import csv
import os
import re
import copy


class StepperTranscript(object):
    def __init__(self, filepath):
        self.last_uid = 0.0
        if os.path.splitext(filepath)[1] == ".xls":
            self.committed = self.convert_excel_to_dict(filepath)
        else: # assume it's a tab-delimited file
            self.committed = self.convert_tab_to_dict(filepath)
        self.working = copy.deepcopy(self.committed)
        self.update_sorted_ids()
        self.current_uid = self.sorted_ids[0]

    def update_sorted_ids(self):
        self.sorted_ids = sorted(self.working.keys())

    @staticmethod
    def separate_turns(raw_text):
        return re.findall(r"(\w+?)\t(.*?)[\t\n\r]", raw_text)

    def convert_excel_to_dict(self, filepath, ignorecols=0):
        print filepath
        result = {}
        wb = xlrd.open_workbook(filepath, formatting_info=True)
        sh = wb.sheet_by_name('Sheet1')

        for rownum in xrange(sh.nrows):
            the_row = sh.row_values(rownum)
            the_row[2] = unicode(the_row[2])
            the_row[2] = re.sub(u'\u2019', u"\'", the_row[2])
            the_row[2] = re.sub(u'\u2018', u"\'", the_row[2])
            the_row[2] = re.sub(u'\u2026', u"...", the_row[2])
            the_row[2] = re.sub(u'\u201c', u"\"", the_row[2])
            the_row[2] = re.sub(u'\u201d', u"\"", the_row[2])
            the_row[2] = re.sub(u'\xe4', u" ", the_row[2])
            try:
                if the_row[1][-1] == ":":
                    the_row[1] = the_row[1][:-1]
            except IndexError:
                print "problem at", rownum, the_row

            result[self.last_uid] = {"time": the_row[0],
                                     "speaker": the_row[1],
                                     "utterance": the_row[2]}
            self.last_uid += 1
        return result

    def convert_tab_to_dict(self, filepath):
        print filepath
        result = {}
        with open(filepath, 'rb') as csvfile:
            csvreader = csv.reader(csvfile, delimiter='\t')
            for the_row in csvreader:
                result[self.last_uid] = {"time": the_row[0],
                                        "speaker": the_row[1],
                                        "utterance": the_row[2]}
                self.last_uid += 1
        return result

    @property
    def video_file_name(self):
        for item in self.committed.values():
            if item['speaker'] == 'VideoFile':
                return item["utterance"]
                break
        return None

    def get_transcript_as_array(self):
        result = []
        for uid in self.sorted_ids:
            turn = self.working[uid]
            result.append([uid] + self.turn_as_list(turn))
        return result

    def turn_from_uid(self, uid):
        return self.working[uid]

    def current_turn(self):
        return self.turn_from_uid(self.current_uid)

    def preceding_uid(self, uid):
        return self.sorted_ids[self.sorted_ids.index(uid) - 1]

    def following_uid(self,uid):
        return self.sorted_ids[self.sorted_ids.index(uid) + 1]

    def move_to_position(self, position):
        self.current_uid = self.sorted_ids[int(round(position * len(self.sorted_ids)))]

    def insert_new(self, uid, before_or_after="before"):
        if before_or_after == "before":
            neighbor = self.preceding_uid(uid)
        else:
            neighbor = self.following_uid(uid)
        new_id = (neighbor + uid) / 2.0

        self.working[new_id] = {"time": "",
                               "speaker": "",
                               "utterance": ""}
        self.update_sorted_ids()
        self.current_uid = new_id
        return new_id

    def delete_uid(self, uid):
        if self.current_uid == uid:
            self.go_to_next()
        del self.working[uid]
        self.update_sorted_ids()

    def current_index(self):
        return self.sorted_ids.index(self.current_uid)

    def go_to_index(self, index):
        self.current_uid = self.sorted_ids[index]

    def delete_current(self):
        self.delete_uid(self.current_uid)

    def go_to_next(self):
        if self.current_uid != self.sorted_ids[-1]:
            self.current_uid = self.following_uid(self.current_uid)

    def go_to_previous(self):
        if self.current_uid != self.sorted_ids[0]:
            self.current_uid = self.preceding_uid(self.current_uid)

    def revert_uid(self, uid):
        self.working[uid] = copy.deepcopy(self.committed[uid])

    def revert_current(self):
        self.revert_uid(self.current_uid)

    def commit_uid(self, uid):
        self.committed[uid] = copy.deepcopy(self.working[uid])

    def commit_current(self):
        self.committed[self.current_uid] = copy.deepcopy(self.working[self.current_uid])

    def commit_all(self):
        self.committed = copy.deepcopy(self.working)

    def turn_as_list(self, turn):
        return [turn["time"], turn["speaker"], turn["utterance"]]

    def save_as_csv(self, filename):
        outfile = open(filename, 'wb')
        wr = csv.writer(outfile, delimiter='\t')
        for uid in sorted(self.committed.keys()):
            turn = self.committed[uid]
            wr.writerow(self.turn_as_list(turn))
        outfile.close()
