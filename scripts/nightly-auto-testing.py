import commands
#import copy
#import datetime
import json
import glob
import os
import subprocess
import sys
import time
import threading
import ConfigParser
import utility.common as common
import utility.dorerun as dorerun
import ReadyPackagesLocal
import utility.QAMail as QAMail
import utility.QAReport as QAReport


logger = utility.logger
settings_dic = utility.settings_dic
project_path = settings_dic["project_path"]
pack_mode = settings_dic["pack_mode"]
current_ww = settings_dic["current_ww"]
xwalkdriver = settings_dic["xwalkdriver_path"]
test_scope_list = settings_dic["test_scope_list"]
config_dic = utility.config_dic
mail_templet_dic = utility.mail_templet_dic
manual_pack_result_list = utility.manual_pack_result_list
key_pack_ok = manual_pack_result_list[0]
key_pack_error = manual_pack_result_list[1]
key_no_update = manual_pack_result_list[2]
pack_results_dic = None
#start_test_time = None
arch_dic = {"x86": "IA", "arm": "ARM"}
opposite_device_arch_dic = {"x86": "arm", "arm": "x86"}
no_update_mail_templet = mail_templet_dic["templet001"]
mail_templet = mail_templet_dic["templet002"]
install_output_macro = "pkg: /data/local/tmp/%s.apk\n"
START_TEST_TIME = None
rerun_line = settings_dic["rerun_line"]
auto_pack_packages = settings_dic["auto_pack_packages"]
webdriver_mode = settings_dic['webdriver_mode']
testsuites_dic = utility.testsuites_dic

def send_mail(mail_content, target_type, device_arch, device_name, timestamp, target_version = None):
    #For example: result_dir likes 'test-result/canary_android_x86/zte_v975/201406172200_8.36.157.0'
    result_dir = "%s/test-result/%s_android_%s/%s/%s" % (project_path, target_type, device_arch, device_name, timestamp)

    if target_version:
        result_dir = "%s_%s" % (result_dir, target_version)
    else:
        os.makedirs(result_dir)

    file_handle = open("%s/report_summary.txt" % result_dir, "w")
    file_handle.write(mail_content)
    file_handle.close()

    QAMail.send(device_name, result_dir)


def restart_xwalkdriver(test_name, device_name):
    logger.debug("For \'%s\' on \'%s\' Restart xwalk driveer process ..." % (test_name, device_name))
    xwalk_status = commands.getoutput("ps x | grep xwalkdriver64")
    field = xwalk_status.split()
    process_xkid = field[0]
    process = field[4]
    if process.find("xwalkdriver64") > 0:
        #os.kill(process_xkid,9)
        os.system("kill -9 %s" % process_xkid)
        logger.debug("Kill xwalk driver ...")
        os.system("nohup %s/xwalkdriver64_release 2>&1 &" % xwalkdriver)
        logger.debug("Restart xwalk driver ...")
    else:
        os.system("nohup %s/xwalkdriver64_release 2>&1 &" % xwalkdriver)
        logger.debug("Start xwalk driver ...")


def kill_testkit_lite_process(device_name, test_name):
    logger.debug("Test \'%s\' on \'%s\' timeout, kill testkit-lite process ..." % (test_name, device_name))
    output = commands.getoutput("ps x | grep testkit-lite")
    process_list = output.split('\n')
    for process_info in process_list:
        if process_info.find(device_name) != -1:
            logger.debug("process_info: %s" % process_info)
            process_id = process_info.lstrip().split(' ')[0]
            logger.debug("kill %s" % process_id)
            os.system("kill %s" % process_id)
    time.sleep(60)


def analyze_result(result_dir, analyze_xml_dir):
    os.system("bash analyze_results.sh %s %s %s" % (result_dir, analyze_xml_dir, webdriver_mode))


