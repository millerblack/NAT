import glob
import shutil
import os
import sys
sys.path.append("%s/../../util" % os.path.abspath(os.path.dirname(__file__)))
from ntcommon import *
import random
import commands


wrs_api = report_settings_dic["wrs_api"]
authtokens = report_settings_dic["authtokens"]


def print_usage():
    print """usage:
  python ntreport.py <result_dir>"""


def get_random_str():
    nt_logger.debug("Call Function: 'get_random_str'")
    seds = "abcdefghijklmnopqrstuvwxyz1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    rand_ceiling = len(seds) - 1
    random_str = ""

    for i in range(10):
        index = random.randint(0, rand_ceiling)
        random_str += seds[index]

    return random_str


def get_test_suite_name(file_name):
    nt_logger.debug("Call Function: 'get_test_suite_name' with file_name(%s)" % file_name)
    base_name = os.path.basename(file_name)
    test_suite_name = os.path.splitext(base_name)[0].split('result_')[1]

    return test_suite_name


def get_dist_dir_upload(test_suite_name, key):
    nt_logger.debug("Call Function: 'get_dist_dir_upload' with test_suite_name(%s), key(%s)" % (test_suite_name, key))
    catergory = base_test_dic[test_suite_name]["catergory"]
    dist_dir_upload = "%s/upload_xml/%s/%s" % (middle_tmp_dir, key, catergory)

    return dist_dir_upload


def sort_result_xml(result_dir, random_key):
    nt_logger.debug("Call Function: 'sort_result_xml' with result_dir(%s), random_key(%s)" % (result_dir, random_key))
    result_xml_list = glob.glob("%s/*.xml" % result_dir)

    for result_xml in result_xml_list:
        test_suite_name = get_test_suite_name(result_xml)
        dist_dir = get_dist_dir_upload(test_suite_name, random_key)
        create_folder(dist_dir)
        shutil.copy(result_xml, dist_dir)


def is_need_upload(result_file):
    nt_logger.debug("Call Function: 'is_need_upload' with result_file(%s)" % result_file)

    if result_file.endswith('.csv'):
        return True
    elif result_file.endswith('.xml'):
        cmd_get_test_number = 'grep -rn "actual_result" %s | wc -l' % result_file.replace(' ', '\ ')
        number = commands.getoutput(cmd_get_test_number)
        return int(number) > 0


def get_device_index_from_database(device_name, platform, arch, device_type, sdk_version):
    nt_logger.debug("Call Function: 'get_device_index_from_database' with device_name(%s), platform(%s), arch(%s), device_type(%s), sdk_version(%s)" % (device_name, platform, arch, device_type, sdk_version))
    #http POST http://wrs.sh.intel.com:8080/api/devices/  Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' name='ZTE Geek V975' platform='Android' arch='X86' type='phone' sdk='4.2.2' --timeout 3600 --ignore-stdin
    #post_cmd = "http POST %s/devices/  Authorization:' Token %s' name='%s' platform='%s' arch='%s' type='%s' sdk='%s' --timeout 3600 --ignore-stdin" % (wrs_api, authtokens, device_name.replace('_', ' '), platform.capitalize(), arch.upper().replace("X86", "IA"), device_type.capitalize(), sdk_version)
    post_cmd = """curl -d "name=%s&platform=%s&arch=%s&type=%s&sdk=%s" %s/devices/ -H 'Authorization: Token %s'""" % (device_name.replace('_', ' '), platform.capitalize(), arch, device_type.capitalize(), sdk_version, wrs_api, authtokens)
    #logger.debug("devices API: %s" % post_cmd)
    post_result = commands.getoutput(post_cmd).split('\n')[-1]
    #logger.debug("get_device_index_from_database: %s" % post_result)
    result_dic = eval(post_result.replace('null', '-1'))

    return result_dic['id']


