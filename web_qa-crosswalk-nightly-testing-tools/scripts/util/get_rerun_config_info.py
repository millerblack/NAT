import json
import sys
from ntcommon import generate_spec_file


def get_rerun_test_base_dic(rerun_json_file):
    with open(rerun_json_file) as f:
        d = json.load(f)

    return d


def get_rerun_test_spec(rerun_json_file, output_file="output_rerurn_test_list.spec"):
    test_list = []
    d = get_rerun_test_base_dic(rerun_json_file)

    if len(d):
        if d.has_key("suite-level"):
            test_list.extend(d["suite-level"])
        if d.has_key("case-level"):
            test_list.extend(d["case-level"].keys())

    generate_spec_file(test_list, output_file)


def get_rerun_test_dic(rerun_json_file):
    rerurn_test_dic = {}
    d = get_rerun_test_base_dic(rerun_json_file)

    if len(d):
        if d.has_key("suite-level"):
            for ts in d["suite-level"]:
                sub_info_d = {}
                sub_info_d['level'] = 1#"suite-level"
                rerurn_test_dic[ts] = sub_info_d
        if d.has_key("case-level"):
            for ts in d["case-level"].keys():
                sub_info_d = {}
                sub_info_d['level'] = 2#"case-level"
                sub_info_d['case_list'] = d["case-level"][ts]
                rerurn_test_dic[ts] = sub_info_d

    return rerurn_test_dic


if __name__ == '__main__':
    json_file = sys.argv[1]
    get_rerun_test_dic(json_file)

    if len(sys.argv) == 3:
        output_file =  sys.argv[2]
        get_rerun_test_spec(json_file, output_file)
    else:
        get_rerun_test_spec(json_file)
