import copy
import json
import logging
import os
import urllib2
import re
import xml.etree.ElementTree as etree
import glob
from check_json import check

utility_module_path = os.path.dirname(os.path.abspath(__file__))
resources_dir_path = "%s/../../resources" % utility_module_path
device_config_file = "%s/device_config.json" % resources_dir_path
settings_file = "%s/settings.json" % resources_dir_path
tests_list_file = "%s/tests_list.json" % resources_dir_path
middle_tmp_dir_path = "%s/../../middle_tmp" % utility_module_path


check(device_config_file)
check(settings_file)
check(tests_list_file)


def get_json_dic(json_file):
    with open(json_file) as jf:
        json_dic = json.load(jf)

    return json_dic


def load():
    dc_dic = get_json_dic(device_config_file)
    s_dic = get_json_dic(settings_file)
    bt_dic = get_json_dic(tests_list_file)

    return dc_dic, s_dic, bt_dic


def get_nt_logger(vlevel):
    lg = logging.getLogger("CrosswalkNightlyTest")
    logging.basicConfig(level = getattr(logging, vlevel.upper()))
    return lg


device_config_dic, settings_dic, base_tests_dic = load()
log_level = settings_dic['log_level']
nt_logger = get_nt_logger(log_level)


def get_tested_devices_list():
    tested_devices_list = []

    for device_name, device_info_dic in device_config_dic.iteritems():
        if device_info_dic.get('is_tested', 0) == 1:
            tested_devices_list.append(device_name)


def fill_orders_dic(device_name, arch, src_dic, dist_dic):
    #print ">>>>> [%s] %s\n%s\n%s" % (device_name, arch, src_dic, dist_dic)
    branch = src_dic["branch"]
    mode = src_dic["mode"]
    version = src_dic["version"]

    if dist_dic.has_key(branch):
        branch_dic = dist_dic[branch]
        if branch_dic.has_key(version):
            version_dic = branch_dic[version]
            if version_dic.has_key(mode):
                mode_dic = version_dic[mode]
                if mode_dic.has_key(arch):
                    device_name_list = mode_dic[arch]
                    if device_name not in device_name_list:
                        device_name_list.append(device_name)
                else:
                    mode_dic[arch] = [device_name]
            else:
                tmp_mode_dic = {}
                tmp_mode_dic[arch] = [device_name]
                version_dic[mode] = tmp_mode_dic
        else:
            tmp_mode_dic = {}
            tmp_mode_dic[arch] = [device_name]
            tmp_version_dic = {}
            tmp_version_dic[mode] = tmp_mode_dic
            branch_dic[version] = tmp_version_dic
    else:
        tmp_mode_dic = {}
        tmp_mode_dic[arch] = [device_name]
        tmp_version_dic = {}
        tmp_version_dic[mode] = tmp_mode_dic
        tmp_branch_dic = {}
        tmp_branch_dic[version] = tmp_version_dic
        dist_dic[branch] = tmp_branch_dic


def get_orders_dic():
    #{
    #  "beta" : {
    #    "version": {
    #      "embedded": {
    #        "arm": ['DEVICE_NAME1','DEVICE_NAMEn']
    #        "arm64": ['DEVICE_NAME1','DEVICE_NAMEn']
    #        "x86": ['DEVICE_NAME1','DEVICE_NAMEn']
    #        "x86_64": ['DEVICE_NAME1','DEVICE_NAMEn']
    #      },
    #      "shared": {
    #        "arm": ['DEVICE_NAME1','DEVICE_NAMEn']
    #        "arm64": ['DEVICE_NAME1','DEVICE_NAMEn']
    #        "x86": ['DEVICE_NAME1','DEVICE_NAMEn']
    #        "x86_64": ['DEVICE_NAME1','DEVICE_NAMEn']
    #      }
    #    }
    #  }
    #}
    #TODO: One type device with multi numbers
    orders_dic = {}

    for device_name, device_info_dic in device_config_dic.iteritems():
        if device_info_dic.get('is_tested', 0) == 1:
            arch = device_info_dic["device_arch"]

            if device_info_dic.has_key("target_binary"):
                target_binary_dic = device_info_dic["target_binary"]
                fill_orders_dic(device_name, arch, target_binary_dic, orders_dic)
            else:
                device_id_list = device_info_dic["id_list"]
                for id_iterm in device_id_list:
                    sub_target_binary_dic = device_info_dic[id_iterm]["target_binary"]
                    fill_orders_dic(device_name, arch, sub_target_binary_dic, orders_dic)
    return orders_dic