def get_relevant_builds_01_index_from_database(segment, mode, arch):
    nt_logger.debug("Call Function: 'get_relevant_builds_01_index_from_database' with segment(%s), mode(%s), arch(%s) " % (segment, mode, arch))
    #http POST http://wrs.sh.intel.com:8080/api/relevant_builds_01/ Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' name='crosswalk' --timeout 3600 --ignore-stdin
    xw_type = ' '.join([x.capitalize() for x in crosswalk_type.split('-')])
    pack_mode = mode.capitalize()
    segment_name = "%s %s" % (pack_mode, xw_type)
    bit_suffix = '64bit'

    if arch.find('64') != -1:
        segment_name = "%s %s" % (segment_name, bit_suffix)

    if segment.find("cordova") != -1:
        middle_key = "WebView Plugin for"
        if segment.find("3.6") != -1:
            middle_key = "based"
        segment_name = "%s %s Cordova" % (segment_name, middle_key)

    #post_cmd = "http post %s/relevant_builds_01/ Authorization:' Token %s' name='%s' --timeout 3600 --ignore-stdin" % (wrs_api, authtokens, segment_name)
    post_cmd = """curl -d "name=%s" %s/relevant_builds_01/ -H 'Authorization: Token %s'""" % (segment_name, wrs_api, authtokens)
    #logger.debug("relevant_builds_01 API: %s" % post_cmd)
    post_result = commands.getoutput(post_cmd).split('\n')[-1]
    #logger.debug("get_relevant_builds_01_index_from_database: %s" % post_result)
    result_dic = eval(post_result.replace('null', '-1'))

    return result_dic['id']


def get_builds_index_from_database(main_version, target_branch, relevant_builds_01_index):
    nt_logger.debug("Call Function: 'get_builds_index_from_database' with main_version(%s), target_branch(%s), relevant_builds_01_index(%s)" % (main_version, target_branch, relevant_builds_01_index))
    #http POST http://wrs.sh.intel.com:8080/api/builds/ Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' mversion='13.41.390.0' branch='canary' relevant_builds_01=1 --timeout 3600 --ignore-stdin
    #post_cmd = "http POST %s/builds/ Authorization:' Token %s' mversion='%s' branch='%s' relevant_builds_01=%d --timeout 3600 --ignore-stdin" % (wrs_api, authtokens, main_version, target_branch.capitalize(), relevant_builds_01_index)
    post_cmd = """curl -d "mversion=%s&branch=%s&&relevant_builds_01=%s" %s/builds/ -H 'Authorization: Token %s'""" % (main_version, target_branch.capitalize(), relevant_builds_01_index, wrs_api, authtokens)
    #logger.debug("builds API: %s" % post_cmd)
    post_result = commands.getoutput(post_cmd).split('\n')[-1]
    #logger.debug("get_builds_index_from_database: %s" % post_result)
    result_dic = eval(post_result.replace('null', '-1'))

    return result_dic['id']


def get_relevant_reports_01_index_database(test_type):
    nt_logger.debug("Call Function: 'get_relevant_reports_01_index_database' with test_type(%s)" % test_type)
    #http POST http://wrs.sh.intel.com:8080/api/relevant_reports_01/ Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' name='nightly' --timeout 3600 --ignore-stdin
    #post_cmd = "http POST %s/relevant_reports_01/ Authorization:' Token %s' name='%s' --timeout 3600 --ignore-stdin" % (wrs_api, authtokens, type_name)
    post_cmd = """curl -d "name=%s" %s/relevant_reports_01/ -H 'Authorization: Token %s'""" % (test_type, wrs_api, authtokens)
    #logger.debug("relevant_reports_01 API: %s" % post_cmd)
    post_result = commands.getoutput(post_cmd).split('\n')[-1]
    #logger.debug("get_relevant_reports_01_index_database: %s" % post_result)
    result_dic = eval(post_result.replace('null', '-1'))

    return result_dic['id']


