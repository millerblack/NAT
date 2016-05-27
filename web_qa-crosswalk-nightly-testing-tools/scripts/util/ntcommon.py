import copy
import json
import os
import urllib2
import re
import xml.etree.ElementTree as etree
import glob
import shutil
import urlparse
import time
import logging
import ConfigParser
import socket


util_module_path = os.path.dirname(os.path.abspath(__file__))
repo_dir = "%s/../../repo" % util_module_path
resources_dir = "%s/../../resources" % util_module_path
scripts_dir = "%s/../../scripts" % util_module_path
device_config_file = "%s/device_config.json" % resources_dir
settings_file = "%s/settings.json" % resources_dir
test_list_file = "%s/test_list.json" % resources_dir
cordova_test_spec = "%s/cordova_test_list.spec" % resources_dir
middle_tmp_dir = "%s/../../middle_tmp" % util_module_path
update_device_config_file = "%s/update_device_config.json" % middle_tmp_dir
packages_save_info_file = "%s/packages_save_info.json" % middle_tmp_dir
test_result_dir = "%s/../../test-result" % util_module_path
upload_log_dir = "%s/../../upload-log" % util_module_path
download_spec_dir = "%s/download_spec" % middle_tmp_dir
test_spec_dir = "%s/test_spec" % middle_tmp_dir
aio_test_suite_list = ["webapi-noneservice-tests", "webapi-service-tests"]
unneed_install_test_suite_list = [
    "wrt-manifest-android-tests",
    "wrt-manifest2-android-tests"]
comm_module_dic = {
    "android": "androidmobile",
    "windows": "windowshttp"
}


def check(json_file):
    file_name = os.path.basename(json_file)

    try:
        with open(json_file) as jf:
            json.load(jf)
        print "Check '%s'\t ... [OK]" % file_name
    except Exception, e:
        print "Check '%s'\t ... [FAIL] --- Exception: %s" % (file_name, e)


def get_json_dic(json_file):
    with open(json_file) as jf:
        json_dic = json.load(jf)

    return json_dic


check(device_config_file)
check(settings_file)
check(test_list_file)


def load():
    dc_dic = get_json_dic(device_config_file)
    s_dic = get_json_dic(settings_file)
    bt_dic = get_json_dic(test_list_file)

    return dc_dic, s_dic, bt_dic


def get_nt_logger(vlevel):
    lg = logging.getLogger("CrosswalkNightlyTest")
    logging.basicConfig(level = getattr(logging, vlevel.upper()))
    return lg


device_config_dic, settings_dic, base_test_dic = load()

log_level = settings_dic['log_level']
nt_logger = get_nt_logger(log_level)

package_release_server_url = settings_dic["package_release_server_url"]
crosswalk_release_server_url = settings_dic["crosswalk_release_server_url"]
crosswalk_release_server_url_internal = settings_dic["crosswalk_release_server_url_internal"]
crosswalk_type = settings_dic["crosswalk_type"]#TODO:upgrade together with QiuZong
test_platform = settings_dic["test_platform"]
xwalkdriver_path = settings_dic["xwalkdriver_path"]
is_webdriver = settings_dic["is_webdriver"]
open_source_projects_dir = settings_dic["open_source_projects_dir"]
data_conf_platform_dic = settings_dic["data_conf_platform_dic"]
is_upload_report = settings_dic["is_upload_report"]
upload_type = settings_dic["upload_type"]
report_settings_dic = settings_dic["report_settings"]
mail_settings_dic = settings_dic["mail_settings"]
domain_name = settings_dic["domain_name"]
test_suite_categories_list = settings_dic["test_suite_categories"]
tinyweb_docroot_path = settings_dic["tinyweb_docroot_path"]
tinyweb_path = settings_dic["tinyweb_path"]

dir_pattern = '\<img\ src=\"\/icons\/folder\.gif\"\ alt=\"\[DIR\]\"\>.*'


