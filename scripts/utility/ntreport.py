import commands
import os
import sys
import time
import common

logger = common.nt_logger
settings_dic = common.settings_dic
config_dic = common.device_config_dic
report_settings_dic = settings_dic["report_settings"]
wrs_api = report_settings_dic["wrs_api"]
authtokens = report_settings_dic["authtokens"]
auto_pack_packages = settings_dic["auto_pack_packages"]


def print_usage():
    print """usage:
  python QAReport.py <device_name> <result_dir>"""


def is_need_upload(result_file):
    if result_file.endswith('.csv'):
        return True
    elif result_file.endswith('.xml'):
        cmd_get_test_number = 'grep -rn "actual_result" %s | wc -l' % result_file
        number = commands.getoutput(cmd_get_test_number)
        return int(number) > 0


def get_device_index_from_database(device_name, platform, arch, device_type, sdk_version):
    #http POST http://wrs.sh.intel.com:8080/api/devices/  Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' name='ZTE Geek V975' platform='Android' arch='X86' type='phone' sdk='4.2.2' --timeout 3600 --ignore-stdin
    #post_cmd = "http POST %s/devices/  Authorization:' Token %s' name='%s' platform='%s' arch='%s' type='%s' sdk='%s' --timeout 3600 --ignore-stdin" % (wrs_api, authtokens, device_name.replace('_', ' '), platform.capitalize(), arch.upper().replace("X86", "IA"), device_type.capitalize(), sdk_version)
    post_cmd = """curl -d "name=%s&platform=%s&arch=%s&type=%s&sdk=%s" %s/devices/ -H 'Authorization: Token %s'""" % (device_name.replace('_', ' '), platform.capitalize(), arch.upper().replace("X86", "IA"), device_type.capitalize(), sdk_version, wrs_api, authtokens)
    logger.debug("devices API: %s" % post_cmd)
    post_result = commands.getoutput(post_cmd).split('\n')[-1]
    logger.debug("get_device_index_from_database: %s" % post_result)
    result_dic = eval(post_result.replace('null', '-1'))
    return result_dic['id']


def get_relevant_builds_01_index_from_database(scope_name):
    #http POST http://wrs.sh.intel.com:8080/api/relevant_builds_01/ Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' name='crosswalk' --timeout 3600 --ignore-stdin
    pack_mode = settings_dic['pack_mode'].capitalize()
    cordova_version_value = settings_dic['cordova_version']
    lite_64bit = settings_dic['lite_64bit']
    type_dic = {
        0: "",
        1: " Lite",
        2: " 64bit"
    }
    cordova_version_dic = {
        "4.0": " 4.0",
        "3.6": ""
    }
    type_value = type_dic[lite_64bit]
    cordova_version = cordova_version_dic[cordova_version_value]
    segment_name = ''
    if scope_name == "cordova":
        segment_name = "%s Crosswalk%s WebView Plugin for Cordova%s" % (pack_mode, type_value, cordova_version)
    else:
        segment_name = "%s Crosswalk%s" % (pack_mode, type_value)

    #post_cmd = "http post %s/relevant_builds_01/ Authorization:' Token %s' name='%s' --timeout 3600 --ignore-stdin" % (wrs_api, authtokens, segment_name)
    post_cmd = """curl -d "name=%s" %s/relevant_builds_01/ -H 'Authorization: Token %s'""" % (segment_name, wrs_api, authtokens)
    logger.debug("relevant_builds_01 API: %s" % post_cmd)
    post_result = commands.getoutput(post_cmd).split('\n')[-1]
    logger.debug("get_relevant_builds_01_index_from_database: %s" % post_result)
    result_dic = eval(post_result.replace('null', '-1'))
    return result_dic['id']


def get_builds_index_from_database(main_version, target_branch, relevant_builds_01_index):
    #http POST http://wrs.sh.intel.com:8080/api/builds/ Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' mversion='13.41.390.0' branch='canary' relevant_builds_01=1 --timeout 3600 --ignore-stdin
    #post_cmd = "http POST %s/builds/ Authorization:' Token %s' mversion='%s' branch='%s' relevant_builds_01=%d --timeout 3600 --ignore-stdin" % (wrs_api, authtokens, main_version, target_branch.capitalize(), relevant_builds_01_index)
    post_cmd = """curl -d "mversion=%s&branch=%s&&relevant_builds_01=%s" %s/builds/ -H 'Authorization: Token %s'""" % (main_version, target_branch.capitalize(), relevant_builds_01_index, wrs_api, authtokens)
    logger.debug("builds API: %s" % post_cmd)
    post_result = commands.getoutput(post_cmd).split('\n')[-1]
    logger.debug("get_builds_index_from_database: %s" % post_result)
    result_dic = eval(post_result.replace('null', '-1'))
    return result_dic['id']


