import mimetypes
import os
import smtplib
import sys
import common
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


logger = common.nt_logger
settings_dic = common.settings_dic
config_dic = common.device_config_dic
auto_pack_packages = settings_dic["auto_pack_packages"]


def print_usage():
    print """usage:
  python QAMail.py <device_name> <result_dir>"""


def send(device_name, result_dir):
    logger.debug("Send mail with the result of \'%s\'." % device_name)

    try:
        test_device_info = config_dic[device_name]
    except KeyError:
        logger.error("Not found the device infos of \'%s\' in \'device_config.json\'." % device_name)
        return False

    if not os.path.exists(result_dir):
        logger.error("No such directory: \'%s\'." % result_dir)
        return False

    if auto_pack_packages:
        target_type = test_device_info["target_branch"]
    else:
        target_type = settings_dic['target_branch'].replace("master", "canary")

    device_os = test_device_info["device_os"]

    if device_os == "android":
        device_arch = test_device_info["device_arch"]
        test_type = device_arch.upper().replace('X86', 'IA')
    else:
        os_type = test_device_info["os_type"]
        if os_type == 'ivi':
            test_type = os_type.upper()
        else:
            test_type = os_type.capitalize()

    try:
        mail_settings_dic = settings_dic["mail_settings"]
        mail_object =  mail_settings_dic["mail_object"]
        mail_from = mail_settings_dic["mail_user"] + "<" + mail_settings_dic["mail_user"] + "@" + mail_settings_dic["mail_postfix"] + ">"
        mail_list = mail_settings_dic["mail_list"].values()
        mail_cclist = mail_settings_dic["mail_cclist"].values()
        mail_bcclist = mail_settings_dic["mail_bcclist"].values()
        message = MIMEMultipart()
        content_file = "%s/report_summary.txt" % result_dir
        file_handle = open(content_file)
        mail_content = file_handle.read()
        file_handle.close()
        message.attach(MIMEText(mail_content))
        message["Subject"] = "[NightlyReport]Crosswalk-%s-%s-%s_%s (%s)" % (target_type.capitalize(), device_os.capitalize(), test_type, mail_object, device_name.replace('_', ' '))
        message["From"] = mail_from
        message["To"] = ";".join(mail_list)
        message["Cc"] = ";".join(mail_cclist)
        message["Bcc"] = ";".join(mail_bcclist)

        test_scope_list = settings_dic["test_scope_list"]

        for scope_name in test_scope_list:
            attachment_file = "%s/%s/report_details.html" % (result_dir, scope_name)

            if os.path.isfile(attachment_file):
                ctype, encoding = mimetypes.guess_type(attachment_file)

                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"

                maintype, subtype = ctype.split("/", 1)
                attachment = MIMEImage((lambda f: (f.read(), f.close()))(open(attachment_file, "rb"))[0], _subtype = subtype)
                name = "report_details.html"
                if scope_name == "cordova":
                    name = "report_details_cordova.html"
                elif scope_name == "webview":
                    name = "report_details_embeddingapi.html"

                attachment.add_header("Content-Disposition", "attachment", filename = name)
                message.attach(attachment)

        smtp = smtplib.SMTP()
        smtp.connect(mail_settings_dic["mail_host"])
        smtp.sendmail(mail_from, mail_list + mail_cclist + mail_bcclist, message.as_string())
        smtp.quit()
    except Exception, errmsg:
        logger.error("""Fail to send the mail due to:
%s.""" % errmsg)
        return False

    return True


if __name__ == '__main__':
    argv_len = len(sys.argv)

    if argv_len != 3:
        print_usage()
        sys.exit(-1)

    device_name = sys.argv[1]
    result_dir = sys.argv[2]
    status = send(device_name, result_dir)
    print "Send mail status: %s" % status
