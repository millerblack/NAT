import json
import sys
import os

def check(json_file):
    file_name = os.path.basename(json_file)

    try:
        with open(json_file) as jf:
            json.load(jf)
        print "Check '%s'\t ... [OK]" % file_name
    except Exception, e:
        print "Check '%s'\t ... [FAIL] --- Exception: %s" % (file_name, e)


if __name__ == '__main__':
    checking_file = sys.argv[1]
    check(checking_file)
