import commands
import json
import os
import re
import time
import urllib2
import common


error_version = "ErrorVerison"
logger = common.logger
config_dic = common.config_dic
settings_dic = common.settings_dic
pack_mode = settings_dic["pack_mode"]
current_ww = settings_dic["current_ww"]
project_path = settings_dic["project_path"]
test_scope_list = settings_dic["test_scope_list"]
crosswalk_releases_url_external = settings_dic["crosswalk_releases_url_external"]
crosswalk_releases_url_internal = settings_dic["crosswalk_releases_url_internal"]
tests_project_path = settings_dic["tests_project_path"]
crosswalk_infos_file = "tested_crosswalk_infos.json"
pack_results_file = "pack_results.json"
manual_pack_result_list = common.manual_pack_result_list
key_pack_ok = manual_pack_result_list[0]
key_pack_error = manual_pack_result_list[1]
key_no_update = manual_pack_result_list[2]


def download_crosswalk(target_type, version, manual_flag = False):
    save_dir = "%s/repo/wrt/android/%s" % (project_path, target_type)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    if os.path.exists("%s/%s" % (save_dir, version)):
        logger.debug("Already exsits '%s/%s'" % (save_dir, version))
        return True

    download_url = "%s/crosswalk/android/%s/%s/" % (crosswalk_releases_url_internal, target_type, version)
    download_cmd = "wget -r -np %s --no-check-certificate -nH --cut-dirs=5 -A zip -P %s" % (download_url, save_dir)

    os.system(download_cmd)
    #TODO: check whether download successfully

    is_need_record_version(target_type, version)
    return True


def setup_pack_env(target_type, version):
    crosswalk_file = "%s/repo/wrt/android/%s/%s/crosswalk-%s.zip" % (project_path, target_type, version, version)

    if not os.path.isfile(crosswalk_file):
        logger.error("No such file '%s'" % crosswalk_file)
        return False

    tools_dir = "%s/tools" % tests_project_path
    crosswalk_dir = "%s/crosswalk" % tools_dir

    if os.path.exists(crosswalk_dir):
        os.system("rm -r %s" % crosswalk_dir)

    os.system("unzip %s -d %s" % (crosswalk_file, tools_dir))
    os.system("mv %s/crosswalk-%s %s/crosswalk" % (tools_dir, version, tools_dir))
    return True


def sub_setup_pack_env(target_type, version, arch, scope_name):
    #prepare XwalkRuntimeLibrary.apk into tools
    tools_dir = "%s/tools" % tests_project_path

    if scope_name == "apk":
        lib_file = "XWalkRuntimeLib.apk"

        if os.path.isfile("%s/%s" % (tools_dir, lib_file)):
            os.system("rm %s/%s" % (tools_dir, lib_file))

        crosswalk_apks_dir = "%s/crosswalk-apks-%s-%s" % (tools_dir, version, arch)
        if os.path.exists(crosswalk_apks_dir):
            os.system("rm -r %s" % crosswalk_apks_dir)

        crosswalk_apks_file = "%s/repo/wrt/android/%s/%s/%s/crosswalk-apks-%s-%s.zip" % (project_path, target_type, version, arch, version, arch)
        if not os.path.isfile(crosswalk_apks_file):
            logger.error("No such file '%s'" % crosswalk_apks_file)
            return False

        os.system("unzip %s -d %s" % (crosswalk_apks_file, tools_dir))

        src_lib_file = "%s/%s" % (crosswalk_apks_dir, lib_file)
        if not os.path.isfile(src_lib_file):
            logger.error("No such file '%s'" % src_lib_file)
            return False

        os.system("cp %s %s" % (src_lib_file, tools_dir))
        os.system("rm -r %s" % crosswalk_apks_dir)
        return True
    elif scope_name == "cordova":
        cordova_dir = "%s/tools/cordova" % tests_project_path

        if os.path.exists(cordova_dir):
            os.system("rm -r %s" % cordova_dir)

        cordova_file = "%s/repo/wrt/android/%s/%s/%s/crosswalk-cordova-%s-%s.zip" % (project_path, target_type, version, arch, version, arch)
        if not os.path.isfile(cordova_file):
            logger.error("No such file '%s'" % cordova_file)
            return False

        os.system("unzip %s -d %s" % (cordova_file, tools_dir))
        os.system("mv %s/tools/crosswalk-cordova-%s-%s %s" % (tests_project_path, version, arch, cordova_dir))
        return True
    elif scope_name == "webview":
        webview_dir = "%s/tools/crosswalk-webview" % tests_project_path

        if os.path.exists(webview_dir):
            os.system("rm -r %s" % webview_dir)

        webview_file = "%s/repo/wrt/android/%s/%s/%s/crosswalk-webview-%s-%s.zip" % (project_path, target_type, version, arch, version, arch)
        if not os.path.isfile(webview_file):
            logger.error("No such file '%s'" % webview_file)
            return False

        os.system("unzip %s -d %s" % (webview_file, tools_dir))
        os.system("mv %s/tools/crosswalk-webview-%s-%s %s" % (tests_project_path, version, arch, webview_dir))
        return True


