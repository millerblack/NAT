import os
import time
import commands
import threading
import multiprocessing
import sys
import subprocess
import glob
import operator

from util.ntcommon import *
from util.ntreport import *
from util.ntmail import *
import ntpackages


START_TEST_TIME = None
update_device_config_dic = {}
#lock.acquire()
#lock.release()
host_id = get_host_ip()

def is_xwalkdriver_active():
    nt_logger.debug("Call Function: 'is_xwalkdriver_active'")
    output = commands.getoutput("ps x | grep xwalkdriver64_release | grep -v grep")

    return output != ''


def kill_xwalkdriver_process():
    nt_logger.debug("Call Function: 'kill_xwalkdriver_process'")
    process_id = commands.getoutput("ps x | grep xwalkdriver64_release | grep -v grep | awk '{print $1}'")

    if process_id != '':
        os.system("kill -9 %s" % process_id)


def launch_xwalkdriver():
    nt_logger.debug("Call Function: 'launch_xwalkdriver'")
    os.system("nohup %s/xwalkdriver64_release 2>&1 &" % xwalkdriver_path)


def get_test_package(test_suite_name, path_type):
    nt_logger.debug("Call Function: 'get_test_package' with test_suite_name(%s), path_type(%s)" % (test_suite_name, path_type))
    test_package = None
    packages_dic = get_json_dic(packages_save_info_file)
    test_suite_dic = packages_dic.get(test_suite_name, None)

    if test_suite_dic and test_suite_dic.get(path_type, None):
        test_package = "%s/%s/%s" % (repo_dir, path_type, packages_dic[test_suite_name][path_type])

    return test_package


def unzip_test_package(test_package, unzip_to_dir):
    nt_logger.debug("Call Function: 'unzip_test_package' with test_package(%s), unzip_to_dir(%s)" % (test_package, unzip_to_dir))
    create_folder(unzip_to_dir)
    unzip_status, unzip_output = commands.getstatusoutput("unzip %s -d %s" % (test_package, unzip_to_dir))


def uninstall_test_package(test_suite_name, device_name, device_id, unzip_to_dir):
    nt_logger.debug("Call Function: 'uninstall_test_package' with test_suite_name(%s), device_name(%s), device_id(%s), unzip_to_dir(%s)" % (test_suite_name, device_name, device_id, unzip_to_dir))
    inst_py_file = "%s/opt/%s/inst.py" % (unzip_to_dir, test_suite_name)

    if os.path.isfile(inst_py_file):
        uninst_status, uninst_output = commands.getstatusoutput('python %s -s %s -u' % (inst_py_file, device_id))
    else:
        nt_logger.error("No such 'int.py' of '%s', fail to do uninstall" % test_suite_name)


def install_test_package(test_suite_name, test_package, device_name, device_id, unzip_to_dir):
    nt_logger.debug("Call Function: 'install_test_package' with test_suite_name(%s), test_package(%s), device_name(%s), device_id(%s), unzip_to_dir(%s)" % (test_suite_name, test_package, device_name, device_id, unzip_to_dir))
    if test_suite_name not in unneed_install_test_suite_list:
        inst_py_file = "%s/opt/%s/inst.py" % (unzip_to_dir, test_suite_name)
        if os.path.isfile(inst_py_file):
            inst_status, inst_output = commands.getstatusoutput('python %s -s %s' % (inst_py_file, device_id))
            if inst_status != 0:
                nt_logger.error("Error: Fail to install '%s' on '%s(%s)' with [%s]" % (test_package, test_suite_name, device_id, inst_output))
                if inst_output.find("INSTALL_FAILED_INSUFFICIENT_STORAGE") != -1:
                    nt_logger.debug("Reboot '%s(%s)', to fix 'INSTALL_FAILED_INSUFFICIENT_STORAGE'" % (device_name, device_id))
                    os.system("adb -s %s reboot" % device_id)
                    time.sleep(30)
                    inst_status1, inst_output1 = commands.getstatusoutput('python %s -s %s' % (inst_py_file, device_id))
                    if inst_status1 != 0:
                        nt_logger.error("Error: Fail to re-install '%s' on '%s(%s)' with [%s]" % (test_package, device_name, device_id, inst_output1))
                        return False
                    else:
                        return True
                return False
            return True
        else:
            nt_logger.error("No such 'int.py' of '%s', fail to do install" % test_package)
            #TODO:Current some test suits don't have inst.py, ignore it, Or notify the testsuite's owner to update suite.json
            #return False
            return True
    else:
        return True