def generate_report_summary(result_dir, target_type, target_version, device_name, android_version, report_link_list):
    crosswalk_info = "Image Location\n-----------------------\nCrosswalk for Android: %s (%s/%s/%s/crosswalk-tools/crosswalk-%s.zip)" % (target_version, settings_dic["pack_server"], target_type.replace('canary', 'master'), target_version, target_version)
    device_info_title = "\n\nTest Device & Operating System\n-----------------------\n"
    device_info = "%s - Android Image version: %s\n" % (device_name.replace("_", " "), android_version)

    details_info = ''
    details_info_list = []
    url = "%s/%s/%s" % (settings_dic["pack_server"], settings_dic["target_branch"], target_version)
    commit_id = common.get_commit_id(url)

    test_env_infos_dic = settings_dic["test_env_infos"]
    for key, value in test_env_infos_dic.iteritems():
        if key == "Commit ID":
            value = commit_id
        env_item = '%s: %s' % (key, value)
        details_info_list.append(env_item)

    details_info = '\n'.join(details_info_list)

    summary_info = crosswalk_info + device_info_title + device_info + '\n' + details_info

    #for scope_name in test_scope_list:
    #    analyzed_result_file_handle = open("%s/%s/analyzed_result.txt" % (result_dir, scope_name))
    #    if not summary_info:
    #        summary_info = analyzed_result_file_handle.read()
    #    else:
    #        summary_title = "\nSummary %s\n-----------------------\n" % {"cordova": "Cordova", "webview": "EmbeddingAPI"}[scope_name]
    #        summary_info = summary_info + summary_title + analyzed_result_file_handle.read()
    #    analyzed_result_file_handle.close()

    if settings_dic["upload_report"]:
        report_info = "\n\nReport links\n-----------------------\n%s\n" % '\n'.join(report_link_list)
        #summary_info = summary_info + report_info
        upload_log_dir = "%s/upload_log/%s/%s_%s" % (project_path, device_name, target_version, START_TEST_TIME)
        exception_cases_list = []
        index = 1
        log_arr =  glob.glob("%s/*" % upload_log_dir)
        for log_file in log_arr:
            with open(log_file) as f:
                log_dic = json.load(f)
                exception_cases_dic = log_dic['exception_case']
                if exception_cases_dic:
                    for k, v in exception_cases_dic.iteritems():
                        exception_cases_list.append("[%d] %s" % (index, v))
                        index += 1
        upload_log_info = "\n\nError infos\n-----------------------\n%s\n" % '\n'.join(exception_cases_list)
        summary_info = summary_info + report_info + upload_log_info

    summary_info =  summary_info + "\n\nThanks,\nCrosswalk QA team"
    #mail_content = mail_templet % (crosswalk_info, device_info_title, device_info, summary_info)
    report_summary_file_handle = open("%s/report_summary.txt" % result_dir, "w")
    report_summary_file_handle.write(summary_info)
    report_summary_file_handle.close()


def install_runtimelib(target_type, device_arch, device_id, target_version, device_name):
    logger.debug("Install XWalkRuntimeLib on '%s'." % device_name)
    os.system("adb -s %s uninstall org.xwalk.core" % device_id)

    crosswalk_apks_file = "%s/repo/wrt/android/%s/%s/%s/crosswalk-apks-%s-%s.zip" % (project_path, target_type, target_version, device_arch, target_version, device_arch)

    if not os.path.isfile(crosswalk_apks_file):
        logger.error("No such file '%s'" % crosswalk_apks_file)
        return

    unzip_dir = "%s/test-env/%s" % (project_path, device_name)
    if not os.path.exists(unzip_dir):
        os.makedirs(unzip_dir)

    os.system("unzip %s -d %s" % (crosswalk_apks_file, unzip_dir))
    lib_file = "%s/crosswalk-apks-%s-%s/XWalkRuntimeLib.apk" % (unzip_dir, target_version, device_arch)

    if not os.path.isfile(lib_file):
        logger.error("No such file '%s'" % lib_file)
        return

    os.system("adb -s %s install %s" % (device_id, lib_file))


def deploy_service_envs(device_name, scope_name, target_type, target_version, device_id, device_arch, var_ww):
    if os.path.exists("%s/test-env/%s/%s/webapi-service-docroot-tests" % (project_path, device_name, scope_name)):
        return

    if auto_pack_packages:
        docroot_file = commands.getoutput("ls %s/repo/docroot/%s/%s/%s/webapi-service-docroot-tests*zip" % (project_path, var_ww, scope_name, device_arch))
    else:
        #repo/tests/android/canary/13.42.319.0/WW13/testsuites-embedded/x86
        if scope_name == "cordova":
            tmp_dir = testsuites_dic[scope_name]
        else:
            tmp_dir = testsuites_dic[scope_name][pack_mode]
        docroot_file = commands.getoutput("ls %s/repo/tests/android/%s/%s/%s/%s/%s/webapi-service-docroot-tests*zip" % (project_path, target_type, target_version, var_ww, tmp_dir, device_arch))

    if docroot_file.find('No such file or directory') != -1:
        logger.error("Fail to pack 'webapi-service-docroot-tests' %s package " % device_arch)
        return

    unzip_dir = "%s/test-env/%s/%s" % (project_path, device_name, scope_name)

    if not os.path.exists(unzip_dir):
        os.makedirs(unzip_dir)
    os.system("unzip %s -d %s" % (docroot_file, unzip_dir))
    os.system('python %s/webapi-service-docroot-tests/inst.py -s %s' % (unzip_dir, device_id))#TODO:optimize check install status


def clean_service_envs(device_name, device_id):
    pass
    #os.system('python %s/test-env/%s/webapi-service-docroot-tests/inst.py -s %s -u' % (project_path, device_name, device_id))
    #stop tinyweb


def active_tinyweb(device_name, device_id):
    tinyweb_process_info = commands.getoutput("adb -s %s shell ps | grep tinywebtestservice" % device_id)

    if not tinyweb_process_info:
        logger.debug("Launch tinyweb on \'%s\'" % device_name)
        output_info = commands.getoutput("adb -s %s shell am start -a android.intent.action.MAIN -n com.intel.tinywebtestservice/.FullscreenActivity" % device_id)
        logger.debug("active_tinyweb start tinyweb: %s" % output_info)
        #TODO:check output_info wether start successfully
        time.sleep(300)
    elif len(tinyweb_process_info.split('\r\n')) != 2:
        logger.debug("Tinyweb is not active.Relaunch tinywebi on \'%s\'." % device_name)
        output_info = commands.getoutput("adb -s %s shell am start -a android.intent.action.MAIN -n com.intel.tinywebtestservice/.FullscreenActivity" % device_id)
        logger.debug("active_tinyweb start tinyweb: %s" % output_info)
        #TODO:check output_info wether start successfully

        time.sleep(300)