def do_pack(arch, test_category, test_suite_name, target_type, version, scope_name):
    save_docroot_dir = "%s/repo/docroot/%s/%s/%s" % (project_path, current_ww, scope_name, arch)

    if test_suite_name == "webapi-service-docroot-tests":
        if os.path.exists(save_docroot_dir):
            logger.info("Already exists the docroot package for \'%s\'." % current_ww)
            return True


    tool_info = "crosswalk-%s" % version

    if scope_name == "cordova":
        tool_info = "crosswalk-cordova-%s-%s" % (version, arch)
    elif scope_name == "webview":
        tool_info = "crosswalk-webview-%s-%s" % (version, arch)

    logger.info("[%s] Begin to pack %s \'%s\' package by \'%s %s\'." % (time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime()), arch, test_suite_name, target_type, tool_info))

    if test_suite_name == "webapi-service-docroot-tests":
        save_dir = save_docroot_dir
    else:
        save_dir = "%s/repo/tests/android/%s/%s/%s/%s/%s/%s" % (project_path, target_type, version, current_ww, scope_name, arch, test_category)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    #Only for 'apk' scope and test-suite-name in ['wrt-manifest-android-tests','wrt-packertool-android-tests']
    if scope_name == "apk" and (test_suite_name in ['wrt-manifest-android-tests','wrt-packertool-android-tests']):
        #prepare sub apk packages
        logger.debug("[%s] Begin to prepare sub apk packages of %s" % (time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime()), test_suite_name))
        testpackages_dir = "%s/wrt/%s/apks" % (tests_project_path, test_suite_name)
        if os.path.exists(testpackages_dir):
            os.system("rm -r %s" % testpackages_dir)

        packRes_file = "%s/wrt/%s/report/packRes.txt" % (tests_project_path, test_suite_name)
        if os.path.isfile(packRes_file):
             os.system("rm %s" % packRes_file)

        os.system("python %s/wrt/%s/ge_package.py" % (tests_project_path, test_suite_name))

        backup_dir = "%s/%s_testpackages" % (save_dir, test_suite_name)#"repo/tests/android/canary/11.39.260.0/WW48/apk/arm/WRT/wrt-packagemgt-android-tests_testpackages"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        testpackages_dir = "%s/wrt/%s/apks" % (tests_project_path, test_suite_name)
        os.system("cp -r %s %s" % (testpackages_dir, backup_dir))

        if os.path.exists(testpackages_dir):
            os.system("rm -r %s" % testpackages_dir)

    pack_cmd_dic = {
        "WebAPI": {
            "aio": "bash %(tests_project_path)s/misc/%(test_name)s/pack.sh -t %(scope)s -a %(arch)s -m %(pack_mode)s",
            "embeddingapi": "python %(tests_project_path)s/tools/build/pack.py -t embeddingapi -s %(tests_project_path)s/embeddingapi/%(test_name)s"
        },
        "UseCase": {
            "usecase": "python %(tests_project_path)s/tools/build/pack.py -t %(scope)s -a %(arch)s -m embedded -s %(tests_project_path)s/usecase/%(test_name)s"
        },
        "SampleApp": {
            "sampleapp": "python %(tests_project_path)s/tools/build/pack.py -t %(scope)s -a %(arch)s -m embedded -s %(tests_project_path)s/misc/%(test_name)s",
            "sysapps": "python %(tests_project_path)s/tools/crosswalk/make_apk.py --package=org.xwalk.sysapps --manifest=/tmp/crosswalk-demos/SysApps_DeviceCapabilities/src/manifest.json --mode=embedded --arch=x86 --enable-remote-debugging",
            "gallery": "python %(tests_project_path)s/tools/crosswalk/make_apk.py --package=org.xwalk.gallery --manifest=/tmp/crosswalk-demos/Gallery/manifest.json --mode=embedded --arch=x86 --enable-remote-debugging",
            "hexgl": "python %(tests_project_path)s/tools/crosswalk/make_apk.py --package=org.xwalk.hexgl --name=Hexgl --app-root=/tmp/crosswalk-demos/HexGL/assets/www --app-local-path=index.html --mode=embedded --arch=x86 --enable-remote-debugging",
            "memorygame": "python %(tests_project_path)s/tools/crosswalk/make_apk.py --package=org.xwalk.memorygame --name=Memorygame --app-root=/tmp/crosswalk-demos/MemoryGame/src --app-local-path=index.html --mode=embedded --arch=x86 --enable-remote-debugging",
            "simd": "python %(tests_project_path)s/tools/crosswalk/make_apk.py --package=org.xwalk.simd --name=Simd --app-url=http://peterjensen.github.io/mandelbrot/js/mandelbrot-xdk.html --mode=embedded --arch=x86 --enable-remote-debugging",
            "webtrc": "python %(tests_project_path)s/tools/crosswalk/make_apk.py --package=org.xwalk.webrtc --manifest=/tmp/crosswalk-demos/WebRTC/manifest.json --mode=embedded --arch=x86 --enable-remote-debugging",
            "hangoman": "python %(tests_project_path)s/tools/crosswalk/make_apk.py --package=org.xwalk.hangonman --name=hangonman --app-root=/tmp/crosswalk-demos/HangOnMan/app --app-local-path=index.html"
        },
        "WRT": "python %(tests_project_path)s/tools/build/pack.py -t %(scope)s -m embedded -a %(arch)s -s %(tests_project_path)s/wrt/%(test_name)s"
    }

    #os.system('rm -rf %s/%s/%s/%s*.zip' % (tests_project_path, tmp_dir, test_suite_name, test_suite_name))    
    for i in range(1,6):
        logger.debug("-------------ReBuild package-------------: %s " % i)
        if test_category == "WebAPI":
            if scope_name == "webview":
                os.system(pack_cmd_dic[test_category]["embeddingapi"] % {"tests_project_path": tests_project_path, "test_name": test_suite_name})
            else:
                os.system(pack_cmd_dic[test_category]["aio"] % {"tests_project_path": tests_project_path, "test_name": test_suite_name, "arch": arch, "scope": scope_name, "pack_mode": pack_mode})
        elif test_category == "UseCase":
            os.system(pack_cmd_dic[test_category]["usecase"] % {"tests_project_path": tests_project_path, "test_name": test_suite_name, "arch": arch, "scope": scope_name})
        elif test_category == "SampleApp":
            for pre_sample in ["sysapps", "gallery", "hexgl", "memorygame", "simd", "webtrc", "hangoman"]:
                print "---------------%s-------------------------" % pre_sample
                os.system(pack_cmd_dic[test_category][pre_sample] % {"tests_project_path": tests_project_path, "arch": arch})
            os.system("rm -rf /tmp/Sampleapp_binary/*.apk")
            os.system("mv *.apk /tmp/Sampleapp_binary/") 
            os.system(pack_cmd_dic[test_category]["sampleapp"] % {"tests_project_path": tests_project_path, "test_name": test_suite_name, "arch": arch, "scope": scope_name})
        else:
            os.system(pack_cmd_dic[test_category] % {"tests_project_path": tests_project_path, "test_name": test_suite_name, "arch": arch, "scope": scope_name})

        tmp_dir = "misc"
        if scope_name == "webview":
            tmp_dir = "embeddingapi"
        elif test_category == "WRT":
            tmp_dir = "wrt"
        elif test_category == "UseCase":
            tmp_dir = "usecase"
        #os.system('rm -rf %s/%s/%s/%s*.zip' % (tests_project_path, tmp_dir, test_suite_name, test_suite_name))
         
        apk_files,o = commands.getstatusoutput('unzip -v %s/%s/%s/%s*.zip | grep apk' % (tests_project_path, tmp_dir, test_suite_name, test_suite_name))

        if apk_files == 0:
            break
        else :
            logger.info("[%s] Fail to pack %s \'%s\' apk package by \'%s %s\'." % (time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime()), arch, test_suite_name, target_type, tool_info))      

    package_file = commands.getoutput('ls %s/%s/%s/%s*.zip' % (tests_project_path, tmp_dir, test_suite_name, test_suite_name))

    if package_file.find('No such file or directory') != -1:
        logger.info("[%s] Fail to pack %s \'%s\' package by \'%s %s\'." % (time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime()), arch, test_suite_name, target_type, tool_info))
        return False

    logger.info("[%s] Success to pack %s \'%s\' package by \'%s %s\'." % (time.strftime('%Y-%m-%d-%H:%M:%S', time.localtime()), arch, test_suite_name, target_type, tool_info))
    
    os.system('cp %s %s' % (package_file, save_dir))
    logger.info('cp %s %s' % (package_file, save_dir))
    os.system('rm -rf %s/%s/%s/%s*.zip' % (tests_project_path, tmp_dir, test_suite_name, test_suite_name))
    logger.info('rm -rf %s/%s/%s/%s*.zip' % (tests_project_path, tmp_dir, test_suite_name, test_suite_name))
    return True


