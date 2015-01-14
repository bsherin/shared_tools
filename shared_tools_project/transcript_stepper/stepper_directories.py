__author__ = 'bls910'

# This module sets a variety of file system relevant defaults.

import sys
HOME_PROJECTS_DIR = "/Users/bls910/PycharmProjects/"
REMOTE_PROJECTS_DIR = "/sscc/home/b/bls910/repositories/"

if sys.platform != "darwin":
    PROJECTS_DIR = REMOTE_PROJECTS_DIR
else:
    PROJECTS_DIR = HOME_PROJECTS_DIR

CURRENT_PROJECT_DIR = PROJECTS_DIR + "shared_tools_project/transcript_stepper/"
SHARED_TOOLS_DIR = PROJECTS_DIR + "shared_tools/shared_tools_project/"
REMOTE_SERVER = "bls910@seldon.it.northwestern.edu"