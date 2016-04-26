import json
import sys
from ntcommon import *


def show_not_in(ts_list_file):
    ts_list = get_lines(ts_list_file)

    with open("%s/test_list.json" % resources_dir) as f:
        d = json.load(f)

    ts_list.sort()

    for ts in ts_list:
        if not d.has_key(ts):
           print ts


if __name__ == '__main__':
    show_not_in(sys.argv[1])