def pack_tests_packages(target_type, version):
    arch_list = common.get_arch_list()
    with open("../resources/merged_tests_list.json") as f:
        merged_tests_dic = json.load(f)

    tests_dic = common.reorganize_tests_dic(merged_tests_dic, "android")
    test_category_list = tests_dic.keys()

    if "WebAPI" in test_category_list:
        if tests_dic["WebAPI"].has_key("webapi-service-tests"):
            for arch in arch_list:
                for scope_name in test_scope_list:
                    test_category = "WebAPI"
                    test_suite_name = "webapi-service-docroot-tests"
                    do_pack(arch, test_category, test_suite_name, target_type, version, scope_name)

    for arch in arch_list:
        for scope_name in test_scope_list:
            sub_setup_pack_env(target_type, version, arch, scope_name)

            if scope_name == "webview":
                #for extend, if new embeddingapi test added, update test_name_list
                test_name_list = ["embedding-api-android-tests"]
                test_category = "WebAPI"
                for test_name in test_name_list:
                    do_pack(arch, test_category, test_name, target_type, version, scope_name)
            else:
                for test_category in test_category_list:
                    if scope_name == "cordova" and test_category == "WRT":
                        break

                    test_list = tests_dic[test_category].keys()

                    for test_name in test_list:
                        if test_name != "embedding-api-android-tests":
                            if test_name in ['wrt-manifest-android-tests','wrt-packertool-android-tests']:
                                #write arch's value in arch.txt
                                arch_file = "%s/wrt/%s/arch.txt" % (tests_project_path, test_name)
                                write_handle = open(arch_file, 'w')
                                write_handle.write(arch)
                                write_handle.close()

                            do_pack(arch, test_category, test_name, target_type, version, scope_name)