def unzip_install_package(target_type, device_arch, device_id, target_version, var_ww, device_name, scope_name, test_category, test_name, rerun):
    logger.debug("Install '%s' on '%s'" % (test_name, device_name))
    if auto_pack_packages:
        test_package_file = commands.getoutput("ls %s/repo/tests/android/%s/%s/%s/%s/%s/%s/%s*zip" % (project_path, target_type, target_version, var_ww, scope_name, device_arch, test_category, test_name))
    else:
        tmp_dir = testsuites_dic[scope_name][pack_mode]
        test_package_file = commands.getoutput("ls %s/repo/tests/android/%s/%s/%s/%s/%s/%s*zip" % (project_path, target_type, target_version, var_ww, tmp_dir, device_arch, test_name))

    if test_package_file.find('No such file or directory') != -1:
        logger.error("No such '%s' %s package" % (test_name, device_arch))
        return False

    unzip_dir = "%s/test-env/%s/%s/%s" % (project_path, device_name, scope_name, test_category)
    if rerun:
        unzip_dir = "%s/test-env/%s/rerun/%s/%s" % (project_path, device_name, scope_name, test_category)

    if not os.path.exists(unzip_dir):
        os.makedirs(unzip_dir)

    #for BDD case
    os.system("unzip %s -d %s" % (test_package_file, unzip_dir))
    return_value, exit_arch_txt = commands.getstatusoutput('ls %s/opt/%s/arch.txt' % (unzip_dir, test_name))
    if return_value == 0:
       os.system('echo %s > %s/opt/%s/arch.txt' % (device_arch, unzip_dir, test_name))
    return_value, exit_opt_dir = commands.getstatusoutput('ls %s/opt/%s/opt' % (unzip_dir, test_name))
    if return_value == 0:
        os.system('cp -a %s/opt/%s/opt/* /opt/.' % (unzip_dir, test_name))
    #if test_name in ["tct-backgrounds-css3-tests", "tct-colors-css3-tests", "tct-fonts-css3-tests", "tct-svg-html5-tests", "tct-text-css3-tests"]:
    if test_name in ["webapi-noneservice-tests", "webapi-service-tests"]:
        os.system('cp %s/opt/%s/data.conf .' % (unzip_dir, test_name))
        return_value, data_conf_path = commands.getstatusoutput('ls data.conf')
        if return_value == 0:
            devices_name_dic = utility.devices_name_dic
            cof = ConfigParser.ConfigParser()
	    cof.read(data_conf_path)
	    cof.set("info", "platform", "%s" % devices_name_dic[device_name])
            cof.write(open(data_conf_path, "w"))
            os.system("cp %s . " % data_conf_path)

    #For none inst.py in "wrt-manifest-android-tests", "wrt-packertool-android-tests"
    if test_name in ["wrt-manifest-android-tests", "wrt-packertool-android-tests"]:
        return True

    #Uninstall existing old app
    os.system('python %s/opt/%s/inst.py -s %s -u' % (unzip_dir, test_name, device_id))

    #Install new app
    install_output = commands.getoutput('python %s/opt/%s/inst.py -s %s' % (unzip_dir, test_name, device_id))
    logger.debug("Install '%s' on '%s' output: \"%s\"" % (test_name, device_name, install_output))

    #Install package precondition
    if test_category == "WebAPI":
        apk_name = test_name.replace('-', '_')
        if scope_name == "webview":
            apk_name = "embeddingapi"

        install_status_info = install_output.split(install_output_macro % apk_name)

        if scope_name == "webview":
            pass
        else:
            if not install_status_info[1].startswith('Success'):
                logger.error("Fail to install \'%s\' on \'%s\'" % (test_name, device_name))
                return False

    #elif test_category.find("BDD") != -1 and webdriver_mode == 1: 
    #    print "9999999999999999999999999999999999999"
    #    if test_name in ["tct-backgrounds-css3-tests", "tct-colors-css3-tests", "tct-fonts-css3-tests", "tct-svg-html5-tests", "tct-text-css3-tests"]:
    #        print test_name
    #        return_value, data_conf_path = commands.getstatusoutput('ls %s/opt/%s/data.conf' % (unzip_dir, test_name))
    #        print data_conf_path
    #        if return_value == 0:
    #            devices_name_dic = {"Google_Nexus_4": "arm-nexus4", "Google_Nexus_7": "arm-nexus7", "ASUS_MeMO_Pad_8_K011": "x86-memo", "Toshiba_Excite_Go_AT7-C8": "x86-toshiba", "ZTE_Geek_V975":"x86-zte"}
    #            cof = ConfigParser.ConfigParser()
    #            cof.read(data_conf_path)
    #            cof.set("info", "platform", "%s" % devices_name_dic[device_name])
    #            cof.write(open(data_conf_path, "w"))
    #            print "88888888888888888888888888888888"
    
    elif test_category == "WRT":
        #No infos show install stauts
        pass
        #if install_output.find("successfully") == -1:
        #    logger.error("Fail to install \'%s\' on \'%s\'" % (test_name, device_name))
        #    return False

    elif test_category == "SampleApp":
        install_sampleapp = commands.getoutput('python /tmp/Sampleapp_binary/inst.py -s %s' % device_id)
        logger.debug("Install SampleApp on '%s' output: \"%s\"" % (device_name, install_sampleapp))

    elif test_category == "AppTools":
        crosswalk_apks_file = "%s/repo/wrt/android/%s/%s/crosswalk-%s.zip" % (project_path, target_type, target_version, target_version)
        os.system("cp -r %s %s/opt/apptools-android-tests/tools/" % (crosswalk_apks_file, unzip_dir))
        os.system("cp -a /home/qawt/crosswalk-app-tools %s/opt/apptools-android-tests/tools/" % (unzip_dir))
    
    elif test_category == "Cordova":
        cordova_sampleapp_package = commands.getoutput("ls %s/repo/tests/android/%s/%s/%s/%s/%s/cordova*_sampleapp_%s.zip" % (project_path, target_type, target_version, var_ww, tmp_dir, device_arch, device_arch))
        os.system("unzip %s -d -o /tmp/cordova-sampleapp/" % cordova_sampleapp_package)
        crosswalk_arr_file = "%s/repo/wrt/android/%s/%s/crosswalk-%s.arr" % (project_path, target_type, target_version, target_version)
        os.system("mvn install:install-file -DgroupId=org.xwalk -DartifactId=xwalk_core_library -Dversion=%s -Dpackaging=aar -Dfile=%s -DgeneratePom=true" % (target_version, crosswalk_arr_file))

        if test_name == "cordova-sampleapp-android-tests":
            os.system('adb install /tmp/cordova-sampleapp/gallery.apk')

    return True