dir_pattern = '\<img\ src=\"\/icons\/folder\.gif\"\ alt=\"\[DIR\]\"\>.*'


def get_latest_version(branch):
    url = "%s/%s/" % (settings_dic["Pack_Server_url"], branch.replace("canary", "master"))
    nt_logger.info("Listen URL: %s" % url)
    bk_http_proxy = os.environ.get('http_proxy', None)

    if bk_http_proxy:
        os.environ['http_proxy'] = ''

    try:
        listen_page = urllib2.urlopen(url)
    except Exception, e:
        nt_logger.error("ERROR! %s . Please check your network connect status." % e)
        return "error"

    content = listen_page.read()
    reobj = re.compile(dir_pattern)
    version_infos_list = reobj.findall(content)

    if not version_infos_list:
        nt_logger.error("Error! Fail to get Crosswalk \'%s\' latest version" % branch)
        return "error"
    else:
        latest_version_info = version_infos_list[-1]#-1
        latest_version = latest_version_info.split('/</a>')[0].split('>')[-1]

    if bk_http_proxy:
        os.environ['http_proxy'] = bk_http_proxy

    return latest_version


def update_orders_dic():
    base_orders_dic = get_orders_dic()
    update_orders_dic = copy.deepcopy(base_orders_dic)

    for branch, branch_dic in base_orders_dic.iteritems():
        if branch_dic.has_key("latest"):
            del update_orders_dic[branch]["latest"]
            back_up_version_dic = copy.deepcopy(branch_dic["latest"])
            version = get_latest_version(branch)
            update_orders_dic[branch][version] = back_up_version_dic

    base_orders_dic.clear()
    base_orders_dic = update_orders_dic

    return base_orders_dic


def save_dic_json_file(saved_dic, json_file):
    nt_logger.debug("[Function: save_dic_json_file]Save dic: \n%s\nas json_file(%s)." % (saved_dic, json_file))

    if os.path.isfile(json_file):
        os.remove(json_file)

    handle = open(json_file, "w")
    content = json.dumps(saved_dic, sort_keys = True, indent = 2)
    handle.write(content)
    handle.close()


def get_lines(file_name):
    lines_list = []

    if os.path.exists(file_name):
        with open(file_name) as sf:
            lines_list = sf.read().rstrip('\n').split('\n')
    else:
        nt_logger.error("ERROR! No such file: '%s'" % file_name)

    return lines_list


def get_tests_list(spec_file):
    nt_logger.debug("[Function: generate_actural_tests_list] spec_file(%s)" % spec_file)
    test_suites_list = get_lines(spec_file)

    return test_suites_list


def get_merged_test_suites_list(spec_files):
    merged_test_suites_list = []

    for file_item in spec_files:
        part_test_suites_list = get_lines(file_item)
        for test_suite in part_test_suites_list:
            if test_suite not in merged_test_suites_list:
                merged_test_suites_list.append(test_suite)

    return merged_test_suites_list



def merge_spec_parts(device_name):
    spec_parts_list = glob.glob("%s/%s/tests_list.spec.part*" % (resources_dir_path, device_name))
    merged_test_suites_list = []

    #Here suppose all part files have uniq test suites each.
    if spec_parts_list:
        merged_test_suites_list = get_merged_test_suites_list(spec_parts_list)
    else:
        merged_test_suites_list = get_lines("%s/%s/tests_list.spec" % (resources_dir_path, device_name))

    return merged_test_suites_list


def create_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    else:
        pass


def generate_spec_file(test_suites_list, file_name):
    test_suites_list.sort()

    with open(file_name, "w") as f:
        for test_suite in test_suites_list:
            f.write("%s\n" % test_suite)