def compare_versions(last_version, current_version):
    if last_version == current_version:
        return False

    last_version_seg = [int(x) for x in last_version.split('.')]
    current_version_seg = [int(y) for y in current_version.split('.')]
    length = len(last_version_seg)

    for index in range(length):
        if last_version_seg[index] < current_version_seg[index]:
            return True

    return False


def is_need_record_version(target_type, version):
    if not os.path.isfile(crosswalk_infos_file):
        crosswalk_infos_dic = {}
        sub_infos_dic = {}
        sub_infos_dic["latest_version"] = version
        sub_infos_dic["0001"] = version
        crosswalk_infos_dic[target_type] = sub_infos_dic
        common.record_infos(crosswalk_infos_dic, crosswalk_infos_file)
        return True
    else:
        with open(crosswalk_infos_file) as f:
            crosswalk_infos_dic = json.load(f)

        if not crosswalk_infos_dic.has_key(target_type):
            sub_infos_dic = {}
            sub_infos_dic["latest_version"] = version
            sub_infos_dic["0001"] = version
            crosswalk_infos_dic[target_type] = sub_infos_dic
            common.record_infos(crosswalk_infos_dic, crosswalk_infos_file)
            return True
        else:
            last_version = crosswalk_infos_dic[target_type]["latest_version"]

            if compare_versions(last_version, version):
                sub_infos_dic = crosswalk_infos_dic[target_type]
                sub_infos_dic["latest_version"] = version
                index = "%04d" % len(sub_infos_dic)
                sub_infos_dic[index] = version
                common.record_infos(crosswalk_infos_dic, crosswalk_infos_file)
                return True
            else:
                return False


def get_update_crosswalk(url, target_type):
    try:
        logger.info("Listen URL: %s" % url)
        bk_http_proxy = os.environ['http_proxy']
        os.environ['http_proxy'] = ''
        listen_page = urllib2.urlopen(url)
        os.environ['http_proxy'] = bk_http_proxy
    except urllib2.HTTPError:
        logger.error("HTTP Error, please check your network connect status.")
        return error_version

    content = listen_page.read()
    pattern = re.compile('\<img\ src=\"\/icons\/folder\.gif\"\ alt=\"\[DIR\]\"\>.*')
    version_infos_list = pattern.findall(content)

    if not version_infos_list:
        logger.error("Fail to get Crosswalk \'%s\' latest version" % target_type)
        return error_version
    else:
        latest_version_info = version_infos_list[-1]#-1
        latest_version = latest_version_info.split('/</a>')[0].split('>')[-1]
        logger.debug("The latest released version of \'%s\': \'%s\'" % (target_type, latest_version))
        #latest_version = "17.45.422.0" #TODO1016
        update_status = is_need_record_version(target_type, latest_version)


        if update_status:
            return latest_version
        else:
            return None