def get_latest_version(server_url, vcrosswalk_type, vtest_platform, branch):
    nt_logger.debug("Call Function: 'get_latest_version' with server_url(%s), vcrosswalk_type(%s), vtest_platform(%s), branch(%s)" % (server_url, vcrosswalk_type, vtest_platform, branch))
    url = "%s/%s/%s/%s/" % (server_url, vcrosswalk_type, vtest_platform, branch.replace("canary", "master"))
    nt_logger.debug("Listened URL: %s" % url)
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
        latest_version_info = version_infos_list[-1]
        latest_version = latest_version_info.split('/</a>')[0].split('>')[-1]

    if bk_http_proxy:
        os.environ['http_proxy'] = bk_http_proxy

    nt_logger.debug("Latest version of '%s' is [%s]" % (url, latest_version))

    return latest_version


def check_exists(path):
    nt_logger.debug("Call Function: 'check_exists' with path(%s)" % path)

    return os.path.exists(path)


def is_binary_tested(device_name, branch, segment_delegate, latest_version, mode, vcrosswalk_type, vtest_platform):
    nt_logger.debug("Call Function: 'is_binary_tested' with device_name(%s), branch(%s), segment_delegate(%s), latest_version(%s), mode(%s), vcrosswalk_type(%s), vtest_platform(%s)" % (device_name, branch, segment_delegate, latest_version, mode, vcrosswalk_type, vtest_platform))
    #return value: True: already tested, False: not tested
    #final_test_result_dir likes test_result/crosswalk/android/crosswalk/master/ASUS_MeMO_Pad_8_K011/shared/18.46.470.0/20160122113
    dst_result_dir = "%s/%s/%s/%s/%s/%s/%s/%s" % (test_result_dir, vcrosswalk_type, vtest_platform, segment_delegate, branch, device_name, mode, latest_version)
    nt_logger.debug("By checking whether the path '%s' exists, to justify whether the binary of '%s-%s-%s-%s' has been tested." % (dst_result_dir, vcrosswalk_type, branch, mode, latest_version))

    return check_exists(dst_result_dir)


def fill_download_orders_dic(arch, src_dic, dst_dic):
    nt_logger.debug("Call Function: 'fill_download_orders_dic' with arch(%s), src_dic(%s), dst_dic(%s)" % (arch, src_dic, dst_dic))
    branch = src_dic["branch"]
    mode = src_dic["mode"]
    version = src_dic["version"]
    segment_list = src_dic["segment_list"]

    if dst_dic.has_key(branch):
        branch_dic = dst_dic[branch]
        if branch_dic.has_key(version):
            version_dic = branch_dic[version]
            if version_dic.has_key(mode):
                mode_dic = version_dic[mode]
                if mode_dic.has_key(arch):
                    new_segment_list = mode_dic[arch]
                    for segment in segment_list:
                        if segment not in new_segment_list:
                            new_segment_list.append(segment)
                else:
                    mode_dic[arch] = copy.deepcopy(segment_list)
            else:
                tmp_mode_dic = {}
                tmp_mode_dic[arch] = copy.deepcopy(segment_list)
                version_dic[mode] = tmp_mode_dic
        else:
            tmp_mode_dic = {}
            tmp_mode_dic[arch] = copy.deepcopy(segment_list)
            tmp_version_dic = {}
            tmp_version_dic[mode] = tmp_mode_dic
            branch_dic[version] = tmp_version_dic
    else:
        tmp_mode_dic = {}
        tmp_mode_dic[arch] = copy.deepcopy(segment_list)
        tmp_version_dic = {}
        tmp_version_dic[mode] = tmp_mode_dic
        tmp_branch_dic = {}
        tmp_branch_dic[version] = tmp_version_dic
        dst_dic[branch] = tmp_branch_dic


def save_dic_json_file(saved_dic, json_file):
    nt_logger.debug("Call Function: 'save_dic_json_file' with saved_dic(%s), json_file(%s)" % (saved_dic, json_file))
    if os.path.isfile(json_file):
        os.remove(json_file)

    handle = open(json_file, "w")
    content = json.dumps(saved_dic, sort_keys = True, indent = 2)
    handle.write(content)
    handle.close()


def get_lines(file_name):
    nt_logger.debug("Call Function: 'get_lines' with file_name(%s)" % file_name)
    lines_list = []

    if os.path.exists(file_name):
        with open(file_name) as sf:
            lines_list = sf.read().rstrip('\n').split('\n')
    else:
        nt_logger.error("ERROR! No such file: '%s'" % file_name)

    return lines_list


def get_test_list(spec_file):
    nt_logger.debug("Call Function: 'get_test_list' with spec_file(%s)" % spec_file)
    test_suite_list = get_lines(spec_file)

    return test_suite_list