def get_relevant_reports_02_index_database(category):
    nt_logger.debug("Call Function: 'get_relevant_reports_02_index_database' with category(%s)" % category)
    #http POST http://wrs.sh.intel.com:8080/api/relevant_reports_02/ Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' name='webapi' --timeout 3600 --ignore-stdin
    #post_cmd = "http POST %s/relevant_reports_02/ Authorization:' Token %s' name='%s' --timeout 3600 --ignore-stdin" % (wrs_api, authtokens, cg)
    post_cmd = """curl -d "name=%s" %s/relevant_reports_02/ -H 'Authorization: Token %s'""" % (category, wrs_api, authtokens)
    #logger.debug("relevant_reports_02 API: %s" % post_cmd)
    post_result = commands.getoutput(post_cmd).split('\n')[-1]
    #logger.debug("get_relevant_reports_02_index_database %s" % post_result)
    result_dic = eval(post_result.replace('null', '-1'))

    return result_dic['id']


def record_report_link(save_dir, link):
    nt_logger.debug("Call Function: 'record_report_link' with save_dir(%s), link(%s)" % (save_dir, link))
    create_folder(save_dir)
    record_file = "%s/report_link.txt" % save_dir

    with open(record_file, "a") as f:
        f.writelines(link + '\n')


def upload(result_dir):
    nt_logger.debug("Call Function: 'upload' with result_dir(%s)" % result_dir)
    #'upload_config.json' in <result_dir> for easily manual-upload
    if not check_exists(result_dir):
        nt_logger.error("No such result dir: [%s]" % result_dir)
        return False
    elif not glob.glob("%s/*.xml" % result_dir):
        nt_logger.error("No such result file in: [%s]" % result_dir)
        return False

    xw_type = None
    platform = None
    segment = None
    binary_branch = None
    binary_version = None
    device_name = None
    device_arch = None
    device_type = None
    mode = None
    test_type = upload_type
    flag = "all"
    timestamp = time.strftime('%Y%m%d%H%M%S', time.localtime())
    upload_config_file = "%s/upload_config.json" % result_dir

    if os.path.isfile(upload_config_file):
        upload_config_dic = get_json_dic(upload_config_file)
        xw_type = upload_config_dic["xw_type"]
        platform = upload_config_dic["platform"]
        platform_version = upload_config_dic["%s_version" % platform]
        segment = upload_config_dic["segment"]
        binary_branch = upload_config_dic["binary_branch"]
        binary_version = upload_config_dic["binary_version"]
        device_name = upload_config_dic["device_name"]
        device_arch = upload_config_dic["device_arch"]
        device_type = upload_config_dic["device_type"]
        mode = upload_config_dic["mode"]
        test_type = upload_config_dic["upload_type"]
    else:
        child_path_list = result_dir.rstrip(os.path.sep).split(os.path.sep)
        flag = child_path_list[-1]
        timestamp = child_path_list[-2]
        binary_version = child_path_list[-3]
        mode = child_path_list[-4]
        device_name = child_path_list[-5]
        binary_branch = child_path_list[-6]
        segment = child_path_list[-7]
        platform = child_path_list[-8]
        platform_version = device_config_dic[device_name]["%s_version" % platform]
        xw_type = child_path_list[-9]
        device_arch = device_config_dic[device_name]["device_arch"]
        device_type = device_config_dic[device_name]["device_type"]

    binary_branch = binary_branch.replace('master', 'canary')
    bk_http_proxy = os.environ['http_proxy']
    os.environ['http_proxy'] = ''
    device_index = get_device_index_from_database(device_name, platform, device_arch, device_type, platform_version)
    relevant_builds_01_index = get_relevant_builds_01_index_from_database(segment, mode, device_arch)
    bk_binary_branch = binary_branch

    #For point one beta version as one stable version, and wrs needs show the branch
    if device_config_dic[device_name].has_key("wrs_branch"):
        binary_branch = device_config_dic[device_name]["wrs_branch"]

    builds_index = get_builds_index_from_database(binary_version, binary_branch, relevant_builds_01_index)
    relevant_reports_01_index = get_relevant_reports_01_index_database(test_type)
    binary_branch = bk_binary_branch
    details_info = ''
    details_info_list = []
    url = "%s/%s/%s/%s/%s" % (settings_dic["package_release_server_url"], xw_type, platform, binary_branch.replace('canary', 'master'), binary_version)
    commit_id = get_commit_id(url)
    test_env_infos_dic = settings_dic["test_env_infos"]

    for key, value in test_env_infos_dic.iteritems():
        if key == "Commit ID":
            value = commit_id
        env_item = '%s: %s' % (key, value)
        details_info_list.append(env_item)

    details_info = ';'.join(details_info_list)
    random_key = get_random_str()
    sort_result_xml(result_dir, random_key)
    catergory_list = os.listdir("%s/upload_xml/%s" % (middle_tmp_dir, random_key))
    catergory_list.sort()

    for test_catergory in catergory_list:
        catergory_dir = "%s/upload_xml/%s/%s" % (middle_tmp_dir, random_key, test_catergory)
        result_file_list = glob.glob("%s/*.xml" % catergory_dir)
        report_result_list = []
        result_file_list.sort()
        for result_file in result_file_list:
            if is_need_upload(result_file):
                #report_result_list.append('files@%s' % result_file_path)
                report_result_list.append('-F files=@%s' % result_file.replace(' ', '\ '))
        if report_result_list:
            relevant_reports_02_index = get_relevant_reports_02_index_database(test_catergory)
            #http -f POST http://wrs.sh.intel.com:8080/api/reports/ Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' files@/home/otcqa/Documents/test_result/result_tct-webstorage-w3c-tests.xml build=2 device=3 relevant_reports_01=1 relevant_reports_02=2  --timeout 3600 --ignore-stdin
            upload_cmd = """curl %s -F build=%s -F device=%s -F relevant_reports_01=%s -F relevant_reports_02=%s -F details='%s' -F summary=Summary %s/reports/ -H 'Authorization: Token %s'""" % (' '.join(report_result_list), builds_index, device_index, relevant_reports_01_index, relevant_reports_02_index, details_info, wrs_api, authtokens)
            #logger.debug("reports API: %s" % upload_cmd)
            upload_result = commands.getoutput(upload_cmd).split('\n')[-1]
            #logger.debug("upload result infos: %s" % upload_result)
            result_dic = eval(upload_result.replace('null', '-1'))
            #check report record whether exists, if existed, execute put cmd to update report
            if result_dic.get("error_message", None) == 'The report record is already exists.':
                report_id = result_dic["report"]["id"]
                #update_report_cmd = "http -f PUT %s/reports/%s/ Authorization:' Token %s' %s build=%d device=%d relevant_reports_01=%d relevant_reports_02=%d details='details' summary='Summary' --timeout 3600 --ignore-stdin" % (wrs_api, report_id, authtokens, ' '.join(report_result_list), builds_index, device_index, relevant_reports_01_index, relevant_reports_02_index)
                update_report_cmd = """curl -X PUT %s -F build=%s -F device=%s -F relevant_reports_01=%s -F relevant_reports_02=%s -F details='%s' -F summary=Summary %s/reports/%s/ -H 'Authorization: Token %s'""" % (' '.join(report_result_list), builds_index, device_index, relevant_reports_01_index, relevant_reports_02_index, details_info, wrs_api, report_id, authtokens)
                #update_report_result = commands.getoutput(update_report_cmd)
                update_report_result = commands.getoutput(update_report_cmd).split('\n')[-1]
                result_dic = eval(update_report_result.replace('null', '-1'))
            save_link_dir = "%s/%s/%s/%s/%s" % (upload_log_dir, device_name, binary_version, timestamp, flag)
            if result_dic.get("report", None):
                report_link = "%s/reports/%s" % (wrs_api, result_dic["report"]["id"])
                report_link = report_link.replace('api/','')
                record_report_link(save_link_dir, report_link)
            #handle upload result and save report id
            upload_log_save_dir = "%s/%s" % (save_link_dir, segment)
            create_folder(upload_log_save_dir)
            upload_log_file = "%s/%s.txt" % (upload_log_save_dir, test_catergory)
            save_dic_json_file(result_dic, upload_log_file)

    #logger.info("Finish upload report.")
    os.environ['http_proxy'] = bk_http_proxy

    return True


if __name__ == '__main__':
    argv_len = len(sys.argv)

    if argv_len != 2:
        print_usage()
        sys.exit(-1)

    result_dir = sys.argv[1]
    status = upload(result_dir)
    print "Upload report status: [%s]." % status