def execute():
    #TODO: Optimize to use threads to get packages ready parallel
    #Current, only consider testing by android xwalk
    flag = common.default_check_config_json_valid()

    if not flag:
        logger.error("The \'config.json\' file is not correct. Please modify it.")
        return False

    is_valid, is_manual = common.double_check_config_json_valid()

    if not is_valid:
        return False
    else:
        if is_manual:
            logger.debug("Pack packages by the specified version.")
            manual_pack_results_dic = {}#{"beta": {"v1":0,'v2':1}}
            manual_target_crosswalk_dic = {}#{"beta": ["v1", "v2"]}

            for manual_device_item in config_dic.items():
                manual_device_details_dic = manual_device_item[1]
                manual_target_type = manual_device_details_dic["target_type"]
                manual_target_version = manual_device_details_dic["specify_version"]

                if os.path.exists("%s/repo/tests/android/%s/%s" % (project_path, manual_target_type, manual_target_version)):
                    logger.debug("Already ready tests packages.")

                    if not manual_pack_results_dic.has_key(key_pack_ok):
                        sub_dic = {}
                        sub_dic[manual_target_type] = [manual_target_version]
                        manual_pack_results_dic[key_pack_ok] = sub_dic
                    else:
                        sub_dic = manual_pack_results_dic[key_pack_ok]

                        if not sub_dic.has_key(manual_target_type):
                            sub_dic = {}
                            sub_dic[manual_target_type] = [manual_target_version]
                        else:
                            version_list = sub_dic[manual_target_type]

                            if manual_target_version not in version_list:
                                version_list.append(manual_target_version)
                else:
                    if manual_target_crosswalk_dic.has_key(manual_target_type):
                        version_list = manual_target_crosswalk_dic[manual_target_type]

                        if manual_target_version not in version_list:
                            version_list.append(manual_target_version)
                    else:
                        manual_target_crosswalk_dic[manual_target_type] = [manual_target_version]

            if not manual_target_crosswalk_dic:
                common.record_infos(manual_pack_results_dic, pack_results_file)
                return True

            logger.debug("manual_target_crosswalk_dic: \"%s\"." % manual_target_crosswalk_dic)

            for target_type, version_list in manual_target_crosswalk_dic.iteritems():
                for version in version_list:
                    download_status = download_crosswalk(target_type, version, True)

                    if download_status:
                        status = setup_pack_env(target_type, version)

                        if not status:
                            logger.error("Fail to pack tests packages by \'%s crosswalk-%s\'" % (target_type, version))

                            if not manual_pack_results_dic.has_key(key_pack_error):
                                sub_dic = {}
                                sub_dic[target_type] = [version]
                                manual_pack_results_dic[key_pack_error] = sub_dic
                            else:
                                sub_dic = manual_pack_results_dic[key_pack_error]

                                if not sub_dic.has_key(target_type):
                                    sub_dic[target_type] = [version]
                                else:
                                    pack_error_version_list = sub_dic[target_type]
                                    pack_error_version_list.append(version)
                        else:
                            pack_tests_packages(target_type, version)

                            logger.info("Success to pack tests packages by \'%s crosswalk-%s\'" % (target_type, version))

                            if not manual_pack_results_dic.has_key(key_pack_ok):
                                sub_dic = {}
                                sub_dic[target_type] = [version]
                                manual_pack_results_dic[key_pack_ok] = sub_dic
                            else:
                                sub_dic = manual_pack_results_dic[key_pack_ok]

                                if not sub_dic.has_key(target_type):
                                    sub_dic[target_type] = [version]
                                else:
                                    pack_ok_version_list = sub_dic[target_type]
                                    pack_ok_version_list.append(version)
                    else:
                        logger.error("Fail to dowanload \'%s/crosswalk/android/%s/%s/crosswalk-%s.zip\'" % (crosswalk_releases_url_external, target_type, version, version))

                        if not manual_pack_results_dic.has_key(key_pack_error):
                            sub_dic = {}
                            sub_dic[target_type] = [version]
                            manual_pack_results_dic[key_pack_error] = sub_dic
                        else:
                            sub_dic = manual_pack_results_dic[key_pack_error]

                            if not sub_dic.has_key(target_type):
                                sub_dic[target_type] = [version]
                            else:
                                pack_error_version_list = sub_dic[target_type]
                                pack_error_version_list.append(version)

            common.record_infos(manual_pack_results_dic, pack_results_file)
            return True

    target_crosswalk_dic = {}

    #Current, all devices auto test the same version crosswalk
    for device_name, device_details_dic in config_dic.iteritems():
        if device_details_dic["device_os"] == "android":
            target_type = device_details_dic["target_type"]

            if not target_crosswalk_dic.has_key(target_type):
                target_crosswalk_dic[target_type] = None

    logger.debug("Target Crosswalk dic: \"%s\"." % target_crosswalk_dic)
    target_num = len(target_crosswalk_dic)
    pack_results_dic = {}
    download_crosswalk_dic = {}

    for target in target_crosswalk_dic:
        listen_url = "%s/crosswalk/android/%s" % (crosswalk_releases_url_external, target)
        latest_version = get_update_crosswalk(listen_url, target)

        if not latest_version:
            if not pack_results_dic.has_key(key_no_update):
                pack_results_dic[key_no_update] = [target]
            else:
                pack_results_dic[key_no_update].append(target)
        elif latest_version == error_version:
            if not pack_results_dic.has_key(key_pack_error):
                pack_results_dic[key_pack_error] = [target]
            else:
                pack_results_dic[key_pack_error].append(target)
        else:
             download_crosswalk_dic[target] = latest_version

    logger.debug("After checking, download_crosswalk_dic: \"%s\"." % download_crosswalk_dic)
    logger.debug("After checking, pack_results_dic: \"%s\"." % pack_results_dic)

    if (not download_crosswalk_dic) and pack_results_dic.has_key(key_no_update):
        no_update_target_list = pack_results_dic[key_no_update]

        if len(no_update_target_list) == target_num:
            if target_num > 1:
                logger.info("No all new crosswalk of \"%s\" released." % no_update_target_list)
            else:
                logger.info("No new crosswalk of \'%s\' released." % no_update_target_list[0])

            pack_results_dic['all_no_upate'] = "all_no_update"
            common.record_infos(pack_results_dic, pack_results_file)
            return True

    if (not download_crosswalk_dic) and (not pack_results_dic.has_key(key_no_update)):
        return False

    for target_type, update_version in download_crosswalk_dic.iteritems():
        download_status = download_crosswalk(target_type, update_version)

        if download_status:
            status = setup_pack_env(target_type, update_version)

            if not status:
                logger.error("Fail to pack tests packages by \'%s crosswalk-%s\'" % (target_type, update_version))

                if not pack_results_dic.has_key(key_pack_error):
                    pack_results_dic[key_pack_error] = [target_type]
                else:
                    pack_results_dic[key_pack_error].append(target_type)
            else:
                pack_tests_packages(target_type, update_version)
                logger.info("Success to pack tests packages by \'%s crosswalk-%s\'" % (target_type, update_version))

                if not pack_results_dic.has_key(key_pack_ok):
                    pack_ok_dic = {}
                    pack_ok_dic[target_type] = [update_version]
                    pack_results_dic[key_pack_ok] = pack_ok_dic
                else:
                    pack_ok_dic = pack_results_dic[key_pack_ok]
                    pack_ok_dic[target_type] = [update_version]
        else:
            logger.error("Fail to dowanload \'%s/crosswalk/android/%s/%s/crosswalk-%s.zip\'" % (crosswalk_releases_url_internal, target_type, update_version, update_version))

            if not pack_results_dic.has_key(key_pack_error):
                pack_results_dic[key_pack_error] = [target_type]
            else:
                pack_results_dic[key_pack_error].append(target_type)

    common.record_infos(pack_results_dic, pack_results_file)
    return True