def get_merged_test_suite_list(spec_files):
    nt_logger.debug("Call Function: 'get_merged_test_suite_list' with spec_files(%s)" % spec_files)
    merged_test_suite_list = []

    for file_item in spec_files:
        part_test_suite_list = get_lines(file_item)
        for test_suite in part_test_suite_list:
            if test_suite not in merged_test_suite_list:
                merged_test_suite_list.append(test_suite)

    return merged_test_suite_list


def merge_spec_parts(device_name):
    nt_logger.debug("Call Function: 'merge_spec_parts' with device_name(%s)" % device_name)
    spec_parts_list = glob.glob("%s/%s/test_list.spec.part*" % (resources_dir, device_name))
    merged_test_suite_list = []

    if spec_parts_list:
        merged_test_suite_list = get_merged_test_suite_list(spec_parts_list)
    else:
        merged_test_suite_list = get_lines("%s/%s/test_list.spec" % (resources_dir, device_name))

    return merged_test_suite_list


def create_folder(folder_name):
    nt_logger.debug("Call Function: 'create_folder' with folder_name(%s)" % folder_name)
    time.sleep(1)

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    else:
        pass


def generate_spec_file(test_suite_list, file_name):
    nt_logger.debug("Call Function: 'generate_spec_file' with test_suite_list(%s), file_name(%s)" % (test_suite_list, file_name))
    test_suite_list.sort()

    with open(file_name, "w") as f:
        for test_suite in test_suite_list:
            f.write("%s\n" % test_suite)


def generate_merged_test_spec(device_name):
    nt_logger.debug("Call Function: 'generate_merged_test_spec' with device_name(%s)" % device_name)
    save_dir = "%s/%s" % (test_spec_dir, device_name)
    create_folder(save_dir)
    merged_spec_file = "%s/merged_test_list.spec" % (save_dir)
    merged_test_suite_list = merge_spec_parts(device_name)
    generate_spec_file(merged_test_suite_list, merged_spec_file)


def generate_download_cordova_test_spec():
    nt_logger.debug("Call Function: 'generate_download_cordova_test_spec'")
    download_cordova_test_spec = "%s/download_cordova_test.spec" % download_spec_dir
    create_folder(download_spec_dir)
    shutil.copy(cordova_test_spec, download_cordova_test_spec)


def generate_merged_download_spec(arch, device_list):
    nt_logger.debug("Call Function: 'generate_merged_download_spec' with arch(%s), device_list(%s)" % (arch, device_list))
    #Regardless of "branch" & "version" & "mode", the test scope is up to "arch".
    create_folder(download_spec_dir)
    download_spec_file = "%s/download_%s.spec" % (download_spec_dir, arch)
    merged_spec_files = []

    for device in device_list:
        generate_merged_test_spec(device)
        merged_test_list_spec = "%s/%s/merged_test_list.spec" % (test_spec_dir, device)
        merged_spec_files.append(merged_test_list_spec)

    merged_download_test_suite_list = get_merged_test_suite_list(merged_spec_files)
    generate_spec_file(merged_download_test_suite_list, download_spec_file)


def generate_test_xml(dir_path, test_name, output_dir):
    nt_logger.debug("Call Function: 'generate_test_xml' with dir_path(%s), test_name(%s), output_dir(%s)" % (dir_path, test_name, output_dir))
    #TODO: optimize to merge if those test files have different sets
    file_list = glob.glob("%s/tests_v*.xml" % dir_path)
    file_list.sort()
    length = len(file_list)
    #dst_file = '%s/%s.tests.xml' % (output_dir, test_name)
    dst_file = '%s/tests.xml' % output_dir

    if os.path.exists(dst_file):
        os.remove(dst_file)

    root = etree.parse(file_list[0]).getroot()
    suite_elem = root.find("suite")
    set_elem = suite_elem.find("set")

    for i in range(1, length):
        tmp_root = etree.parse(file_list[i]).getroot()
        tmp_set_elem = tmp_root.find("suite/set")
        tmp_tc_list = tmp_set_elem.getiterator("testcase")
        for tc in tmp_tc_list:
            set_elem.append(tc)

    with open(dst_file, 'w') as output:
        wtree = etree.ElementTree(element=root)
        wtree.write(output)


