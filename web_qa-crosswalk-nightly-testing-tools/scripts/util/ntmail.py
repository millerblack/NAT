#import mimetypes
import os
import smtplib
import platform
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ntcommon import *


def get_report_link_info(link_dir):
    nt_logger.debug("Call Function: 'get_report_link_info' with link_dir(%s)" % link_dir)
    link_info = None
    link_file = "%s/report_link.txt" % link_dir

    if os.path.isfile(link_file):
        with open(link_file) as f:
            link_info = f.read()

    return link_info


def generate_report_mail_summary(result_dir, binary_branch, binary_version, device_name, timestamp, flag, segment, platform_version, device_arch, device_type):
    nt_logger.debug("Call Function: 'generate_report_mail_summary' with result_dir(%s), binary_branch(%s), binary_version(%s), device_name(%s), timestamp(%s), flag(%s), segment(%s), platform_version(%s), device_arch(%s), device_type(%s)"% (result_dir, binary_branch, binary_version, device_name, timestamp, flag, segment, platform_version, device_arch, device_type))
    binary_file_name = "crosswalk-%s" % binary_version

    if device_arch in ['x86_64', 'arm64']:
        binary_file_name = "crosswalk-%s-64bit" % binary_version

    binary_info = "Binary Location\n-----------------------\n%s (%s/%s/%s/%s/%s/crosswalk-tools/%s.zip)" % (binary_file_name, package_release_server_url, crosswalk_type, test_platform, binary_branch.replace('canary', 'master'), binary_version, binary_file_name)
    device_info_title = "\n\nTest Device & Operating System\n-----------------------\n"
    device_info = "%s (%s) - %s Version: %s\n\n" % (device_name.replace("_", " "), device_type.capitalize(), test_platform.capitalize(), platform_version)
    host_info = ''
    host_info_list = []
    host_name_info = "Host Name: %s%s" % (get_host_name(), domain_name)

    if platform.system() == 'Darwin':
        host_name_info = "Host Name: %s" % get_host_name()

    host_system_info = "Host OS: "

    if platform.system() != 'Darwin':
        with open("/etc/issue") as issue_file:
            ubuntu_info = issue_file.read().strip('\n')
            host_system_info += ubuntu_info[:ubuntu_info.find("\\n")-1]
    else:
        host_system_info += get_macbook_system_info()

    host_info_list.append(host_name_info)
    host_info_list.append(host_system_info)
    host_info = '\n'.join(host_info_list)
    details_info = ''
    details_info_list = []
    url = "%s/%s/%s/%s/%s/" % (package_release_server_url, crosswalk_type, test_platform, binary_branch.replace('canary', 'master'), binary_version)
    commit_id = get_commit_id(url)
    test_env_infos_dic = settings_dic["test_env_infos"]

    for key, value in test_env_infos_dic.iteritems():
        if key == "Commit ID":
            value = commit_id
        env_item = '%s: %s' % (key, value)
        details_info_list.append(env_item)

    details_info_list.sort()
    details_info = '\n'.join(details_info_list)
    summary_info = binary_info + device_info_title + device_info + host_info + '\n' + details_info

    if is_upload_report:
        save_link_dir = "%s/%s/%s/%s/%s" % (upload_log_dir, device_name, binary_version, timestamp, flag)
        link_info = get_report_link_info(save_link_dir)
        link_summary = "\n\nReport links\n-----------------------\n%s\n" % link_info
        report_log_dir = "%s/%s" % (save_link_dir, segment)
        exception_cases_list = []
        index = 1
        log_arr =  glob.glob("%s/*" % report_log_dir)
        for log_file in log_arr:
            with open(log_file) as f:
                log_dic = json.load(f)
                exception_cases_dic = log_dic['exception_case']
                if exception_cases_dic:
                    for k, v in exception_cases_dic.iteritems():
                        exception_cases_list.append("[%d] %s" % (index, v))
                        index += 1
        upload_log_info = "Error infos\n-----------------------\n%s" % '\n'.join(exception_cases_list)
        summary_info = summary_info + link_summary + upload_log_info

    summary_info = summary_info + "\nThanks,\nCrosswalk QA team"

    with open("%s/report_summary.txt" % result_dir, "w") as f:
        f.write(summary_info)

    return summary_info


def send_mail(result_dir):
    nt_logger.debug("Call Function: 'send_mail' with result_dir(%s)" % result_dir)
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
    #xw_type = child_path_list[-9]
    device_arch = device_config_dic[device_name]["device_arch"]
    device_type = device_config_dic[device_name]["device_type"]
    binary_branch = binary_branch.replace('master', 'canary')

    try:
        mail_object =  mail_settings_dic["mail_object"]
        if is_webdriver:
            mail_object += '-webdriver'
        mail_user = mail_settings_dic["mail_user"]
        mail_from = "%s<%s@%s>" % (mail_user, mail_user, mail_settings_dic["mail_postfix"])
        mail_list = mail_settings_dic["mail_list"]
        mail_cclist = mail_settings_dic["mail_cclist"]
        mail_bcclist = mail_settings_dic["mail_bcclist"]
        mail_to = mail_list + mail_cclist + mail_bcclist
        message = MIMEMultipart()
        mail_content = generate_report_mail_summary(result_dir, binary_branch, binary_version, device_name, timestamp, flag, segment, platform_version, device_arch, device_type)
        message.attach(MIMEText(mail_content))
        message["Subject"] = "[NightlyReport]%s-%s-%s-%s-%s_%s (%s)" % (mode.capitalize(), ' '.join([x.capitalize() for x in crosswalk_type.split('-')]), binary_branch.capitalize(), test_platform.capitalize(), device_arch.upper(), mail_object, device_name.replace('_', ' '))
        message["From"] = mail_from
        message["To"] = ";".join(mail_list)
        message["Cc"] = ";".join(mail_cclist)
        message["Bcc"] = ";".join(mail_bcclist)
        smtp = smtplib.SMTP()
        smtp.connect(mail_settings_dic["mail_host"])
        smtp.sendmail(mail_from, mail_to, message.as_string())
        smtp.quit()
        return True
    except Exception, errmsg:
        nt_logger.error("Fail to send the mail with: [%s]." % errmsg)
        return False
