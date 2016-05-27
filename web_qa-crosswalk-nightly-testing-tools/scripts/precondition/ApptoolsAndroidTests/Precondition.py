import os
import commands
import shutil
import sys
sys.path.append("%s/../../util" % os.path.abspath(os.path.dirname(__file__)))
from ntcommon import *


class Precondition:
    _https_proxy = os.environ["https_proxy"]


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
        unzipped_test_dir = "%s/opt/apptools-android-tests" % unzipped_dir
        cache_path = "%s/tools" % unzipped_test_dir
        binary_name = "crosswalk-%s.zip" %  self.binary_version
        bit = "32"

        if self.device_arch.find("64") != -1:
            binary_name = "crosswalk-%s-64bit.zip" %  self.binary_version
            bit = "64"

        shutil.copy("%s/%s/%s/%s/%s/crosswalk-tools/%s" % (repo_dir, crosswalk_type, test_platform, self.binary_branch, self.binary_version, binary_name), cache_path)
        local_crosswalk_app_tools = "%s/crosswalk-app-tools" % open_source_projects_dir
        save_repo_path = "%s/crosswalk-app-tools" % cache_path

        if os.path.exists(local_crosswalk_app_tools):
            shutil.copytree(local_crosswalk_app_tools, save_repo_path)
        else:
            save_repo_path = "%s/crosswalk-app-tools" % cache_path
            s, o = commands.getstatusoutput("git clone https://github.com/crosswalk-project/crosswalk-app-tools.git %s" % save_repo_path)

        back_up_path = os.getcwd()
        os.chdir(save_repo_path)
        pull_status, pull_output = commands.getstatusoutput("git pull")
        npm_inst_status, npm_inst_output = commands.getstatusoutput("npm install")
        os.chdir(back_up_path)
        os.environ["CROSSWALK_APP_TOOLS_CACHE_DIR"] = cache_path
        env_var_path = os.environ["PATH"]
        os.environ["PATH"] = "%s/src:%s" % (save_repo_path, env_var_path)
        os.environ["https_proxy"] = os.environ["http_proxy"]
        os.environ[self.env_var] = "--testprefix=%s" % unzipped_dir
        arch_file = "%s/arch.txt" % unzipped_test_dir
        os.system("echo %s > %s" % (self.device_arch, arch_file))
        mode_file = "%s/mode.txt" % unzipped_test_dir
        os.system("echo %s > %s" % (self.mode, mode_file))
        version_file = "%s/version.txt" % unzipped_test_dir
        os.system("echo %s %s > %s" % (self.binary_version, bit, version_file))


    def restore_precondition(self):
        os.environ["https_proxy"] = self._https_proxy
        del os.environ[self.env_var]