def get_set_list(xml_file):
    nt_logger.debug("Call Function: 'get_set_list' with xml_file(%s)" % xml_file)
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
        nt_logger.error("Function: 'get_set_list' has Exception: %s" % e)

    return set_name_list


def get_listen_page(url):
    nt_logger.debug("Call Function: 'get_listen_page' with url(%s)" % url)
    listen_page = None

    try:
        bk_http_proxy = os.environ.get('http_proxy', None)
        if bk_http_proxy:
            os.environ['http_proxy'] = ''
        listen_page = urllib2.urlopen(url).read()
        if bk_http_proxy:
            os.environ['http_proxy'] = bk_http_proxy
    except Exception,e:
        nt_logger.error("Function: 'get_listen_page' has Exception: %s" % e)

    return listen_page


obj_pattern = 'alt=\"\[\   \]\".*'


def get_commit_id(url):
    nt_logger.debug("Call Function: 'get_commit_id' with url(%s)" % url)
    error_commit_id = "error commit id"
    commit_id_length = 40
    listen_page = get_listen_page(url)

    if listen_page:
        #<td valign="top"><img src="/icons/unknown.gif" alt="[   ]"></td><td><a href="99b7ab34f6ee68082cf2c7e31c061acefa55bc10">99b7ab34f6ee68082cf2c7e31c061acefa55bc10</a></td>
        reobj = re.compile(obj_pattern)
        commit_id_info =  reobj.findall(listen_page)
        if commit_id_info:
            length = len(commit_id_info)
            for i in range(0, length):
                commit_id = commit_id_info[i].split('href="')[1].split('">')[0]
                if len(commit_id) == 40:
                    return commit_id

    nt_logger.error("No such commit-id on '%s'" % url)
    return error_commit_id


def get_map_url_type(branch, version, segment, mode, arch, vcrosswalk_type, vtest_platform):
    nt_logger.debug("Call Function: 'get_map_url_type' with branch(%s), version(%s), segment(%s), mode(%s), arch(%s), vcrosswalk_type(%s), vtest_platform(%s)" % (branch, version, segment, mode, arch, vcrosswalk_type, vtest_platform))
    map_url_type = "%s/%s/%s/%s" % (vcrosswalk_type, vtest_platform, branch.replace("canary", "master"), version)

    if vtest_platform == "android":
        map_url_type += "/%s-%s/%s" % (segment.replace("crosswalk", "testsuites"), mode, arch)

    return map_url_type


def get_cut_dirs_num(url):
    nt_logger.debug("Call Function: 'get_cut_dirs_num' with url(%s)" % url)
    components = urlparse.urlparse(url.rstrip('/'))
    cut_dirs_num = components.path.count('/')

    return cut_dirs_num


def download_by_wget(url, save_dir, obj_type=0, no_proxy_flag=True):
    nt_logger.debug("Call Function: 'download_by_wget' with url(%s), save_dir(%s), obj_type(%d), no_proxy_flag(%s)" % (url, save_dir, obj_type, no_proxy_flag))
    #obj_type: 0 file, 1 folder
    components = urlparse.urlparse(url.rstrip('/'))
    target_obj = "%s/%s" % (save_dir, components.path.split('/')[-1])

    if obj_type == 1:
       target_obj = save_dir

    if not check_exists(target_obj):
        nt_logger.debug("Now downloading [%s] as '%s'" % (url, target_obj))
        if obj_type == 0:
            wget_cmd = "wget -q %s --no-check-certificate -P %s" % (url, save_dir)
        elif obj_type == 1:
            cut_dirs_num = get_cut_dirs_num(url)
            wget_cmd = "wget -q -r -np -nH --no-check-certificate --cut-dirs=%d %s -A zip,apk,aar,txt -P %s" % (cut_dirs_num, url, save_dir)
        if no_proxy_flag:
            wget_cmd += " --no-proxy"
        os.system(wget_cmd)
    else:
        nt_logger.debug("[%s] has already been downloaded, exists as '%s'" % (url, target_obj))