def is_tinyweb_active_android(device_name, device_id):
    nt_logger.debug("Call Function: 'is_tinyweb_active_android' with device_name(%s), device_id(%s)" % (device_name, device_id))
    output = commands.getoutput("adb -s %s shell ps -x | grep tinyweb" % device_id)
    return output != ''


def ready_docroot_for_tinyweb(device_name, device_id, branch, version, segment, mode, device_arch):
    nt_logger.debug("Call Function: 'ready_docroot_for_tinyweb' with device_name(%s), device_id(%s), branch(%s), version(%s), segment(%s), mode(%s), device_arch(%s)" % (device_name, device_id, branch, version, segment, mode, device_arch))
    docroot_package = None
    path_type = get_map_url_type(branch, version, segment, mode, device_arch, crosswalk_type, test_platform)
    tmp_list = glob.glob("%s/%s/webapi-service-docroot-tests*zip" % (repo_dir, path_type))

    if tmp_list:
        docroot_package = tmp_list[0]
        unzip_to_dir = "%s/unzip_package/%s_%s/%s/%s" % (middle_tmp_dir, device_name, device_id, version, segment)
        unzip_test_package(docroot_package, unzip_to_dir)
        inst_py_file = "%s/webapi-service-docroot-tests/inst.py" % unzip_to_dir
        inst_status, inst_output = commands.getstatusoutput('python %s -s %s' % (inst_py_file, device_id))
        nt_logger.debug("inst_output '%s'" % inst_output)
        return True
    else:
        return False


def stop_tinyweb_windows():
    output =  commands.getoutput("pgrep -x tinyweb")
    if output:
        process_id = int(output)
        os.system("kill -9 %d" % process_id)
    else:
        pass


def launch_tinyweb_windows():
    stop_tinyweb_windows()

    if os.path.exists(tinyweb_docroot_path):
        os.system("rm -rf %s" % tinyweb_docroot_path)

    os.makedirs("%s/packages" % tinyweb_docroot_path)
    #according to packages_save_info.json, prepare docroot resources
    packages_dic = get_json_dic(packages_save_info_file)
    #3333 
    sorted_test_suite_list = sorted(packages_dic.iteritems(), key=operator.itemgetter(0))
    save_path = None

    for test_suite, save_test_suite_dic in sorted_test_suite_list:
        for save_path, package_name in save_test_suite_dic.iteritems():
            package_file = "%s/%s/%s" % (repo_dir, save_path, package_name)
            os.system("unzip %s -d %s/packages" % (package_file, tinyweb_docroot_path))

    os.system("unzip %s/%s/docroot/webapi-service-docroot-tests-%s-1.apk.zip -d %s" % (repo_dir, save_path, save_path.split('/')[-1], middle_tmp_dir))
    os.system("unzip %s/webapi-service-docroot-tests/docroot.zip -d %s" % (middle_tmp_dir, middle_tmp_dir))
    os.system("cp -r %s/docroot/opt %s" % (middle_tmp_dir, tinyweb_docroot_path)) 
    os.system("env LD_LIBRARY_PATH=%(tinyweb_path)s PATH=$PATH:%(tinyweb_path)s tinyweb -ssl_certificate %(tinyweb_path)s/server.pem -document_root %(docroot_path)s -listening_ports 8080,8081,8082,8083,8084,8443s; sleep 3s" % {"tinyweb_path": tinyweb_path, "docroot_path": tinyweb_docroot_path} )


def active_tinyweb_android(device_name, device_id, branch, version, segment, mode, device_arch):
    nt_logger.debug("Call Function: 'active_tinyweb_android' with device_name(%s), device_id(%s), branch(%s), version(%s), segment(%s), mode(%s), device_arch(%s)" % (device_name, device_id, branch, version, segment, mode, device_arch))
    nt_logger.debug("Active tinyweb on [%s(%s)]..." % (device_name, device_id))
    status = ready_docroot_for_tinyweb(device_name, device_id, branch, version, segment, mode, device_arch)
    if status:
        commands.getoutput("adb -s %s shell am start -a android.intent.action.MAIN -n com.intel.tinywebtestservice/.FullscreenActivity" % device_id)
        time.sleep(120)
        return True
    else:
        return False


