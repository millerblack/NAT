import sys
import os
sys.path.append("%s/../../util" % os.path.abspath(os.path.dirname(__file__)))
from ntcommon import *
import shutil

def print_usage():
    print """usage:
  python create_csv_template_dirs.py <result_dir>"""


def create_csv_template_dirs(dst_dir):
    upload_xml_csv_dir = "%s/upload_xml_csv" % dst_dir

    if not os.path.exists(upload_xml_csv_dir):
        os.makedirs(upload_xml_csv_dir)
    else:
        os.system("rm -rf %s" % upload_xml_csv_dir)

    for category in test_suite_categories_list:
        sub_dir = "%s/%s" % (upload_xml_csv_dir, category)
        os.makedirs(sub_dir)

    shutil.copy("%s/upload_config.json" % resources_dir, upload_xml_csv_dir)


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print_usage()
    else:
        result_dir = sys.argv[1]
        create_csv_template_dirs(result_dir)
