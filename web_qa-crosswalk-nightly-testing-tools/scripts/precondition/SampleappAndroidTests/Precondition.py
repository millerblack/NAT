import os
import commands
import shutil
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
        self.env_var = ("TESTKIT_EXTRA_PARMETERS_%s_%s_%s" % (parameter_dic["test_suite_name"].replace('-', ''), parameter_dic["binary_branch"], parameter_dic["mode"])).upper()


    def set_precondition(self):
        unzipped_dir = "%s/unzip_package/%s_%s/%s/%s" % (middle_tmp_dir, self.device_name, self.device_id, self.binary_version, self.segment)
        save_dir = "%s/%s/%s/%s/%s/%s-%s/%s" % (repo_dir, crosswalk_type, test_platform, self.binary_branch, self.binary_version, self.segment, self.mode, self.device_arch)
        #http://otcqa.sh.intel.com/qa-auto/live/Xwalk-testsuites/NewSampleApp/android/beta/18.48.477.13/32bit/Sampleapp_sourcecode.zip
        sourcecode_file = "Sampleapp_sourcecode.zip"

        if not os.path.exists("%s/%s" % (save_dir, sourcecode_file)):
            os.system("wget http://otcqa.sh.intel.com/qa-auto/live/Xwalk-testsuites/NewSampleApp/%s/%s/%s/%s/%s -P %s" % (test_platform, self.binary_branch, self.binary_version, {"arm": "32bit", "arm64": "64bit", "x86": "32bit", "x86_64": "64bit"}[self.device_arch], sourcecode_file, save_dir))

        source_dir = "/tmp/crosswalk-samples"

        if os.path.exists(source_dir):
            os.system("rm -rf %s" % source_dir)

        os.system("unzip %s/%s -d /tmp" % (save_dir, sourcecode_file))
        crosswalk_file = "%s/%s/%s/%s/%s/crosswalk-tools/crosswalk-%s.zip" % (repo_dir, crosswalk_type, test_platform, self.binary_branch, self.binary_version, self.binary_version)
        shutil.copy(crosswalk_file, os.environ['CROSSWALK_APP_TOOLS_CACHE_DIR'])
        os.environ[self.env_var] = "--testenvs 'CHANNEL=%s;XWALK_VERSION=%s' --testprefix=%s" % (self.binary_branch.replace('master', 'canary'), self.binary_version, unzipped_dir)


    def restore_precondition(self):
        del os.environ[self.env_var]
        os.system("rm -rf /tmp/crosswalk-samples")
        crosswalk_file = "%s/crosswalk-%s.zip" % (os.environ['CROSSWALK_APP_TOOLS_CACHE_DIR'], self.binary_version)
        os.remove(crosswalk_file)