def kill_testkit_process(device_name, device_id, test_suite_name):
    nt_logger.debug("Call Function: 'kill_testkit_process' with device_name(%s), device_id(%s), test_suite_name(%s)" % (device_name, device_id, test_suite_name))
    output = commands.getoutput("ps x | grep testkit-lite | grep -v grep")
    process_list = output.split('\n')

    for process_info in process_list:
        if process_info.find(device_id) != -1 or process_info.find("testkit-lite-dbus") != -1:
            nt_logger.debug("process_info: %s" % process_info)
            process_id = process_info.lstrip().split(' ')[0]
            os.system("kill -9 %s" % process_id)

    time.sleep(20)


def invoke_testkit(test_suite_name, device_name, device_id, input_file, output_file, timeout, vtest_platform, aio_name, branch, version, segment, mode, device_arch):
    nt_logger.debug("Call Function: 'invoke_testkit' with test_suite_name(%s), device_name(%s), device_id(%s), input_file(%s), output_file(%s), timeout(%s), vtest_platform(%s), aio_name(%s), branch(%s), version(%s), segment(%s), mode(%s), device_arch(%s)" % (test_suite_name, device_name, device_id, input_file, output_file, timeout, vtest_platform, aio_name, branch, version, segment, mode, device_arch))
    nt_logger.debug("[%s] Start to run '%s' on '%s(%s)' by testkit-lite ..." % (time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime()), test_suite_name, device_name, device_id))
    #testkit_parameters are composite of common parmeters and extra parameters
    testkit_cmd = "testkit-lite -f %s -o %s -A --deviceid %s" % (input_file, output_file, device_id)
    parameter_key = ("TESTKIT_EXTRA_PARMETERS_%s_%s_%s" % (test_suite_name.replace('-', ''), branch, mode)).upper()

    if os.environ.get(parameter_key, None):
        testkit_cmd += " " + os.environ[parameter_key]

    if testkit_cmd.find(" --comm ") == -1:
        testkit_cmd += " --comm " + comm_module_dic[vtest_platform]

    if is_webdriver:
        testkit_cmd += " -k webdriver"
        if test_suite_name != "usecase-webapi-xwalk-tests":#For there is 'blankspace' in set name of usecase-webapi-xwalk-tests, and testkit-lite not support it, so here filter it
            set_list = get_set_list(input_file)
            testkit_cmd += " --set %s" % ' '.join(set_list)
        os.chdir(os.path.dirname(input_file))

    if segment.find('cordova') != -1:
        testkit_cmd += " -e CordovaLauncher"

    nt_logger.debug("Run '%s' on %s(%s)" % (testkit_cmd, device_name, device_id))
    test_proc = subprocess.Popen(args=testkit_cmd, shell=True)
    pre_time = time.time()
    tinyweb_flag = aio_name == "webapi-service-tests"

    while True:
        exit_code = test_proc.poll()
        elapsed_time = time.time() - pre_time
        if exit_code == None:
            if vtest_platform == "android":
                if tinyweb_flag:
                    if not is_tinyweb_active_android(device_name, device_id):
                        nt_logger.debug("tinyweb on '%s(%s)' is not active ..." % (device_name, device_id))
                        active_tinyweb_android(device_name, device_id, branch, version, segment, mode, device_arch)
                    else:
                        nt_logger.debug("tinyweb on '%s(%s)' is active ..." % (device_name, device_id))
                if is_webdriver and (not is_xwalkdriver_active()):
                    launch_xwalkdriver()
            if elapsed_time >= timeout:
                nt_logger.error("Test '%s' on '%s(%s)' timeout, kill its test process" % (test_suite_name, device_name, device_id))
                kill_testkit_process(device_name, device_id, test_suite_name)
                break
        else:
            break
        time.sleep(20)

    nt_logger.debug("[%s] End to run '%s' on '%s(%s)' by testkit-lite ..." % (time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime()), test_suite_name, device_name, device_id))


