import os
import sys
sys.path.append("%s/../../util" % os.path.abspath(os.path.dirname(__file__)))
from ntcommon import *


class Precondition:
    def __init__(self, parameter_dic):
        self.device_name = parameter_dic["device_name"]
        self.device_id = parameter_dic["device_id"]
        self.binary_version = parameter_dic["binary_version"]
        self.segment = parameter_dic["segment_type"]
        self.test_suite_name = parameter_dic["test_suite_name"]


    def set_precondition(self):
        unzipped_test_dir = "%s/unzip_package/%s_%s/%s/%s/opt/%s" % (middle_tmp_dir, self.device_name, self.device_id, self.binary_version, self.segment, self.test_suite_name)
        generate_test_xml(unzipped_test_dir, self.test_suite_name, unzipped_test_dir)


    def restore_precondition(self):
        pass