def uninstall_package(device_name, scope_name, test_category, test_name, device_id, rerun):
    if rerun:
        os.system('python %s/test-env/%s/rerun/%s/%s/opt/%s/inst.py -s %s -u' % (project_path, device_name, scope_name, test_category, test_name, device_id))
        if test_category == "SampleApp":
            os.system('python /tmp/Sampleapp_binary/inst.py -s %s -u' % (device_id))
        if test_name == "cordova-sampleapp-android-tests":
            os.system('adb uninstall com.example.gallery')
    else:
        os.system('python %s/test-env/%s/%s/%s/opt/%s/inst.py -s %s -u' % (project_path, device_name, scope_name, test_category, test_name, device_id))
        if test_category == "SampleApp":
            os.system('python /tmp/Sampleapp_binary/inst.py -s %s -u' % (device_id))
        if test_name == "cordova-sampleapp-android-tests":
            os.system('adb uninstall com.example.gallery')
    #check wether unistall successfully


def get_execute_cmd(execute_cmd_template, input_file, result_file, device_id, scope_name):
    #testkit-lite -f MACRO_INPUT_XML -A --comm localhost --testenvs 'DEVICE_ID=MACRO_DEVICE_ID' -o MACRO_OUTPUT_XML
    actual_execute_cmd = execute_cmd_template.replace('MACRO_INPUT_XML', input_file).replace('MACRO_DEVICE_ID', device_id).replace('MACRO_OUTPUT_XML', result_file)

    #input_file /somepath/test-env/devicename/analyze-xml/WRT/wrt-some-tests.tests.xml
    #prefix /somepath/test-env/WRT/wrt-some-tests
    #for prefix_suit in ['WebAPI','WRT','UseCase','SampleApp','Cordova','AppTools','Stability']:
    prefix_suit = input_file.split('/')[-2] 
    #if input_file.find(prefix_suit) != -1:
    device_name = input_file.split('/')[-4]
    test_name = input_file.split('/')[-1].split('.')[0]
    prefix = "%s/test-env/%s/%s/%s" % (project_path, device_name, scope_name, prefix_suit)
    actual_execute_cmd = actual_execute_cmd.replace('MACRO_PREFIX', prefix)

    if test_name in ["wrt-manifest-android-tests", "wrt-packertool-android-tests"]:
    #result_dir = "%s/test-result/%s_android_%s/%s/%s_%s/%s/%s" % (project_path, target_type, device_arch, device_name, target_version, START_TEST_TIME, scope_name, test_category
    #The following 3 codes are not valid if rerun "wrt-manifest-android-tests", "wrt-packertool-android-tests", for when rerun, result_file doesn't have target_version
        target_type = result_file.split('test-result/')[1].split('/')[0].split('_')[0]
        device_arch = result_file.split('test-result/')[1].split('/')[0].split('_')[2]
        target_version = result_file.split('test-result/')[1].split('/')[2].split('_')[0]
        if test_name == "wrt-manifest-android-tests":
            apk_dir = "%s/repo/tests/android/%s/%s/%s/testsuites-embedded/%s/apks-manifest" % (project_path, target_type, target_version, current_ww, device_arch)
        else:
            apk_dir = "%s/repo/tests/android/%s/%s/%s/testsuites-embedded/%s/apks-packertool" % (project_path, target_type, target_version, current_ww, device_arch)

        actual_execute_cmd = actual_execute_cmd.replace('MACRO_APK_DIR', apk_dir)

    if test_name in ["sampleapp-android-tests"]:
        target_version = result_file.split('test-result/')[1].split('/')[2].split('_')[0]
        actual_execute_cmd = actual_execute_cmd.replace('MACRO_CROSSWALK', target_version)

    dic = {"apk": "XWalkLauncher", "cordova": "CordovaLauncher", "webview": "XWalkLauncher"}
    actual_execute_cmd = actual_execute_cmd.replace('MACRO_LAUNCHER', dic[scope_name])

    if webdriver_mode == 1:
        actual_execute_cmd = "%s -k webdriver" % actual_execute_cmd

    set_list = common.get_set_list(input_file)
    if set_list:
        actual_execute_cmd = actual_execute_cmd + " --set " + ' '.join(set_list)

    logger.debug("Execute CMD: %s" % actual_execute_cmd)
    return actual_execute_cmd


