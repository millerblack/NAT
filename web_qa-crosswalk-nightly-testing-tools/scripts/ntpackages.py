import copy
import os
import re
import glob
import time
import threading
import multiprocessing
from util.ntcommon import *


def update_device_config_dic():
    nt_logger.debug("Call Function: 'update_device_config_dic'")
    update_device_config_dic = copy.deepcopy(device_config_dic)
    latest_version_dic = {}

    for device_name, device_info_dic in device_config_dic.iteritems():
        #1. filter untested devices
        if device_info_dic["is_tested"] == 0:
            del update_device_config_dic[device_name]
        else:
            #2. update 'latest' version as latest version
            if device_info_dic.has_key("target_binary"):
                target_binary_dic = device_info_dic["target_binary"]
                version = target_binary_dic["version"]
                if version == "latest":
                    branch = target_binary_dic["branch"]
                    if latest_version_dic.get(branch, None):
                        latest_version = latest_version_dic[branch]
                    else:
                        latest_version = get_latest_version(package_release_server_url, crosswalk_type, test_platform, branch)
                        latest_version_dic[branch] = latest_version
                    if latest_version == "error":
                        update_device_config_dic[device_name]["error_flag"] = 1
                    else:
                        rerun_flag = device_info_dic.get("rerun_flag", 0)
                        if rerun_flag == 0: #rerun_flag(1): no mater with update version
                            mode = target_binary_dic["mode"]
                            #for example segment_list likes ["crosswalk", "cordova4.x"], use "crosswalk" to check, no permit for mixing untested and tested segment
                            segment_delegate = target_binary_dic["segment_list"][0]
                            if is_binary_tested(device_name, branch, segment_delegate, latest_version, mode, crosswalk_type, test_platform):
                                update_device_config_dic[device_name]["no_update"] = 1
                    update_device_config_dic[device_name]["target_binary"]["version"] = latest_version
            else:
                assignments_dic = device_info_dic["assignments"]
                for id_iterm_seriels_key, info_dic in assignments_dic.iteritems():
                    target_binary_dic = info_dic["target_binary"]
                    version = target_binary_dic["version"]
                    branch = target_binary_dic["branch"]
                    rerun_flag = info_dic.get("rerun_flag", 0)
                    if version == "latest":
                        #branch = target_binary_dic["branch"]
                        if latest_version_dic.get(branch, None):
                            latest_version = latest_version_dic[branch]
                        else:
                            latest_version = get_latest_version(package_release_server_url, crosswalk_type, test_platform, branch)
                            latest_version_dic[branch] = latest_version
                        if latest_version == "error":
                            update_device_config_dic[device_name]["assignments"][id_iterm_seriels_key]["error_flag"] = 1
                        else:
                            #rerun_flag = info_dic.get("rerun_flag", 0)
                            if rerun_flag == 0:
                                mode = target_binary_dic["mode"]
                                segment_delegate = target_binary_dic["segment_list"][0]
                                if is_binary_tested(device_name, branch, segment_delegate, latest_version, mode, crosswalk_type, test_platform):
                                    update_device_config_dic[device_name]["assignments"][id_iterm_seriels_key]["no_update"] = 1
                        update_device_config_dic[device_name]["assignments"][id_iterm_seriels_key]["target_binary"]["version"] = latest_version
                    else:
                        if rerun_flag == 0:
                            mode = target_binary_dic["mode"]
                            segment_delegate = target_binary_dic["segment_list"][0]
                            if is_binary_tested(device_name, branch, segment_delegate, version, mode, crosswalk_type, test_platform):
                                update_device_config_dic[device_name]["assignments"][id_iterm_seriels_key]["no_update"] = 1

    create_folder(middle_tmp_dir)
    save_dic_json_file(update_device_config_dic, update_device_config_file)

    return update_device_config_dic


def get_tested_device_by_arch(dc_dic):
    nt_logger.debug("Call Function: 'get_tested_device_by_arch' with dc_dic(%s)" % dc_dic)
    tested_device = {}

    for device_name, device_info_dic in dc_dic.iteritems():
        device_arch = device_info_dic["device_arch"]
        if not tested_device.has_key(device_arch):
            tested_device[device_arch] = [device_name]
        else:
            tested_device[device_arch].append(device_name)

    return tested_device


