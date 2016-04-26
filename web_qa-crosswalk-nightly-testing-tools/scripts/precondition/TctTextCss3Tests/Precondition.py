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
        self.is_webdriver = parameter_dic["is_webdriver"]
        self.aio_name = parameter_dic["aio_name"]
        self.test_suite_name = parameter_dic["test_suite_name"]


    def set_precondition(self):
        if self.is_webdriver:
            unzipped_dir = "%s/unzip_package/%s_%s/%s/%s" % (middle_tmp_dir, self.device_name, self.device_id, self.binary_version, self.segment)
            data_conf_file = "%s/opt/%s/data.conf" % (unzipped_dir, self.test_suite_name)
            resouces_dir = "%s/opt/%s" % (unzipped_dir, self.test_suite_name)

            if self.aio_name:
                data_conf_file = "%s/opt/%s/data.conf" % (unzipped_dir, self.aio_name)
                resouces_dir = "%s/opt/%s/opt/%s" % (unzipped_dir, self.aio_name, self.test_suite_name)

            #config 'platform' of data.conf
            update_config_file(data_conf_file, "info", "platform", data_conf_platform_dic[self.device_name])

            #prepara resouces onto /opt
            opt_resouces_dir = "/opt/%s" % self.test_suite_name

            if check_exists(opt_resouces_dir):
                shutil.rmtree(opt_resouces_dir)

            shutil.copytree(resouces_dir, opt_resouces_dir)
        else:
            print "No precondition when non-webdriver testing."
            pass


    def restore_precondition(self):
        if self.is_webdriver:
            opt_resouces_dir = "/opt/%s" % self.test_suite_name
            shutil.rmtree(opt_resouces_dir)
        else:
            pass