def test_handle(device_name, scope_name, target_type, target_version, device_id, device_arch, test_category, test_name, test_info_dic, extra = None, rerun = None):
    print "===================Begin to test [%s] ========================" % test_name
    bk_http_proxy = os.environ["http_proxy"]
    if webdriver_mode == 1:
        restart_xwalkdriver(test_name, device_name)
        os.environ["http_proxy"] = '' #precondition for webdriver test

    result_dir = "%s/test-result/%s_android_%s/%s/%s_%s/%s/%s" % (project_path, target_type, device_arch, device_name, target_version, START_TEST_TIME, scope_name, test_category)
    if rerun:
        result_dir = "%s/test-result/%s_android_%s/%s/rerun/%s/%s" % (project_path, target_type, device_arch, device_name, scope_name, test_category)

    analyze_xml_dir = "%s/test-env/%s/analyze_xml/%s" % (project_path, device_name, test_category)
    if scope_name == "webview":
        analyze_xml_dir = "%s/test-env/%s/%s/analyze_xml/%s" % (project_path, device_name, scope_name, test_category)

    if not os.path.exists(analyze_xml_dir):
        os.makedirs(analyze_xml_dir)

    if not rerun:
        if test_category == "Cordova" and scope_name == "apk":
            if webdriver_mode == 1:
                os.environ["http_proxy"] = bk_http_proxy
            return
        if test_category == "WebAPI":
            if test_name in ["embedding-api-android-tests", "embedding-asyncapi-android-tests"]:
                tests_unzip_dir = "%s/test-env/%s/%s/%s/opt/%s" % (project_path, device_name, scope_name, test_category, test_name)
                common.generate_tests_xml(tests_unzip_dir, test_name, analyze_xml_dir)
            else:
                aio_test = extra
                print aio_test

                tests_unzip_dir = "%s/test-env/%s/%s/%s/opt/%s" % (project_path, device_name, scope_name, test_category, aio_test)
                if os.path.isfile("%s/%s.tests.xml" % (tests_unzip_dir, test_name)):
                    if not os.path.isfile("%s/%s.tests.xml" % (analyze_xml_dir, test_name)):
                        os.system("cp %s/%s.tests.xml %s" % (tests_unzip_dir, test_name, analyze_xml_dir))
                #elif aio_test == "usecase-webapi-xwalk-tests":
                #    if not os.path.isfile("%s/%s.tests.xml" % (analyze_xml_dir, test_name)):
                #        os.system("cp %s/tests.xml %s/%s.tests.xml" % (tests_unzip_dir, test_name, analyze_xml_dir))
                else:
                    if webdriver_mode == 1:
                        os.environ["http_proxy"] = bk_http_proxy
                    return
        else:
            tests_unzip_dir = "%s/test-env/%s/%s/%s/opt/%s" % (project_path, device_name, scope_name, test_category, test_name)

            if not os.path.isfile("%s/%s.tests.xml" % (analyze_xml_dir, test_name)):
                if test_name in ["usecase-webapi-xwalk-tests", "usecase-wrt-android-tests"]:
                    os.system("cp %s/tests.auto.xml %s/%s.tests.xml" % (tests_unzip_dir, analyze_xml_dir, test_name))
                else:
                    os.system("cp %s/tests.xml %s/%s.tests.xml" % (tests_unzip_dir, analyze_xml_dir, test_name))

    if not os.path.exists(result_dir):
        os.makedirs(result_dir)

    timeout = test_info_dic["timeout"] * 60
    execute_cmd_template = test_info_dic["execute_cmd"]

    #if test_name == "embedding-api-android-tests":
    #    tests_xml_file = test_xml_list
    #else:
    tests_xml_file = "%s/%s.tests.xml" % (analyze_xml_dir, test_name)

    result_file = "%s/result_%s.xml" % (result_dir, test_name)
    execute_cmd = get_execute_cmd(execute_cmd_template, tests_xml_file, result_file, device_id, scope_name)

    logger.info("[%s] Start to run %s '%s' on '%s'" % (time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime()), scope_name, test_name, device_name))
    test_proc = subprocess.Popen(args=execute_cmd, shell=True)
    pre_time = time.time()
    while True:
        exit_code = test_proc.poll()
        elapsed_time = time.time() - pre_time

        if exit_code == None:
            if elapsed_time >= timeout:
                kill_testkit_lite_process(device_name, test_name)
                break
        else:
            break
        time.sleep(20)

    logger.info("[%s] End to run sub_test: %s \'%s\' on \'%s\'" % (time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime()), scope_name, test_name, device_name))

    #Here do anaylze whether this test suite need rerun
    if not rerun:
        #Condition 1: test timeout
        if not os.path.isfile(result_file):
            rerun_dir = "../rerun/%s/%s/%s" % (START_TEST_TIME, device_name, scope_name)

            if not os.path.exists(rerun_dir):
                os.makedirs(rerun_dir)
            tests_txt_file = "%s/tests.txt" % rerun_dir
            if os.path.isfile(tests_txt_file):
                file_handle = open(tests_txt_file, "a")
            else:
                file_handle = open(tests_txt_file, "w")
            write_content = "%s\n" % test_name
            file_handle.write(write_content)
            file_handle.close()
        else:
            block_rate = dorerun.get_block_rate(tests_xml_file, result_file, webdriver_mode)
            #Condition 2: many blocks
            if block_rate >= rerun_line:
                logger.debug(">>>>>>>>>>>>>>>>>>>>RERUN>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                rerun_time = test_info_dic["rerun_time"]
                print "%s %s rerun_time: %d" % (device_name, test_name, rerun_time)
                if rerun_time > 0:
                    #backup first test result file
                    backup_dir = "%s/test-result/%s_android_%s/%s/first_run/%s/%s" % (project_path, target_type, device_arch, device_name, scope_name, test_category)
                    if not os.path.exists(backup_dir):
                        os.makedirs(backup_dir)
                    os.system("cp %s %s" % (result_file, backup_dir))

                    rerun_dir = "../rerun/%s/%s/%s" % (START_TEST_TIME, device_name, scope_name)
                    if not os.path.exists(rerun_dir):
                        os.makedirs(rerun_dir)
                    tests_txt_file = "%s/tests.txt" % rerun_dir
                    if os.path.isfile(tests_txt_file):
                        file_handle = open(tests_txt_file, "a")
                    else:
                        file_handle = open(tests_txt_file, "w")

                    write_content = "%s\n" % test_name
                    file_handle.write(write_content)
                    file_handle.close()

    if webdriver_mode == 1:
        os.environ["http_proxy"] = bk_http_proxy


def run_tests(device_name, is_manual = False, rerun = None):
    device_detail_dic = config_dic[device_name]
    if auto_pack_packages:
        target_type = device_detail_dic["target_type"]
    else:
        target_type = settings_dic['target_branch'].replace("master", "canary")

    device_id = device_detail_dic["device_id"]
    device_arch = device_detail_dic["device_arch"]
    android_version = device_detail_dic["android_version"]
    target_version = None
    var_ww = current_ww

    if is_manual:
        target_version = device_detail_dic["specify_version"]
        tests_dir = "%s/repo/tests/android/%s/%s" % (project_path, target_type, target_version)
        var_ww = os.listdir(tests_dir)[0]
    else:
        target_version = pack_results_dic[key_pack_ok][target_type][0]

    #get tests list
    tests_list_file = "../resources/%s/tests_list.json" % device_name

    for scope_name in test_scope_list:
        if rerun:
            tests_list_file = "../rerun/%s/%s/%s/tests_list.json" % (START_TEST_TIME, device_name, scope_name)
            if not os.path.isfile(tests_list_file):
                continue

        with open(tests_list_file) as f:
            all_tests_dic = json.load(f)

        reorganized_all_tests_dic = utility.reorganize_tests_dic(all_tests_dic, "android")
        logger.debug("reorganized_all_tests_dic: %s" % reorganized_all_tests_dic)

        if scope_name == "webview":
            for sub_test in ["embedding-api-android-tests", "embedding-asyncapi-android-tests"]:
                test_category = "WebAPI"
                status = unzip_install_package(target_type, device_arch, device_id, target_version, var_ww, device_name, scope_name, test_category, sub_test, rerun)

                if not status:
                    continue

                sub_test_info_dic = reorganized_all_tests_dic["WebAPI"][sub_test]
                test_handle(device_name, scope_name, target_type, target_version, device_id, device_arch, test_category, sub_test, sub_test_info_dic, None, rerun)
                uninstall_package(device_name, scope_name, test_category, sub_test, device_id, rerun)

            continue

        for test_category, tests_dic in reorganized_all_tests_dic.iteritems():
            if test_category == "WebAPI":
                webapi_tests_dic = tests_dic

                if pack_mode == "shared" and scope_name == "apk":
                    install_runtimelib(target_type, device_arch, device_id, target_version, device_name)

                print webapi_tests_dic.iteritems()
                for aio_test, aio_test_info_dic in webapi_tests_dic.iteritems():
                    if aio_test in ["embedding-api-android-tests", "embedding-asyncapi-android-tests", "usecase-webapi-xwalk-tests"]:
                        continue

                    if aio_test in ["webmanu-system-android-tests"]:
                        sub_test = aio_test
                        sub_test_info_dic = reorganized_all_tests_dic["WebAPI"][aio_test]
                        status = unzip_install_package(target_type, device_arch, device_id, target_version, var_ww, device_name, scope_name, test_category, sub_test, rerun)

                        if not status:
                            continue
                        test_handle(device_name, scope_name, target_type, target_version, device_id, device_arch, test_category, sub_test, sub_test_info_dic, None, rerun)
                        uninstall_package(device_name, scope_name, test_category, sub_test, device_id, rerun)
                        continue

                    status = unzip_install_package(target_type, device_arch, device_id, target_version, var_ww, device_name, scope_name, test_category, aio_test, rerun)

                    if not status:
                        continue

                    if aio_test == "webapi-service-tests":
                        deploy_service_envs(device_name, scope_name, target_type, target_version, device_id, device_arch, var_ww)

                    for sub_test, sub_test_info_dic in aio_test_info_dic.iteritems():
                        if aio_test == "webapi-service-tests":
                            active_tinyweb(device_name, device_id)

                        test_handle(device_name, scope_name, target_type, target_version, device_id, device_arch, test_category, sub_test, sub_test_info_dic, aio_test, rerun)

                    uninstall_package(device_name, scope_name, test_category, aio_test, device_id, rerun)

                    if aio_test == "webapi-service-tests":
                        clean_service_envs(device_name, device_id)

                if pack_mode == "shared":
                    logger.debug("Uninstall XWalkRuntimeLib on '%s'." % device_name)
                    os.system("adb -s %s uninstall org.xwalk.core" % device_id)
            else:
                if scope_name == "cordova":
                    if test_category in ["SampleApp","UseCase","Cordova"]:
                        pass
                    else:
                        continue
                for sub_test, sub_test_info_dic in tests_dic.iteritems():
                    status = unzip_install_package(target_type, device_arch, device_id, target_version, var_ww, device_name, scope_name, test_category, sub_test, rerun)

                    if not status:
                        continue

                    test_handle(device_name, scope_name, target_type, target_version, device_id, device_arch, test_category, sub_test, sub_test_info_dic, None, rerun)
                    uninstall_package(device_name, scope_name, test_category, sub_test, device_id, rerun)
    if not rerun:
        save_rerun_tests_dir = "../rerun/%s/%s" % (START_TEST_TIME, device_name)
        if os.path.exists(save_rerun_tests_dir):
            logger.debug(">>>>>>>>>>>Begin to do rerun on %s, generate rerun tests_list.json" % device_name)
            for tmp_rerun_dir in glob.glob("%s/*" % save_rerun_tests_dir):
                tests_txt_file = "%s/tests.txt" % tmp_rerun_dir
                dorerun.generate_rerun_tests_list(device_name, tests_txt_file, tmp_rerun_dir)
            run_tests(device_name, is_manual, "rerun")

        result_dir = "%s/test-result/%s_android_%s/%s/%s_%s" % (project_path, target_type, device_arch, device_name, target_version, START_TEST_TIME)
        os.system("find %s/../ -name '*.dmesg' -delete" % result_dir)
        os.system("find %s/../ -name '*.logcat' -delete" % result_dir)

        #merge 2 test times results file, then do the following steps
        rerun_result_dir = "%s/test-result/%s_android_%s/%s/rerun" % (project_path, target_type, device_arch, device_name)
        #result_dir = "%s/test-result/%s_android_%s/%s/%s_%s" % (project_path, target_type, device_arch, device_name, target_version, START_TEST_TIME)
        report_link_list = []
        for scope_name in test_scope_list:
            if os.path.exists("%s/%s" % (rerun_result_dir, scope_name)):
                os.system("cp -r %s/%s/* %s/%s" % (rerun_result_dir, scope_name, result_dir, scope_name))
            if settings_dic["upload_report"]:
                logger.debug("Upload result xml files onto http://wrt-qa-report.sh.intel.com/#/v2/")
                try:
                    s1, link_list = QAReport.upload(device_name, "%s/%s" % (result_dir, scope_name))
                    logger.debug("Upload report status: %s %s" % (s1, link_list))
                    if s1:
                        report_link_list.extend(link_list)
                except Exception, errormsg:
                    logger.error("Error: \"%s\" happened when Upload report!" % errormsg)

            logger.debug("Please wait, now analyzing result files by testing on \'%s\'..." % device_name)
            analyze_xml_dir = "%s/test-env/%s/analyze_xml" % (project_path, device_name)
            if scope_name == "apk":
                analyze_result("%s/%s" % (result_dir, scope_name), analyze_xml_dir)
            elif scope_name == "webview":
                analyze_xml_dir = "%s/test-env/%s/%s/analyze_xml" % (project_path, device_name, scope_name)
                analyze_result("%s/%s" % (result_dir, scope_name), analyze_xml_dir)
            elif scope_name == "cordova":
                if os.path.exists("%s/WRT" % analyze_xml_dir):
                    os.system("mv %s/WRT %s/../" % (analyze_xml_dir, analyze_xml_dir))
                analyze_result("%s/%s" % (result_dir, scope_name), analyze_xml_dir)
                if os.path.exists("%s/../WRT" % analyze_xml_dir):
                    os.system("mv %s/../WRT %s/" % (analyze_xml_dir, analyze_xml_dir))

        generate_report_summary(result_dir, target_type, target_version, device_name, android_version, report_link_list)

        s2 = QAMail.send(device_name, result_dir)
        logger.debug("Send mail status: %s" % s2)

        first_run_dir = "%s/test-result/%s_android_%s/%s/first_run" % (project_path, target_type, device_arch, device_name)
        if os.path.exists(first_run_dir):
            os.system("mv %s %s" % (first_run_dir, result_dir))

        if os.path.exists(rerun_result_dir):
            os.system("mv %s %s" % (rerun_result_dir, result_dir))


def execute():
    global START_TEST_TIME

    START_TEST_TIME = time.strftime('%Y%m%d%H%M', time.localtime())
    #time1 = time.localtime(time.time())
    #start_test_time = datetime.datetime(time1[0], time1[1], time1[2], time1[3], time1[4], time1[5])

    flag = utility.default_check_config_json_valid()

    if not flag:
        logger.error("The \'config.json\' file is not correct. Please modify it.")
        return False

    is_valid, is_manual = utility.double_check_config_json_valid()

    if not is_valid:
        return False

    #status = ReadyPackagesLocal.execute()
    env_vars = settings_dic["env_vars"]
    os.environ["DISPLAY"] = env_vars["DISPLAY"]
    env_path = os.environ["PATH"]
    os.environ["PATH"] = "%s:%s" % (':'.join(env_vars["PATH"]), env_path)
    os.chdir("%s/scripts" % project_path)

    if auto_pack_packages:
        status = ReadyPackagesLocal.execute()
    else:
        status = ReadyPackagesLocal.execute_new()

    if not status:
        logger.error("Fail to pack tests packages.")
        return False
    else:
        try:
            with open("pack_results.json") as f:
                global pack_results_dic
                pack_results_dic = json.load(f)
        except Exception, errormsg:
            logger.error("Error: \"%s\" happened when getting \'pack_results_dic\' from \'pack_results.json\'." % errormsg)
            return False

    job_thread_list = []

    if pack_results_dic.has_key("all_no_upate"):
        #pass
        for device_name, device_detail in config_dic.iteritems():
            if device_detail["device_os"] == "android":
                if auto_pack_packages:
                    target_type = device_detail["target_type"]
                else:
                    target_type = settings_dic['target_branch'].replace("master", "canary")

                device_arch = device_detail["device_arch"]
                arch = arch_dic[device_arch]
                detail_type = "%s Android %s" % (target_type.capitalize(), arch)
                mail_content = no_update_mail_templet % detail_type
                mail_thread = threading.Thread(target = send_mail, args = (mail_content, target_type, device_arch, device_name, START_TEST_TIME))
                job_thread_list.append(mail_thread)
    else:
        if is_manual:
            if not pack_results_dic.has_key(key_pack_ok):
                return False

            pack_ok_dic = pack_results_dic[key_pack_ok]

            for target_type, version_list in pack_ok_dic.iteritems():
                for device_name, device_info_dic in config_dic.iteritems():
                    if (device_info_dic["device_os"] == "android") and ((auto_pack_packages and device_info_dic["target_type"] == target_type) or (auto_pack_packages == 0)):
                        if device_info_dic["specify_version"] in version_list:
                            device_id = device_info_dic["device_id"]
                            device_actives_info = commands.getoutput("adb devices")
                            if device_id in device_actives_info:
                                test_thread = threading.Thread(target = run_tests, args = (device_name, True))
                                job_thread_list.append(test_thread)
        else:
            if pack_results_dic.has_key(key_no_update):
                target_type_list = pack_results_dic[key_no_update]

                for target_type in target_type_list:
                    for device_name, device_info_dic in config_dic.iteritems():
                        if (device_info_dic["device_os"] == "android") and ((auto_pack_packages and device_info_dic["target_type"] == target_type) or (auto_pack_packages == 0)):
                            device_arch = device_info_dic["device_arch"]
                            arch = arch_dic[device_arch]
                            detail_type = "%s Android %s" % (target_type.capitalize(), arch)
                            mail_content = no_update_mail_templet % detail_type
                            mail_thread = threading.Thread(target = send_mail, args = (mail_content, target_type, device_arch, device_name, START_TEST_TIME))
                            #job_thread_list.append(mail_thread)

            if pack_results_dic.has_key(key_pack_ok):
                target_type_list = pack_results_dic[key_pack_ok]

                for target_type in target_type_list:
                    for device_name, device_info_dic in config_dic.iteritems():
                        device_id = device_info_dic["device_id"]
                        device_actives_info = commands.getoutput("adb devices")
                        if device_id in device_actives_info:
                            if (device_info_dic["device_os"] == "android") and ((auto_pack_packages and device_info_dic["target_type"] == target_type) or (auto_pack_packages == 0)):
                                test_thread = threading.Thread(target = run_tests, args = (device_name, False))
                                job_thread_list.append(test_thread)


    if not job_thread_list:
        return False

    for job_thread in job_thread_list:
        job_thread.start()

    for job_thread in job_thread_list:
        job_thread.join()

    os.system("rm -rf %s/test-env" % project_path)
    return True


if __name__ == '__main__':
    output = commands.getoutput("ps -ef | grep -c 'web-auto-testing.py'")
    if int(output) > 4:
        sys.exit(1)

    status = execute()
    print "Run tests status: %s" % status