def generate_merged_tests_spec(device_name):
    save_dir = "%s/tests_spec/%s" % (middle_tmp_dir_path, device_name)
    create_folder(save_dir)
    merged_spec_file = "%s/merged_tests_list.spec" % (save_dir)
    merged_test_suites_list = merge_spec_parts(device_name)
    generate_spec_file(merged_test_suites_list, merged_spec_file)


def generate_merged_download_spec(devices_list, branch, arch):
    download_spec_dir = "%s/download_spec/%s" % (middle_tmp_dir_path, branch)
    create_folder(download_spec_dir)
    download_spec_file = "%s/download_%s.spec" % (download_spec_dir, arch)
    merged_spec_files = ["%s/%s/merged_tests_list.spec" % (middle_tmp_dir_path, device) for device in devices_list]
    merged_download_test_suites_list = get_merged_test_suites_list(merged_spec_files)
    generate_spec_file(merged_download_test_suites_list, download_spec_file)


def get_actural_tests_dic(spec_file):
    """According to spec file in device folder,
    make subset of the tests_list.json,
    and reorganize all-in-one tests if they do have."""

    nt_logger.debug("[Function: generate_actural_tests_dic] spec_file(%s)" % spec_file)
    test_suites_list = get_tests_list(spec_file)
    actural_tests_dic = {}

    for ts in test_suites_list:
        ts_detail_dic = base_tests_dic[ts]
        all_in_one_name = ts_detail_dic.get('all_in_one', None)
        if all_in_one_name:
            if actural_tests_dic.has_key(all_in_one_name):
                sub_dic = actural_tests_dic[all_in_one_name]
                sub_dic[ts] = ts_detail_dic
            else:
                sub_dic = {}
                sub_dic[ts] = ts_detail_dic
                actural_tests_dic[all_in_one_name] = sub_dic
        else:
            actural_tests_dic[ts] = ts_detail_dic

    return actural_tests_dic


def generate_actural_tests_json(device_name, spec_file):
    """Save test suites dic as actural_tests_list.json in device folder."""
    actural_tests_dic = get_actural_tests_dic(spec_file)
    actural_tests_list_file = "%s/tests_spec/%s/actural_%s" % (middle_tmp_dir_path, device_name, os.path.basename(spec_file))
    save_dic_json_file(actural_tests_dic, actural_tests_list_file)


def generate_tests_xml(dir_path, test_name, output_dir):
    #TODO: optimize to merge if those test files have different sets
    nt_logger.debug("[Function: generate_tests_xml] dir_path(%s), test_name(%s), output_dir(%s)" % (dir_path, test_name, output_dir))
    file_list = glob.glob("%s/tests_v*.xml" % dir_path)
    file_list.sort()
    length = len(file_list)
    dist_file = '%s/%s.tests.xml' % (output_dir, test_name)

    if os.path.exists(dist_file):
        os.remove(dist_file)

    root = etree.parse(file_list[0]).getroot()
    suite_elem = root.find("suite")
    set_elem = suite_elem.find("set")

    for i in range(1, length):
        tmp_root = etree.parse(file_list[i]).getroot()
        tmp_set_elem = tmp_root.find("suite/set")
        tmp_tc_list = tmp_set_elem.getiterator("testcase")
        for tc in tmp_tc_list:
            set_elem.append(tc)

    with open(dist_file, 'w') as output:
        wtree = etree.ElementTree(element=root)
        wtree.write(output)


def get_set_list(xml_file):
    nt_logger.debug("[Function: get_set_list] xml_file(%s)" % xml_file)
    set_name_list = []

    try:
        root = etree.parse(xml_file)
        suite_node = root.find("suite")
        set_iter = suite_node.getiterator("set")

        for set_node in set_iter:
            if set_node.get("ui-auto") is not None:
                set_name = set_node.get("name")
                set_name_list.append(set_name)
    except Exception, e:
        nt_logger.error("[Function: get_set_list] has Exception: %s" % e)

    return set_name_list