#def download(save_dir, url, method="wget"):
def download(save_dir, url):
    """Use default wget to download packages"""
    nt_logger.debug("Call Function: 'download' with save_dir(%s), url(%s)" % (save_dir, url))
    download_by_wget(url, save_dir)

    if url.find("webapi-service-tests") != -1:
        #TODO: Optimize by saving html file as local file, and search the docroot package's name, currently, hard code
        docroot_url = url.replace("webapi-service-tests", "webapi-service-docroot-tests").replace("3.6", "1")
        download_by_wget(docroot_url, save_dir)
    elif url.find("wrt-manifest-android-tests") != -1:
        #download "apks-manifest" folder
        manifest_folder_url = "%s/apks-manifest/apks/%s/" % (url[:url.rstrip('/').rfind('/')], url.rstrip('/').split('/')[-2])
        download_by_wget(manifest_folder_url, "%s/apks-manifest/apks/%s" % (save_dir, url.rstrip('/').split('/')[-2]), 1)
    elif url.find("wrt-packertool-android-tests") != -1:
        #download "apks-packertool" folder
        packertool_folder_url = "%s/apks-packertool/apks/%s/" % (url[:url.rstrip('/').rfind('/')], url.rstrip('/').split('/')[-2])
        download_by_wget(packertool_folder_url, "%s/apks-packertool/apks/%s" % (save_dir, url.rstrip('/').split('/')[-2]), 1)


def download_binaries(package_server_url, branch, version, vcrosswalk_type, vtest_platform, bk_crosswalk_server_url_1, bk_crosswalk_server_url_2):
    nt_logger.debug("Call Function: 'download_binaries' with package_server_url(%s), branch(%s), version(%s), vcrosswalk_type(%s), vtest_platform(%s), bk_crosswalk_server_url_1(%s), bk_crosswalk_server_url_2(%s)" % (package_server_url, branch, version, vcrosswalk_type, vtest_platform, bk_crosswalk_server_url_1, bk_crosswalk_server_url_2))
    binaries_url = "%s/%s/%s/%s/%s/crosswalk-tools/" % (package_server_url, vcrosswalk_type, vtest_platform, branch, version) #binaries_url should be ended with '/' for wget cmd
    binaries_dir = "%s/%s/%s/%s/%s/crosswalk-tools" % (repo_dir, vcrosswalk_type, vtest_platform, branch, version)
    no_proxy_flag = True

    if not get_listen_page(binaries_url):
        #2nd reserve solution from crosswalk_release_server(internal)
        nt_logger.error("No such '%s', switch to download from '%s'" % (binaries_url, bk_crosswalk_server_url_1))
        binaries_url = "%s/%s/%s/%s/%s/" % (bk_crosswalk_server_url_1, vcrosswalk_type, vtest_platform, branch.replace("master", "canary"), version)
        if not get_listen_page(binaries_url):
            #3rd reserve solution from crosswalk_release_server
            binaries_url = "%s/%s/%s/%s/%s/" % (bk_crosswalk_server_url_2, vcrosswalk_type, vtest_platform, branch.replace("master", "canary"), version)
            no_proxy_flag = False

    download_by_wget(binaries_url, binaries_dir, 1, no_proxy_flag)


def get_test_list_dic(device_name, flag):
    nt_logger.debug("Call Function: 'get_test_list_dic' with device_name(%s), flag(%s)" % (device_name, flag))
    file_name = "actural_test_list.spec"

    if flag.startswith("part"):
        file_name = "%s.%s" % (file_name, flag)

    spec_file = "%s/%s/%s" % (test_spec_dir, device_name, file_name)
    test_list_dic = get_json_dic(spec_file)

    return test_list_dic


def update_config_file(file_name, section, option, value):
    nt_logger.debug("Call Function: 'update_config_file' with file_name(%s), section(%s), option(%s), value(%s)" % (file_name, section, option, value))

    if os.path.isfile(file_name):
        conf = ConfigParser.ConfigParser()
        conf.read(file_name)
        conf.set(section, option, value)
        conf.write(open(file_name, "w"))
    else:
        nt_logger.error("No such config file:'%s', fail to update" % file_name)


def get_host_name():
    return socket.gethostname()


def get_host_ip():
    host_name = get_host_name()
    host_ip = None

    try:
       host_ip = socket.gethostbyname_ex("%s%s" % (host_name,domain_name))[2][0]
    except Exception, e:
       print "Error [%s] happened when get host ip address, now switch to use the host_ip info in settings.json" % e
       host_ip = settings_dic["host_ip"]

    return host_ip