def test_action(test_suite_name, test_suite_info_dic, device_name, device_id, device_arch, binary_branch, binary_version, mode, unzip_to_dir, flag, segment_type, aio_name=None):
    nt_logger.debug("Call Function: 'test_action' with test_suite_name(%s), test_suite_info_dic(%s), device_name(%s), device_id(%s), device_arch(%s), binary_branch(%s), binary_version(%s), mode(%s), unzip_to_dir(%s), flag(%s), segment_type(%s), aio_name(%s)" % (test_suite_name, test_suite_info_dic, device_name, device_id, device_arch, binary_branch, binary_version, mode, unzip_to_dir, flag, segment_type, aio_name))
    all_in_one_name = test_suite_info_dic.get("all_in_one", None)
    precondition_flag = test_suite_info_dic["precondition"]
    timeout = test_suite_info_dic["timeout"] * 60

    input_file = "%s/opt/%s/tests.xml" % (unzip_to_dir, test_suite_name)

    if all_in_one_name:
        input_file = "%s/opt/%s/%s.tests.xml" % (unzip_to_dir, all_in_one_name, test_suite_name)

    save_result_dir = "%s/%s/%s/%s/%s/%s/%s/%s/%s/%s" % (test_result_dir, crosswalk_type, test_platform, segment_type, binary_branch, device_name, mode, binary_version, START_TEST_TIME, flag)
    create_folder(save_result_dir)
    output_file = "%s/result_%s.xml" % (save_result_dir, test_suite_name)
    name_seg_arr = test_suite_name.split('-')
    module_name = ''.join([seg.capitalize() for seg in name_seg_arr])

    if precondition_flag:
        if os.path.exists("%s/precondition/%s" % (scripts_dir, module_name)):
            exec "from precondition.%s.Precondition import Precondition" % module_name
            precondition_parameter_dic = {
                "device_name": device_name,
                "device_id": device_id,
                "device_arch": device_arch,
                "binary_branch": binary_branch,
                "binary_version": binary_version,
                "mode": mode,
                "segment_type": segment_type,
                "test_suite_name": test_suite_name,
                "aio_name": aio_name,
                "is_webdriver": is_webdriver
            }
            pc = Precondition(precondition_parameter_dic)
            pc.set_precondition()
            invoke_testkit(test_suite_name, device_name, device_id, input_file, output_file, timeout, test_platform, aio_name, binary_branch, binary_version, segment_type, mode, device_arch)
            pc.restore_precondition()
        else:
            nt_logger.error("No such 'Precontion.py' script for ['%s'], please add it." % test_suite_name)
    else:
        invoke_testkit(test_suite_name, device_name, device_id, input_file, output_file, timeout, test_platform, aio_name, binary_branch, binary_version, segment_type, mode, device_arch)


def uninstall_runtimelib_android(device_name, device_id):
    nt_logger.debug("Call Function: 'uninstall_runtimelib_android' with device_name(%s), device_id(%s)" % (device_name, device_id))
    os.system("adb -s %s uninstall org.xwalk.core" % device_id)


def preinstall_runtimelib_android(device_name, device_id, branch, version, arch):
    nt_logger.debug("Call Function: 'preinstall_runtimelib_android' with device_name(%s), device_id(%s), branch(%s), version(%s), arch(%s)" % (device_name, device_id, branch, version, arch))
    runtimelib_zip = "%s/%s/%s/%s/%s/crosswalk-tools/%s/crosswalk-apks-%s-%s.zip" % (repo_dir, crosswalk_type, test_platform, branch, version, arch, version, arch)

    if os.path.isfile(runtimelib_zip):
        unzip_dst_dir = "%s/unzip_package/%s_%s/%s" % (middle_tmp_dir, device_name, device_id, version)
        create_folder(unzip_dst_dir)
        os.system("unzip %s -d %s" % (runtimelib_zip, unzip_dst_dir))
        runtimelib_apk = "%s/crosswalk-apks-%s-%s/XWalkRuntimeLib.apk" % (unzip_dst_dir, version, arch)
        if os.path.isfile(runtimelib_apk):
            uninstall_runtimelib_android(device_name, device_id)
            output = commands.getoutput("adb -s %s install %s" % (device_id, runtimelib_apk))
            if output.find("Success") != -1:
                return True
            else:
                nt_logger.error("Error: Fail to intall 'XWalkRuntimeLib.apk' on '%s(%s)' with [%s]" % (device_name, device_id, output))
                if output.find("INSTALL_FAILED_INSUFFICIENT_STORAGE") != -1:
                    nt_logger.debug("Reboot '%s(%s)', to fix 'INSTALL_FAILED_INSUFFICIENT_STORAGE'" % (device_name, device_id))
                    os.system("adb -s %s reboot" % device_id)
                    time.sleep(30)
                    inst_status1, inst_output1 = commands.getstatusoutput("adb -s %s install %s" % (device_id, runtimelib_apk))
                    if inst_status1 != 0:
                        nt_logger.error("Error: Fail to re-install 'XWalkRuntimeLib.apk' on '%s(%s)' with [%s]" % (device_name, device_id, inst_output1))
                        return False
                    else:
                        return True
                return False
        else:
            nt_logger.error("No such 'XWalkRuntimeLib.apk' for '%s(%s)'" % (device_name, device_id))
            return False
    else:
        nt_logger.error("No such 'crosswalk-apks-%s-%s.zip' for '%s(%s)'" % (version, arch, device_name, device_id))
        return False


