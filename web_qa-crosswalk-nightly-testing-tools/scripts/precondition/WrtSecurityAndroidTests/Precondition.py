import os
import sys
sys.path.append("%s/../../util" % os.path.abspath(os.path.dirname(__file__)))
from ntcommon import *


class Precondition:
    def __init__(self, parameter_dic):
        self.device_name = parameter_dic["device_name"]
        self.device_id = parameter_dic["device_id"]
        self.device_arch = parameter_dic["device_arch"]
        self.binary_branch = parameter_dic["binary_branch"]
        self.binary_version = parameter_dic["binary_version"]
        self.mode = parameter_dic["mode"]
        self.segment = parameter_dic["segment_type"]
        self.env_var = ("TESTKIT_EXTRA_PARMETERS_%s_%s_%s" % (parameter_dic["test_suite_name"].replace('-', ''), self.binary_branch, self.mode)).upper()


    def set_precondition(self):
        unzipped_dir = "%s/unzip_package/%s_%s/%s/%s" % (middle_tmp_dir, self.device_name, self.device_id, self.binary_version, self.segment)
        unzipped_test_dir = "%s/opt/wrt-security-android-tests" % unzipped_dir
        crosswalk_file = "%s/%s/%s/%s/%s/crosswalk-tools/crosswalk-%s.zip" % (repo_dir, crosswalk_type, test_platform, self.binary_branch, self.binary_version, self.binary_version)
        shutil.copy(crosswalk_file, os.environ['CROSSWALK_APP_TOOLS_CACHE_DIR'])
        os.environ[self.env_var] = "--comm androidmobile --testenvs 'XWALK_VERSION=%s' --testprefix %s" % (self.binary_version, unzipped_dir)
        arch_file = "%s/arch.txt" % unzipped_test_dir
        os.system("echo %s > %s" % (self.device_arch, arch_file))
        mode_file = "%s/mode.txt" % unzipped_test_dir
        os.system("echo %s > %s" % (self.mode, mode_file))


    def restore_precondition(self):
        del os.environ[self.env_var]
        crosswalk_file = "%s/crosswalk-%s.zip" % (os.environ['CROSSWALK_APP_TOOLS_CACHE_DIR'], self.binary_version)
        os.remove(crosswalk_file)