def download_from_pack_server(url, target_type, version):
    #Download crossalk
    crosswalk_save_dir = "%s/repo/wrt/android/%s/%s" % (project_path, target_type, version)
    if os.path.exists(crosswalk_save_dir):
        print "Already download crosswalk done."
    else:
        os.makedirs(crosswalk_save_dir)
        os.system("wget -r -np %s/%s/crosswalk-tools/ --no-proxy -nH --cut-dirs=6 -P %s -A zip,aar -c" % (url, version, crosswalk_save_dir))

    #pack_mode = settings_dic['pack_mode']
    #test_scope_list = settings_dic["test_scope_list"]
    #current_ww
    tests_save_dir = "%s/repo/tests/android/%s/%s/%s" % (project_path, target_type, version, current_ww)
    if os.path.exists(tests_save_dir):
        print "Already download tests packages done."
    else:
        os.makedirs(tests_save_dir)
        testsuites_dic = common.testsuites_dic
        arch_list = common.get_arch_list()

        for arch in arch_list:
            #repo/tests/android/canary/13.41.318.0/WW11/apk/arm/WebAPI
            #repo/tests/android/canary/13.41.317.0/WW10/apk/arm/WRT
            for test_scope in test_scope_list:
                if test_scope == "cordova":
                    tmp_tests_save_dir = "%s/%s/%s" % (tests_save_dir, testsuites_dic[test_scope], arch)
                    os.makedirs(tmp_tests_save_dir)
                    os.system("wget -r -np %s/%s/%s/%s --no-proxy -nH --cut-dirs=7 -P %s -A zip -c" % (url, version, testsuites_dic[test_scope], arch, tmp_tests_save_dir))
                else:
                    tmp_tests_save_dir = "%s/%s/%s" % (tests_save_dir, testsuites_dic[test_scope][pack_mode], arch)
                    if not os.path.exists(tmp_tests_save_dir):
                        os.makedirs(tmp_tests_save_dir)
                        os.system("wget -r -np %s/%s/%s/%s --no-proxy -nH --cut-dirs=7 -P %s -A zip -c" % (url, version, testsuites_dic[test_scope][pack_mode], arch, tmp_tests_save_dir))