def get_id_iterm_series_key(device_name, id_iterm):
    nt_logger.debug("Call Function: 'get_id_iterm_series_key' with device_name(%s), id_iterm(%s)" % (device_name, id_iterm))
    #return "id1,id2,..,idn"
    id_iterm_series_key = None
    key_list = device_config_dic[device_name]["assignments"].keys()

    for key in key_list:
        if key.find(id_iterm) != -1:
            id_iterm_series_key = key
            break

    return id_iterm_series_key


def get_download_orders_dic(dc_dic):
    nt_logger.debug("Call Function: 'get_download_orders_dic' with dc_dic(%s)" % dc_dic)
    #{
    #  "beta" : {
    #    "version": {
    #      "embedded": {
    #        "arm": ['crosswalk','cordova3.6','cordova4.x'],
    #        "arm64": ['crosswalk','cordova3.6','cordova4.x'],
    #        "x86": ['crosswalk','cordova3.6','cordova4.x'],
    #        "x86_64": ['crosswalk','cordova3.6','cordova4.x']
    #      },
    #      "shared": {
    #        "arm": ['crosswalk','cordova3.6','cordova4.x'],
    #        "arm64": ['crosswalk','cordova3.6','cordova4.x'],
    #        "x86": ['crosswalk','cordova3.6','cordova4.x'],
    #        "x86_64": ['crosswalk','cordova3.6','cordova4.x']
    #      }
    #    }
    #  }
    #}
    orders_dic = {}

    for device_name, device_info_dic in dc_dic.iteritems():
        arch = device_info_dic["device_arch"]
        if device_info_dic.has_key("target_binary"):
            target_binary_dic = device_info_dic["target_binary"]
            fill_download_orders_dic(arch, target_binary_dic, orders_dic)
        else:
            id_iterm_series_key_check = None
            device_id_list = device_info_dic.get("id_list", None)
            if not device_id_list:
                device_id_list = device_info_dic["assignments"].keys()
            for id_iterm in device_id_list:
                if device_info_dic["assignments"].get(id_iterm, None):
                    sub_target_binary_dic = device_info_dic["assignments"][id_iterm]["target_binary"]
                    fill_download_orders_dic(arch, sub_target_binary_dic, orders_dic)
                else:
                    id_iterm_series_key = get_id_iterm_series_key(device_name, id_iterm)
                    if id_iterm_series_key != id_iterm_series_key_check:
                        sub_target_binary_dic = device_info_dic["assignments"][id_iterm_series_key]["target_binary"]
                        fill_download_orders_dic(arch, sub_target_binary_dic, orders_dic)
                        id_iterm_series_key_check = id_iterm_series_key

    return orders_dic


def get_is_include_cordova_test(download_orders_dic):
    nt_logger.debug("Call Function: 'get_is_include_cordova_test' with download_orders_dic(%s)" % download_orders_dic)
    is_include_cordova_test = False

    for branch, version_dic in download_orders_dic.iteritems():
        for version, mode_dic in version_dic.iteritems():
            for mode, info_dic in mode_dic.iteritems():
                for arch, segment_list in info_dic.iteritems():
                    for segment in segment_list:
                        if segment.startswith("cordova"):
                            is_include_cordova_test = True
                            break

    return is_include_cordova_test


def get_actural_test_dic(spec_file):
    """According to spec file in device folder,
    make subset of the test_list.json,
    and reorganize all-in-one test if they do have."""

    nt_logger.debug("Call Function: 'generate_actural_test_dic' with spec_file(%s)" % spec_file)
    test_suite_list = get_test_list(spec_file)
    actural_test_dic = {}

    for ts in test_suite_list:
        ts_detail_dic = base_test_dic.get(ts, None)
        if ts_detail_dic:
            all_in_one_name = None
            if test_platform == "android":
                all_in_one_name = ts_detail_dic.get('all_in_one', None)
            if all_in_one_name:
                if actural_test_dic.has_key(all_in_one_name):
                    sub_dic = actural_test_dic[all_in_one_name]
                    sub_dic[ts] = ts_detail_dic
                else:
                    sub_dic = {}
                    sub_dic[ts] = ts_detail_dic
                    actural_test_dic[all_in_one_name] = sub_dic
            else:
                actural_test_dic[ts] = ts_detail_dic
        else:
            nt_logger.error("No such '%s' info in 'test_list.json', please configure it in 'test_list.json'." % ts)

    return actural_test_dic