def get_relevant_reports_01_index_database():
    #http POST http://wrs.sh.intel.com:8080/api/relevant_reports_01/ Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' name='nightly' --timeout 3600 --ignore-stdin
    type_name = "Nightly"
    #post_cmd = "http POST %s/relevant_reports_01/ Authorization:' Token %s' name='%s' --timeout 3600 --ignore-stdin" % (wrs_api, authtokens, type_name)
    post_cmd = """curl -d "name=%s" %s/relevant_reports_01/ -H 'Authorization: Token %s'""" % (type_name, wrs_api, authtokens)
    logger.debug("relevant_reports_01 API: %s" % post_cmd)
    post_result = commands.getoutput(post_cmd).split('\n')[-1]
    logger.debug("get_relevant_reports_01_index_database: %s" % post_result)
    result_dic = eval(post_result.replace('null', '-1'))
    return result_dic['id']


def get_relevant_reports_02_index_database(category, scope_name):
    #http POST http://wrs.sh.intel.com:8080/api/relevant_reports_02/ Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' name='webapi' --timeout 3600 --ignore-stdin
    category_dic = {
        "cordova": "Cordova Features",
        "apptools": "App Tools",
        "sampleapp": "Sample Apps",
        "wrt": "WRT",
        "usecase": "Use Cases",
        "stability" : "Stability",
        "bdd": {
             "crosswalk": "Web APIs",
             "cordova": "Web APIs"
         },
        "bdd1": {
             "crosswalk": "Web APIs",
             "cordova": "Web APIs"
         },
        "webapi": {
            "crosswalk": "Web APIs",
            "cordova": "Web APIs",
            "webview": "Embedding APIs"
        }
    }

    cg = ''
    tmp = category.lower()
    if tmp == "webapi" or tmp.find("bdd") != -1:
        cg = category_dic[tmp][scope_name]
    else:
        cg = category_dic[tmp]

    #post_cmd = "http POST %s/relevant_reports_02/ Authorization:' Token %s' name='%s' --timeout 3600 --ignore-stdin" % (wrs_api, authtokens, cg)
    post_cmd = """curl -d "name=%s" %s/relevant_reports_02/ -H 'Authorization: Token %s'""" % (cg, wrs_api, authtokens)
    logger.debug("relevant_reports_02 API: %s" % post_cmd)
    post_result = commands.getoutput(post_cmd).split('\n')[-1]
    logger.debug("get_relevant_reports_02_index_database %s" % post_result)
    result_dic = eval(post_result.replace('null', '-1'))
    return result_dic['id']


