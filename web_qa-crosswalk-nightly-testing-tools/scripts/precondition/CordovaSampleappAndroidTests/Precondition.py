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
        privatenotes_file = "%s/privateNotes.apk" % unzipped_dir
        spacedodge_file = "%s/spacedodge.apk" % unzipped_dir
        apk_resource_dir = "/tmp/cordova-sampleapp"

        if not os.path.exists(apk_resource_dir):
            os.mkdir(apk_resource_dir)

        package_release_url = "%s/%s/%s/%s/%s/%s-%s/%s" % (package_release_server_url, crosswalk_type, test_platform, self.binary_branch, self.binary_version, self.segment, self.mode, self.device_arch)
        save_dir = "%s/%s/%s/%s/%s/%s-%s/%s" % (repo_dir, crosswalk_type, test_platform, self.binary_branch, self.binary_version, self.segment, self.mode, self.device_arch)
        if not os.path.exists(privatenotes_file):
            sampleapp_file_name = "%s_sampleapp_%s.zip" % (self.segment, self.device_arch)
            if not os.path.exists("%s/%s" % (save_dir, sampleapp_file_name )):
                os.system("wget %s/%s -P %s" % (package_release_url, sampleapp_file_name, save_dir))
            os.system("unzip -o %s/%s -d %s" % (save_dir, sampleapp_file_name, unzipped_dir))
            if not os.path.exists(privatenotes_file):
                if not os.path.exists("%s/privateNotes.apk" % save_dir):
                    os.system("wget %s/privateNotes.apk -P %s" % (package_release_url, save_dir))
                    if os.path.exists("%s/privateNotes.apk" % save_dir):
                        shutil.copy("%s/privateNotes.apk" % save_dir, apk_resource_dir)
                    else:
                        print "No such '%s/privateNotes.apk'" % package_release_url
                else:
                    shutil.copy("%s/privateNotes.apk" % save_dir, apk_resource_dir)
            else:
                shutil.copy(privatenotes_file, apk_resource_dir)
            if not os.path.exists(spacedodge_file):
                if not os.path.exists("%s/spacedodge.apk" % save_dir):
                    os.system("wget %s/spacedodge.apk -P %s" % (package_release_url, save_dir))
                    if os.path.exists("%s/spacedodge.apk" % save_dir):
                        shutil.copy("%s/spacedodge.apk" % save_dir, apk_resource_dir)
                    else:
                        print "No such '%s/spacedodge.apk'" % package_release_url
                else:
                    shutil.copy("%s/spacedodge.apk" % save_dir, apk_resource_dir)
            else:
                shutil.copy(spacedodge_file, apk_resource_dir)
        else:
            shutil.copy(privatenotes_file, apk_resource_dir)
            if not os.path.exists(spacedodge_file):
                if not os.path.exists("%s/spacedodge.apk" % save_dir):
                    os.system("wget %s/spacedodge.apk -P %s" % (package_release_url, save_dir))
                    if os.path.exists("%s/spacedodge.apk" % save_dir):
                        shutil.copy("%s/spacedodge.apk" % save_dir, apk_resource_dir)
                    else:
                        print "No such '%s/spacedodge.apk'" % package_release_url
                else:
                    shutil.copy("%s/spacedodge.apk" % save_dir, apk_resource_dir)
            else:
                shutil.copy(spacedodge_file, apk_resource_dir)

        circ_file = "%s/CIRC.apk" % save_dir

        if not os.path.exists(circ_file):
            os.system("wget %s/CIRC.apk -P %s" % (package_release_url, save_dir))

        if not os.path.exists(circ_file):
            print "No such '%s/CIRC.apk'" % package_release_url
        else:
            shutil.copy(circ_file, apk_resource_dir)

        eh_file = "%s/Eh.apk" % save_dir

        if not os.path.exists(eh_file):
            os.system("wget %s/Eh.apk -P %s" % (package_release_url, save_dir))

        if not os.path.exists(eh_file):
            print "No such '%s/Eh.apk'" % package_release_url
        else:
            shutil.copy(eh_file, apk_resource_dir)

        #http://otcqa.sh.intel.com/qa-auto/live/Xwalk-testsuites/NewSampleApp/android/beta/18.48.477.13/32bit/Sampleapp_sourcecode.zip
        sourcecode_file = "Sampleapp_sourcecode.zip"

        if not os.path.exists("%s/%s" % (save_dir, sourcecode_file)):
            os.system("wget http://otcqa.sh.intel.com/qa-auto/live/Xwalk-testsuites/NewSampleApp/%s/%s/%s/%s/%s -P %s" % (test_platform, self.binary_branch, self.binary_version, {"arm": "32bit", "arm64": "64bit"}[self.device_arch], sourcecode_file, save_dir))

        source_dir = "/tmp/crosswalk-demos"

        if os.path.exists(source_dir):
            os.system("rm -rf %s" % source_dir)

        os.system("rm -rf /tmp/crosswalk-samples")
        os.system("unzip %s/%s -d /tmp" % (save_dir, sourcecode_file))
        os.system("mv /tmp/crosswalk-samples %s" % source_dir)

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
        unzipped_test_dir = "%s/opt/cordova-sampleapp-android-tests" % unzipped_dir
        arch_file = "%s/arch.txt" % unzipped_test_dir
        os.system("echo %s > %s" % (self.device_arch, arch_file))
        mode_file = "%s/mode.txt" % unzipped_test_dir
        os.system("echo %s > %s" % (self.mode, mode_file))


    def restore_precondition(self):
        del os.environ[self.env_var]
        os.system("rm -rf /tmp/cordova-sampleapp")
        os.system("rm -rf /tmp/crosswalk-demos")