def scp_from_pack_server(url, target_type, version):
    #Download crossalk
    crosswalk_save_dir = "%s/repo/wrt/android/%s/%s" % (project_path, target_type, version)
    if os.path.exists(crosswalk_save_dir):
        print "Already download crosswalk done."
    else:
        os.makedirs(crosswalk_save_dir)
        os.system("scp -r %s/%s/crosswalk-tools/* %s" % (url, version, crosswalk_save_dir))

    tests_save_dir = "%s/repo/tests/android/%s/%s/%s" % (project_path, target_type, version, current_ww)
    if os.path.exists(tests_save_dir):
        print "Already download tests packages done."
    else:
        os.makedirs(tests_save_dir)
        testsuites_dic = common.testsuites_dic
        arch_list = common.get_arch_list()

        for arch in arch_list:
            for test_scope in test_scope_list:
                if test_scope == "cordova":
                    #tmp_tests_save_dir = "%s/%s/%s" % (tests_save_dir, testsuites_dic[test_scope], arch)
                    tmp_tests_save_dir = "%s/%s" % (tests_save_dir, testsuites_dic[test_scope])
                    os.makedirs(tmp_tests_save_dir)
                    os.system("scp -r %s/%s/%s/%s %s" % (url, version, testsuites_dic[test_scope], arch, tmp_tests_save_dir))
                else:
                    #tmp_tests_save_dir = "%s/%s/%s" % (tests_save_dir, testsuites_dic[test_scope][pack_mode], arch)
                    tmp_tests_save_dir = "%s/%s" % (tests_save_dir, testsuites_dic[test_scope][pack_mode])
                    if not os.path.exists(tmp_tests_save_dir):
                        os.makedirs(tmp_tests_save_dir)
                        os.system("scp -r %s/%s/%s/%s %s" % (url, version, testsuites_dic[test_scope][pack_mode], arch, tmp_tests_save_dir))

def record_crosswalk_info_64bit(target_type, test_version):
    if not os.path.isfile(crosswalk_infos_file):
        crosswalk_infos_dic = {}
        sub_infos_dic = {}
        sub_infos_dic["latest_version"] = test_version
        sub_infos_dic["0001"] = test_version
        crosswalk_infos_dic[target_type] = sub_infos_dic
    else:
        with open(crosswalk_infos_file) as f:
            crosswalk_infos_dic = json.load(f)

        if not crosswalk_infos_dic.has_key(target_type):
            sub_infos_dic = {}
            sub_infos_dic["latest_version"] = test_version
            sub_infos_dic["0001"] = test_version
            crosswalk_infos_dic[target_type] = sub_infos_dic
        else:
            sub_infos_dic = crosswalk_infos_dic[target_type]
            sub_infos_dic["latest_version"] = test_version
            index = "%04d" % len(sub_infos_dic)
            sub_infos_dic[index] = test_version
    common.record_infos(crosswalk_infos_dic, crosswalk_infos_file)