def upload(device_name, result_dir):
    try:
        test_device_info = config_dic[device_name]
    except KeyError:
        logger.error("Not found the device infos of \'%s\' in \'device_config.json\'." % device_name)
        return False, None

    if not os.path.exists(result_dir):
        logger.error("No such directory: \'%s\'." % result_dir)
        return False, None

    result_dir = result_dir.rstrip('/')
    main_version = result_dir.split('/')[-2].split('_')[0]
    scope_name = result_dir.split('/')[-1].replace("apk", "crosswalk")
    platform = test_device_info['device_os']
    arch = test_device_info['device_arch']
    device_type = test_device_info['device_type']

    if auto_pack_packages:
        target_type = test_device_info['target_type']
    else:
        target_type_full = settings_dic['target_branch'].replace('master', 'canary')
        target_type = target_type_full.split('_')[0]

    sdk_version = test_device_info['android_version']
    bk_http_proxy = os.environ['http_proxy']
    os.environ['http_proxy'] = ''
    device_index = get_device_index_from_database(device_name, platform, arch, device_type, sdk_version)
    relevant_builds_01_index = get_relevant_builds_01_index_from_database(scope_name)
    builds_index = get_builds_index_from_database(main_version, target_type, relevant_builds_01_index)
    relevant_reports_01_index = get_relevant_reports_01_index_database()
    test_set_list = os.listdir(result_dir)

    if not test_set_list:
        logger.error("Result directory: \'%s\' is empty." % result_dir)
        os.environ['http_proxy'] = bk_http_proxy
        return False, None

    details_info = ''
    details_info_list = []
    url = "%s/%s/%s" % (settings_dic["pack_server"], settings_dic["target_branch"], main_version)
    commit_id = common.get_commit_id(url)
    test_env_infos_dic = settings_dic["test_env_infos"]

    for key, value in test_env_infos_dic.iteritems():
        if key == "Commit ID":
            value = commit_id
        env_item = '%s: %s' % (key, value)
        details_info_list.append(env_item)

    details_info = ';'.join(details_info_list)
    report_link_list = []
    test_set_list.sort()

    for test_set in test_set_list:
        set_dir = result_dir + '/' + test_set
        result_file_list = os.listdir(set_dir)

        if not result_file_list:
            logger.error("No such result file in \'%s\'." % set_dir)
            continue

        report_result_list = []
        result_file_list.sort()

        for result_file in result_file_list:
            result_file_path = set_dir + '/' + result_file
            logger.debug("Check result file: \'%s\' whether it has tests." % result_file_path)

            if is_need_upload(result_file_path):
                #report_result_list.append('files@%s' % result_file_path)
                report_result_list.append('-F files=@%s' % result_file_path)

        if report_result_list:
            relevant_reports_02_index = get_relevant_reports_02_index_database(test_set, scope_name)
            #http -f POST http://wrs.sh.intel.com:8080/api/reports/ Authorization:' Token 8b2b30a3ee14396a8c742243335c87231eec0d6a' files@/home/otcqa/Documents/test_result/result_tct-webstorage-w3c-tests.xml build=2 device=3 relevant_reports_01=1 relevant_reports_02=2  --timeout 3600 --ignore-stdin
            upload_cmd = """curl %s -F build=%s -F device=%s -F relevant_reports_01=%s -F relevant_reports_02=%s -F details='%s' -F summary=Summary %s/reports/ -H 'Authorization: Token %s'""" % (' '.join(report_result_list), builds_index, device_index, relevant_reports_01_index, relevant_reports_02_index, details_info, wrs_api, authtokens)
            logger.debug("reports API: %s" % upload_cmd)
            upload_result = commands.getoutput(upload_cmd).split('\n')[-1]
            logger.debug("upload result infos: %s" % upload_result)
            result_dic = eval(upload_result.replace('null', '-1'))

            #check report record whether exists, if existed, execute put cmd to update report
            if result_dic.get("error_message", None) == 'The report record is already exists.':
                report_id = result_dic["report"]["id"]
                #update_report_cmd = "http -f PUT %s/reports/%s/ Authorization:' Token %s' %s build=%d device=%d relevant_reports_01=%d relevant_reports_02=%d details='details' summary='Summary' --timeout 3600 --ignore-stdin" % (wrs_api, report_id, authtokens, ' '.join(report_result_list), builds_index, device_index, relevant_reports_01_index, relevant_reports_02_index)
                update_report_cmd = """curl -X PUT %s -F build=%s -F device=%s -F relevant_reports_01=%s -F relevant_reports_02=%s -F details='%s' -F summary=Summary %s/reports/%s/ -H 'Authorization: Token %s'""" % (' '.join(report_result_list), builds_index, device_index, relevant_reports_01_index, relevant_reports_02_index, details_info, wrs_api, report_id, authtokens)
                #update_report_result = commands.getoutput(update_report_cmd)
                update_report_result = commands.getoutput(update_report_cmd).split('\n')[-1]
                result_dic = eval(update_report_result.replace('null', '-1'))

            if result_dic.get("report", None):
                report_link = "%s/reports/%s" % (wrs_api, result_dic["report"]["id"])
                report_link = report_link.replace('api/','')
                report_link_list.append(report_link)

            #handle upload result and save report id
            upload_log_save_dir = "../upload_log/%s/%s" % (device_name, result_dir.split('/')[-2])

            if not os.path.exists(upload_log_save_dir):
                os.makedirs(upload_log_save_dir)

            upload_log_file = "%s/%s_%s-%s_%s.txt" % (upload_log_save_dir, main_version, scope_name, test_set.replace("Cordova", "CoadovaAPI"), time.strftime('%Y%m%d%H%M%S', time.localtime()))
            common.save_dic_json_file(result_dic, upload_log_file)

    logger.info("Finish upload report.")
    os.environ['http_proxy'] = bk_http_proxy

    return True, report_link_list


if __name__ == '__main__':
    argv_len = len(sys.argv)

    if argv_len != 3:
        print_usage()
        sys.exit(-1)

    device_name = sys.argv[1]
    result_dir = sys.argv[2]
    status, reports = upload(device_name, result_dir)
    print "Upload report status: %s %s." % (status, reports)