def upload_onto_wrs(result_dir_path):
    if is_upload_report:
        upload_status = upload(result_dir_path)
        nt_logger.debug("Upload '%s' report to WRS status: [%s]" % (result_dir_path, upload_status))
    else:
        nt_logger.debug("Skip to upload report to WRS")


def test_handle(device_name, device_arch, device_id, target_binary_dic, flag):
    nt_logger.debug("Call Function: 'test_handle' with device_name(%s), device_arch(%s), device_id(%s), target_binary_dic(%s), flag(%s)" % (device_name, device_arch, device_id, target_binary_dic, flag))
    test_list_dic = get_test_list_dic(device_name, flag)
    branch = target_binary_dic["branch"]
    version = target_binary_dic["version"]
    segment_list = target_binary_dic["segment_list"]
    mode = target_binary_dic["mode"]

    if test_platform == "android" and mode == "shared":
        status = preinstall_runtimelib_android(device_name, device_id, branch, version, device_arch)
        if not status:
            return

    bk_http_proxy = None

    if is_webdriver and (not is_xwalkdriver_active()):
        launch_xwalkdriver()
        if os.environ.get("http_proxy", None):
            bk_http_proxy = os.environ["http_proxy"]
            os.environ["http_proxy"] = ""

    if test_platform == "android":
        for segment in segment_list:
            path_type = get_map_url_type(branch, version, segment, mode, device_arch, crosswalk_type, test_platform)
            sorted_test_list = sorted(test_list_dic.iteritems(), key=operator.itemgetter(0))
            for test_suite_name, info_dic in sorted_test_list:
                test_package = get_test_package(test_suite_name, path_type)
                if test_package:
                    unzip_to_dir = "%s/unzip_package/%s_%s/%s/%s" % (middle_tmp_dir, device_name, device_id, version, segment)
                    unzip_test_package(test_package, unzip_to_dir)
                    uninstall_test_package(test_suite_name, device_name, device_id, unzip_to_dir)
                    install_status = install_test_package(test_suite_name, test_package, device_name, device_id, unzip_to_dir)
                    if install_status:
                        if test_suite_name in aio_test_suite_list:
                            aio_name = test_suite_name
                            if test_platform == "android" and test_suite_name == "webapi-service-tests":
                                if not is_tinyweb_active_android(device_name, device_id):
                                    status = active_tinyweb_android(device_name, device_id, branch, version, segment, mode, device_arch)
                                    if not status:
                                        nt_logger.debug("Skip test '%s'" % test_suite_name)
                                        continue
                            sub_sorted_test_list = sorted(info_dic.iteritems(), key=operator.itemgetter(0))
                            for sub_test_suite_name, sub_info_dic in sub_sorted_test_list:
                                test_action(sub_test_suite_name, sub_info_dic, device_name, device_id, device_arch, branch, version, mode, unzip_to_dir, flag, segment, aio_name)
                        else:
                            test_action(test_suite_name, info_dic, device_name, device_id, device_arch, branch, version, mode, unzip_to_dir, flag, segment)
                        uninstall_test_package(test_suite_name, device_name, device_id, unzip_to_dir)
                    else:
                        nt_logger.debug("Skip test '%s'" % test_suite_name)
            result_dir = "%s/%s/%s/%s/%s/%s/%s/%s/%s/%s" % (test_result_dir, crosswalk_type, test_platform, segment, branch, device_name, mode, version, START_TEST_TIME, flag)
            upload_onto_wrs(result_dir)
    elif test_platform == "windows":
        for segment in segment_list:
            result_dir = "%s/%s/%s/%s/%s/%s/%s/%s/%s/%s" % (test_result_dir, crosswalk_type, test_platform, segment, branch, device_name, mode, version, START_TEST_TIME, flag)
            sorted_test_list = sorted(test_list_dic.iteritems(), key=operator.itemgetter(0))
            for test_suite_name, info_dic in sorted_test_list:
                inst_file = "%s/packages/opt/%s/inst.py" % (tinyweb_docroot_path, test_suite_name)
                if os.path.exists(inst_file):
                    print ">>>>>>>>>>>>>>>>>>>>>>>>>>>> Test '%s' on '%s' <<<<<<<<<<<<<<<<<<<<<<<<<<<<<" % (test_suite_name, device_name)
                    kill_stub_status, kill_stub_output = commands.getstatusoutput("curl http://%s:9000/kill_stub" % device_id)
                    time.sleep(3)
                    launch_stub_status, launch_stub_output = commands.getstatusoutput("curl http://%s:9000/launch_stub" % device_id)
                    time.sleep(3)
                    print ">>>1. Uninstall existed '%s' on '%s' firstly ..." % (test_suite_name, device_name)
                    uninst_status, uninst_output = commands.getstatusoutput("python %s -d %s -u" % (inst_file, device_id))
                    print "===>Uninstall existed '%s' on '%s' [%d] [%s]" % (test_suite_name, device_name, uninst_status, uninst_output)
                    if uninst_status == 0:
                        print ">>>2. Install '%s' on '%s' ..." % (test_suite_name, device_name)
                        inst_status, inst_output = commands.getstatusoutput("python %s -d %s -m %s" % (inst_file, device_id, host_id))
                        print "===>Install '%s' on '%s' [%s] [%s]" % (test_suite_name, device_name, inst_status, inst_output)
                        if inst_status == 0:
                            result_file = "%s/result_%s.xml" % (result_dir, test_suite_name)
                            print ">>>3. Run '%s' with testkit-lite on '%s' ..." % (test_suite_name, device_name)
                            input_file = "%s/packages/opt/%s/tests.xml" % (tinyweb_docroot_path, test_suite_name)
                            exe_status, exe_output = commands.getstatusoutput("testkit-lite -f %s -A --comm windowshttp --deviceid %s -o %s" % (input_file, device_id, result_file))
                            print "===>Execute '%s' on '%s' [%s]" % (test_suite_name, device_name, exe_status)
                            print exe_output
                            #kill_stub_status, kill_stub_output = commands.getstatusoutput("curl http://%s:9000/kill_stub" % device_id)
                            #time.sleep(3)
                            launch_stub_status, launch_stub_output = commands.getstatusoutput("curl http://%s:9000/launch_stub" % device_id)
                            time.sleep(3)
                            print ">>>4. Uninstall '%s' on '%s' finally ..." % (test_suite_name, device_name)
                            uninst_status, uninst_output = commands.getstatusoutput("python %s -d %s -u" % (inst_file, device_id))
                            print "===>Uninstall '%s' on '%s' [%d] [%s]" % (test_suite_name, device_name, uninst_status, uninst_output)
                        else:
                            print "####Skip test '%s' on '%s' for [%d: %s]" % (test_suite_name, device_name, inst_status, inst_output)
                    else:
                        print "####Skip test '%s' on '%s' for [%d: %s]" % (test_suite_name, device_name, uninst_status, uninst_output)
                else:
                    print "No such inst.py as '%s'" % inst_file
            stop_tinyweb_windows()
            upload_onto_wrs(result_dir)

    send_stauts = send_mail(result_dir)
    nt_logger.debug("Send mail status: [%s]" % send_stauts)

    if is_webdriver and (not is_xwalkdriver_active()):
        kill_xwalkdriver_process()
        if bk_http_proxy:
            os.environ["http_proxy"] = bk_http_proxy


