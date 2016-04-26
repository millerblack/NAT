import json
import sys
from ntcommon import *

def print_sorted_id_list(device_name):
    with open("%s/device_config.json" % resources_dir) as f:
        d = json.load(f)

    id_list = d[device_name]["id_list"]
    id_list.sort()
    print "Sorted id_list: %s" % id_list


if __name__ == '__main__':
    print_sorted_id_list(sys.argv[1])