def get_listen_page(url):
    nt_logger.debug("[Function: get_listen_page] url(%s)" % url)
    listen_page = None

    try:
        bk_http_proxy = os.environ.get('http_proxy', None)
        if bk_http_proxy:
            os.environ['http_proxy'] = ''
        listen_page = urllib2.urlopen(url).read()
        if bk_http_proxy:
            os.environ['http_proxy'] = bk_http_proxy
    except Exception,e:
        nt_logger.error("[Function: get_listen_page] has Exception: %s" % e)

    return listen_page


obj_pattern = 'alt=\"\[\   \]\".*'


def get_commit_id(url):
    nt_logger.debug("[Function: get_commit_id] url(%s)" % url)
    commit_id = "error commit id"

    listen_page = get_listen_page(url)

    if listen_page:
        #<td valign="top"><img src="/icons/unknown.gif" alt="[   ]"></td><td><a href="99b7ab34f6ee68082cf2c7e31c061acefa55bc10">99b7ab34f6ee68082cf2c7e31c061acefa55bc10</a></td>
        reobj = re.compile(obj_pattern)
        commit_id_info =  reobj.findall(listen_page)
        if commit_id_info:
            commit_id = commit_id_info[0].split('href="')[1].split('">')[0]

    return commit_id


def get_packages_url(spec_file, url):
    nt_logger.debug("[Function: get_packages_url] spec_file(%s), url(%s)" % (spec_file, url))
    packages_url = []

    listen_page = get_listen_page(url)

    if listen_page:
        reobj = re.compile(obj_pattern)
        packages_url_infos = reobj.findall(listen_page)

    all_packages_url = [ os.path.join(url, i.split('href="')[1].split('">')[0]) for i in packages_url_infos ]

    if all_packages_url:
        actural_tests_dic = get_actural_tests_dic(spec_file)
        test_suites_list = actural_tests_dic.keys()
        for ts in test_suites_list:
            exit_flag = False
            for package_url in all_packages_url:
                if package_url.find(ts) != -1:
                    packages_url.append(package_url)
                    exit_flag = True
                    break
            if not exit_flag:
                nt_logger.error("No package for '%s' on the '%s'" % (ts, url))

    return packages_url


#testsuites_dic = {
#   "apk": {
#       "embedded": "testsuites-embedded",
#       "shared": "testsuites-shared"
#   },
#   "cordova": {
#       "embedded": "cordova4.0-embedded",
#       "shared": "cordova4.0-shared"
#   },
#   "webview": {
#       "embedded": "testsuites-embedded",
#       "shared": "testsuites-shared"
#   }
#}
#
#devices_name_dic = {
#    "Google_Nexus_3": "arm-nexus3",
#    "Google_Nexus_4": "arm-nexus4",
#    "Google_Nexus_7": "arm-nexus7",
#    "ASUS_MeMO_Pad_8_K011": "x86-memo",
#    "Toshiba_Excite_Go_AT7-C8": "x86-toshiba",
#    "ZTE_Geek_V975": "x86-zte"
#}
#
#
#def get_arch_list():
#    arch_list = []
#    for device_name, device_details_dic in config_dic.iteritems():
#        if device_details_dic["device_os"] == "android":
#            device_arch = device_details_dic["device_arch"]
#            if device_arch not in arch_list:
#                arch_list.append(device_arch)
#
#    return arch_list
#
#
#key_test_specs_list = "test_specs_list"
#key_special_test_specs_list = "special_test_specs_list"
#key_webapi = "WebAPI"
#key_wrt = "WRT"
#key_bdd = "BDD" #TODO Should it be included in 'WebAPI' and 'WRT' ## TBD
#key_webapi_service_tests = "webapi-service-tests"
#key_webapi_noneservice_tests = "webapi-noneservice-tests"
#
#
#def merge_dic(dic, tmp_dic):
#    for key, value_dic in tmp_dic.iteritems():
#        if not dic.has_key(key):
#            dic[key] = value_dic
#        else:
#            dic[key] = merge_dic(dic[key], value_dic)
#
#    return dic
#
#