def run_test(device_name, device_arch, id_list):
    nt_logger.debug("Call Function: 'run_test' with device_name(%s), device_arch(%s), id_list(%s)" % (device_name, device_arch, id_list))
    thread_list = []
    id_list.sort()#sort by alph order
    id_list_len = len(id_list)
    #lock = threading.Lock()

    if id_list_len == 1:
        flag = "all"
        device_id = id_list[0]
        target_binary_dic = update_device_config_dic[device_name].get("target_binary", None)
        if not target_binary_dic:
            assignments_device_info_dic = update_device_config_dic[device_name]["assignments"][device_id]
            target_binary_dic = assignments_device_info_dic.get("target_binary", None)
            if not target_binary_dic:
                nt_logger.error("Please configure resources/device_config.josn follow README.md")
                return
            if assignments_device_info_dic.has_key("error_flag"):
                nt_logger.error("Error happened when preparing packages, teminate test on '%s(%s)'" % (device_name, device_id))
                return
            else:
                if assignments_device_info_dic.has_key("no_update"):
                    nt_logger.debug("No new released version, skip test on '%s(%s)'" % (device_name, device_id))
                    return
        thread = threading.Thread(target=test_handle, args=(device_name, device_arch, device_id, target_binary_dic, flag))
        thread.start()
        thread_list.append(thread)
    elif id_list_len > 1:
        i = 1
        assignments_dic = update_device_config_dic[device_name]["assignments"]
        for device_id in id_list:
            flag = "part%d" % i
            id_info_dic = assignments_dic[device_id]
            if id_info_dic.has_key("error_flag"):
                nt_logger.error("Error happened when preparing packages, teminate test on '%s(%s)'" % (device_name, device_id))
                i += 1
                continue
            else:
                if id_info_dic.has_key("no_update"):
                    nt_logger.debug("No new released version, skip test on '%s(%s)'" % (device_name, device_id))
                    i += 1
                    continue
            target_binary_dic = id_info_dic["target_binary"]
            thread = threading.Thread(target=test_handle, args=(device_name, device_arch, device_id, target_binary_dic, flag))
            thread.start()
            thread_list.append(thread)
            i += 1

    for thread in thread_list:
        thread.join()