def execute_64bit():
    #monitor 64bit_url
    pack_server_url = settings_dic['pack_server']
    target_version = settings_dic['target_version']
    target_type = settings_dic['target_branch']
    url = "%s/%s/%s-64bit" % (pack_server_url, target_type.replace('canary', 'master'), target_version)

    while True:
        try:
            bk_http_proxy = os.environ['http_proxy']
            os.environ['http_proxy'] = ''
            obj = urllib2.urlopen("%s/BUILD-INPROCESSKK" % url)
            os.environ['http_proxy'] = bk_http_proxy
        except urllib2.HTTPError:
            print "Not find BUILD-INPROCESS, means pack 64bit packages done."
            break
        time.sleep(600)
        print "Going on monitoring: %s ..." % url

    target_type = target_type.replace('master', 'canary')
    record_crosswalk_info_64bit(target_type, target_version)
    scp_pack_server = settings_dic['scp_pack_server']
    scp_from_pack_server(scp_pack_server, target_type, target_version)
    pack_ok_dic = {}
    pack_ok_dic[target_type] = [target_version]
    pack_results_dic[key_pack_ok] = pack_ok_dic

    common.record_infos(pack_results_dic, pack_results_file)


def execute_new():
    #Monitor latest version
    #if exits latest version, monitor flag BUILD-INPROCESS file
    target_branch = settings_dic['target_branch']
    listen_url = "%s/%s" % (settings_dic['pack_server'], target_branch)
    listen_server = "%s/%s" % (settings_dic['scp_pack_server'], target_branch)
    target = target_branch.replace("master", "canary")
    latest_version = get_update_crosswalk(listen_url, target)
    pack_results_dic = {}

    if not latest_version:
        if not pack_results_dic.has_key(key_no_update):
            pack_results_dic[key_no_update] = [target]
        else:
            pack_results_dic[key_no_update].append(target)
        common.record_infos(pack_results_dic, pack_results_file)
        return True
    elif latest_version == error_version:
        if not pack_results_dic.has_key(key_pack_error):
            pack_results_dic[key_pack_error] = [target]
        else:
            pack_results_dic[key_pack_error].append(target)
        common.record_infos(pack_results_dic, pack_results_file)
        return False

    pack_done = False

    while True:
        try:
            bk_http_proxy = os.environ['http_proxy']
            os.environ['http_proxy'] = ''
            obj = urllib2.urlopen("%s/%s/BUILD-INPROCESS" % (listen_url, latest_version))
            obj_manifest = urllib2.urlopen("%s/%s/apks-%s-manifest/BUILD-INPROCESS" % (listen_url, latest_version, latest_version))
            obj_packertool = urllib2.urlopen("%s/%s/apks-%s-packertool/BUILD-INPROCESS" % (listen_url, latest_version, latest_version))
            os.environ['http_proxy'] = bk_http_proxy
        except urllib2.HTTPError:
            print "Not find BUILD-INPROCESS, means pack done."
            pack_done = True
            break
        time.sleep(600)
        print "Going on to monitor: %s/%s" % (listen_url, latest_version)
        if int(time.strftime('%H', time.localtime(time.time()))) == 8:
            break

    if pack_done:
        scp_from_pack_server(listen_server, target, latest_version)
        if not pack_results_dic.has_key(key_pack_ok):
            pack_ok_dic = {}
            pack_ok_dic[target] = [latest_version]
            pack_results_dic[key_pack_ok] = pack_ok_dic
        else:
            pack_ok_dic = pack_results_dic[key_pack_ok]
            pack_ok_dic[target] = [latest_version]
        common.record_infos(pack_results_dic, pack_results_file)
        setup_pack_env(target, latest_version)
        return True
    else:
        if not pack_results_dic.has_key(key_pack_error):
            pack_results_dic[key_pack_error] = [target]
        else:
            pack_results_dic[key_pack_error].append(target)
        common.record_infos(pack_results_dic, pack_results_file)
        return False


if __name__ == '__main__':
    env_vars = settings_dic["env_vars"]
    os.environ["DISPLAY"] = env_vars["DISPLAY"]
    env_path = os.environ["PATH"]
    os.environ["PATH"] = "%s:%s" % (':'.join(env_vars["PATH"]), env_path)
    os.chdir("%s/scripts" % project_path)

    if settings_dic["auto_pack_packages"]:
        status = execute()
    else:
        if settings_dic["lite_64bit"] == 2:
            status = execute_64bit()
        elif settings_dic["lite_64bit"] == 0:
            status = execute_new()
    print "Pack tests packages status: \'%s\'" % status