def generate_actural_test_json(device_name):
    """Save test suites dic as actural_test_list.json in device folder."""
    nt_logger.debug("Call Function: 'generate_actural_test_json' with device_name(%s)" % device_name)
    spec_files = glob.glob("%s/%s/test_list.spec*" % (resources_dir, device_name))

    for spec_file in spec_files:
        actural_test_dic = get_actural_test_dic(spec_file)
        actural_test_list_file = "%s/%s/actural_%s" % (test_spec_dir, device_name, os.path.basename(spec_file))
        save_dic_json_file(actural_test_dic, actural_test_list_file)


def get_packages_url(spec_file_arch, url_type, packages_save_info_dic):
    nt_logger.debug("Call Function: 'get_packages_url' with spec_file_arch(%s), url_type(%s)" % (spec_file_arch, url_type))
    #packages_save_info_dic = {}
    spec_file = "%s/download_%s.spec" % (download_spec_dir, spec_file_arch)

    if url_type.find("cordova") != -1:
        spec_file = "%s/download_cordova_test.spec" % download_spec_dir

    url = "%s/%s" % (package_release_server_url, url_type)
    packages_url = []
    listen_page = get_listen_page(url)

    if listen_page:
        reobj = re.compile(obj_pattern)
        packages_url_infos = reobj.findall(listen_page)
        all_packages_url = [ os.path.join(url, i.split('href="')[1].split('">')[0]) for i in packages_url_infos ]
        if all_packages_url:
            actural_test_dic = get_actural_test_dic(spec_file)
            test_suite_list = actural_test_dic.keys()
            for ts in test_suite_list:
                exit_flag = False
                pacakge_name = None
                for package_url in all_packages_url:
                    if package_url.find(ts) != -1:
                        packages_url.append(package_url)
                        pacakge_name = package_url.split('/')[-1]
                        exit_flag = True
                        break
                if not exit_flag:
                    nt_logger.error("No package for '%s' on the '%s'" % (ts, url))
                else:
                    if packages_save_info_dic.has_key(ts):
                        packages_save_info_dic[ts][url_type] = pacakge_name
                    else:
                        tmp_dic = {}
                        tmp_dic[url_type] = pacakge_name
                        packages_save_info_dic[ts] = tmp_dic

    save_dic_json_file(packages_save_info_dic, packages_save_info_file)

    return packages_url


def is_packed_out(arch, url_type):
    nt_logger.debug("Call Function: 'is_packed_out' with arch(%s), url_type(%s)" % (arch, url_type))
    pack_done = False
    url = "%s/%s" % (package_release_server_url, url_type)
    sign_flag = "BUILD-INPROCESS"

    if arch.find("64") == 1:
        sign_flag = "BUILD-INPROCESS-64"

    flag_url = "%s/%s" % (url, sign_flag)
    bk_http_proxy = os.environ.get('http_proxy', None)
    os.environ['http_proxy'] = ''

    while True:
        try:
            urllib2.urlopen(flag_url)
        except urllib2.HTTPError:
            nt_logger.debug("Not find the sign '%s' on '%s', means pack done." % (sign_flag, url))
            pack_done = True
            break
        time.sleep(600)
        nt_logger.debug("Going on to monitor: '%s'" % flag_url)
        if int(time.strftime('%H', time.localtime(time.time()))) == 8:
            nt_logger.debug("It's time to finish monitor '%s'" % flag_url)
            break

    if bk_http_proxy:
        os.environ['http_proxy'] = bk_http_proxy

    return pack_done