def execute():
    nt_logger.debug("Call Function: 'execute'")
    os.system("rm -rf %s" % middle_tmp_dir)

    global START_TEST_TIME
    START_TEST_TIME = time.strftime('%Y%m%d%H%M', time.localtime())

    ntpackages.prepare_packages()

    if not os.path.isfile(update_device_config_file):
        return False

    if not os.path.isfile(packages_save_info_file):
        return False

    if test_platform == "windows":
        launch_tinyweb_windows()

    global update_device_config_dic
    update_device_config_dic = get_json_dic(update_device_config_file)

    process_list = []

    for device_name, device_info_dic in update_device_config_dic.iteritems():
        device_arch = device_info_dic["device_arch"]
        if device_info_dic.has_key("target_binary"):
            if device_info_dic.has_key("error_flag"):
                nt_logger.error("Error happened when preparing packages, teminate test on '%s'" % device_name)
                continue
            else:
                if device_info_dic.has_key("no_update"):
                    nt_logger.debug("No new released version, skip test on '%s'" % device_name)
                    continue
                id_list = device_info_dic["id_list"]
                process = multiprocessing.Process(target=run_test, args=(device_name, device_arch, id_list))
                process.start()
                process_list.append(process)
        elif device_info_dic.has_key("assignments"):
            id_list = device_info_dic["assignments"].keys()
            process = multiprocessing.Process(target=run_test, args=(device_name, device_arch, id_list))
            process.start()
            process_list.append(process)
        else:
            nt_logger.error("Plese check 'resource/device_config.json', it should be configured like 'README.md'")

    for process in process_list:
        process.join()

    os.system("rm -rf %s" % middle_tmp_dir)

    return True


if __name__ == '__main__':
    output = commands.getoutput("ps -ef | grep -c 'nightly-auto-testing.py'")

    if int(output) > 4:
        print "The last test still runs, skip..."
        sys.exit(1)

    status = execute()
    print "Run tests status: [%s]" % status
