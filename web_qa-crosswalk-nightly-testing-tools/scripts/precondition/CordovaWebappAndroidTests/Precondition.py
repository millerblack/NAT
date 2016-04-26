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
        helloworld_file = "%s/helloworld.apk" % unzipped_dir
        apk_resource_dir = "/tmp/cordova-sampleapp"
        package_release_url = " %s/%s/%s/%s/%s/%s-%s/%s" % (package_release_server_url, crosswalk_type, test_platform, self.binary_branch, self.binary_version, self.segment, self.mode, self.device_arch)
        save_dir =  "%s/%s/%s/%s/%s/%s-%s/%s" % (repo_dir, crosswalk_type, test_platform, self.binary_branch, self.binary_version, self.segment, self.mode, self.device_arch)

        if not os.path.exists(apk_resource_dir):
            os.mkdir(apk_resource_dir)

        if not os.path.exists(helloworld_file):
            sampleapp_file_name = "%s_sampleapp_%s.zip" % (self.segment, self.device_arch)
            if not os.path.exists("%s/%s" % (save_dir, sampleapp_file_name )):
                os.system("wget %s/%s -P %s" % (package_release_url, sampleapp_file_name, save_dir))
            os.system("unzip -o %s/%s -d %s" % (save_dir, sampleapp_file_name, unzipped_dir))
            if not os.path.exists(helloworld_file):
                if not os.path.exists("%s/helloworld.apk" % save_dir):
                    os.system("wget %s/helloworld.apk -P %s" % (package_release_url, save_dir))
                    if os.path.exists("%s/helloworld.apk" % save_dir):
                        shutil.copy("%s/helloworld.apk" % save_dir, apk_resource_dir)
                    else:
                        print "No such '%s/helloworld.apk'" % package_release_url
                else:
                    shutil.copy("%s/helloworld.apk" % save_dir, apk_resource_dir)
            else:
                shutil.copy(helloworld_file, apk_resource_dir)
        else:
            shutil.copy(helloworld_file, apk_resource_dir)

        crosswalk_tools_dir = "%s/%s/%s/%s/%s/crosswalk-tools" % (repo_dir, crosswalk_type, test_platform, self.binary_branch, self.binary_version)
        mvn_cmd = "mvn install:install-file -DgroupId=org.xwalk -DartifactId=%s -Dversion=%s -Dpackaging=aar -Dfile=%s/%s -DgeneratePom=true"
        artifactid = "xwalk_core_library"
        aar_file_name = "crosswalk-%s.aar" % self.binary_version

        if self.mode == "shared":
            artifactid = "xwalk_shared_library"
            aar_file_name = "crosswalk-shared-%s.aar" % self.binary_version
            mvn_cmd = mvn_cmd % (artifactid, self.binary_branch, crosswalk_tools_dir, aar_file_name)
        elif self.mode == "embedded":
            if self.device_arch == "arm64":
                aar_file_name = "crosswalk-%s-64bit.aar" % self.binary_version
                mvn_cmd = mvn_cmd % (artifactid, self.binary_branch, crosswalk_tools_dir, aar_file_name)
                mvn_cmd += " -Dclassifier=64bit"
            else:
                mvn_cmd = mvn_cmd % (artifactid, self.binary_branch, crosswalk_tools_dir, aar_file_name)

        os.system(mvn_cmd)
        os.environ[self.env_var] = "--testprefix=%s" % unzipped_dir
        unzipped_test_dir = "%s/opt/cordova-webapp-android-tests" % unzipped_dir
        arch_file = "%s/arch.txt" % unzipped_test_dir
        os.system("echo %s > %s" % (self.device_arch, arch_file))
        mode_file = "%s/mode.txt" % unzipped_test_dir
        os.system("echo %s > %s" % (self.mode, mode_file))


    def restore_precondition(self):
        del os.environ[self.env_var]
        os.system("rm -rf /tmp/cordova-sampleapp")
