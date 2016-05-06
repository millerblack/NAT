import os
import sys
sys.path.append("%s/../../util" % os.path.abspath(os.path.dirname(__file__)))
from ntcommon import *


class Precondition:
    def __init__(self, parameter_dic):
        self.env_var = ("TESTKIT_EXTRA_PARMETERS_%s_%s_%s" % (parameter_dic["test_suite_name"].replace('-', ''), parameter_dic["binary_branch"], parameter_dic["mode"])).upper()


    def set_precondition(self):
        os.environ[self.env_var] = "-e CordovaLauncher"


    def restore_precondition(self):
        del os.environ[self.env_var]