def download_packages(save_dir, urls, branch, version):
    #download crosswalk, runtimelib, etc. binaries
    nt_logger.debug("Call Function: 'download_packages' with save_dir(%s), urls(%s), branch(%s), version(%s)" % (save_dir, urls, branch, version))
    download_binaries(package_release_server_url, branch, version, crosswalk_type, test_platform, crosswalk_release_server_url_internal, crosswalk_release_server_url)
    create_folder(save_dir)
    thread_list = []

    for url_item in urls:
        thread = threading.Thread(target=download, args=(save_dir, url_item))
        thread.start()
        thread_list.append(thread)

    for thread in thread_list:
        thread.join()


def prepare_packages():
    nt_logger.debug("Call Function: 'prepare_packages'")
    #{
    #  "beta" : {
    #    "version": {
    #      "embedded": {
    #        "arm": ['crosswalk','cordova3.6','cordova4.x'],
    #        "arm64": ['crosswalk','cordova3.6','cordova4.x'],
    #        "x86": ['crosswalk','cordova3.6','cordova4.x'],
    #        "x86_64": ['crosswalk','cordova3.6','cordova4.x']
    #      },
    #      "shared": {
    #        "arm": ['crosswalk','cordova3.6','cordova4.x'],
    #        "arm64": ['crosswalk','cordova3.6','cordova4.x'],
    #        "x86": ['crosswalk','cordova3.6','cordova4.x'],
    #        "x86_64": ['crosswalk','cordova3.6','cordova4.x']
    #      }
    #    }
    #  }
    #}

    nt_logger.debug("[%s] Start to download packages ..." % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))
    dc_dic = update_device_config_dic()
    download_orders_dic = get_download_orders_dic(dc_dic)
    tested_device = get_tested_device_by_arch(dc_dic)

    for arch, device_list in tested_device.iteritems():
        #1.1 Generate download_${arch}.spec
        generate_merged_download_spec(arch, device_list)
        #1.2 Generate actural_test_list.json(.partn)
        for device in device_list:
            generate_actural_test_json(device)

    if get_is_include_cordova_test(download_orders_dic):
        generate_download_cordova_test_spec()

    process_list = []
    packages_save_info_dic = {}

    for branch, branch_dic in download_orders_dic.iteritems():
        for version, version_dic in branch_dic.iteritems():
            if version == "error":
                nt_logger.error("No find the right version, skip download the packages of '%s/%s/%s'" % (crosswalk_type, test_platform, branch))
                continue
            for mode, mode_dic in version_dic.iteritems():
                for arch, segment_list in mode_dic.iteritems():
                    for segment in segment_list:
                        map_url_type = get_map_url_type(branch, version, segment, mode, arch, crosswalk_type, test_platform)
                        if not is_packed_out(arch, map_url_type):
                            nt_logger.error("Packages haven't been packed out, skip this test. You may trigger this NightlyAutoTest manually.")
                            continue
                        packages_url = get_packages_url(arch, map_url_type, packages_save_info_dic)
                        save_dir = "%s/%s" % (repo_dir, map_url_type)
                        process = multiprocessing.Process(target=download_packages, args=(save_dir, packages_url, branch, version))
                        process.start()
                        process_list.append(process)
            if test_platform == "windows":
                #download web sevice docroot resources for windows
                #http://jiaxxx-dev.sh.intel.com/ForNightlyAutoTest/android/master/20.50.530.0/testsuites-embedded/x86/webapi-service-docroot-tests-20.50.530.0-1.apk.zip
                docroot_file = "%s/%s/%s/%s/%s/docroot/webapi-service-docroot-tests-%s-1.apk.zip" % (repo_dir, crosswalk_type, test_platform, branch, version, version)
                if not os.path.exists(docroot_file):
                    docroot_file_url = "%s/%s/android/%s/%s/testsuites-embedded/x86/webapi-service-docroot-tests-%s-1.apk.zip" % (package_release_server_url, crosswalk_type, branch, version, version)
                    docroot_save_dir = "%s/%s/%s/%s/%s/docroot" % (repo_dir, crosswalk_type, test_platform, branch, version)
                    download_by_wget(docroot_file_url, docroot_save_dir)

    for process in process_list:
        process.join()

    nt_logger.debug("[%s] End to download packages ..." % time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()))


if __name__ == '__main__':
    prepare_packages()
