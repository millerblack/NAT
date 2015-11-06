import json
import sys
from xml.etree import ElementTree


layer = "layer"

def get_block_rate(input_file, output_file, webdriver_mode):
    try:
        total_no = 0
        pass_no = 0
        fail_no = 0
        block_no = 0

        #root = ElementTree.fromstring(open(output_file).read())
        input_root = ElementTree.parse(input_file)
        input_suite_node = input_root.find("suite")
        input_set_iter = input_suite_node.getiterator("set")
        for input_set_node in input_set_iter:
            #if input_set_node.get("type") == "ref":
            #    #skip ref auto cases
            #    continue
            input_tcs = input_set_node.getiterator("testcase")
            for input_tc in input_tcs:
                if webdriver_mode == 1:
                    if input_tc.get("execution_type") == "auto" or input_tc.get("execution_type") == "manual":
                        subcase_no = input_tc.get("subcase")
                        if subcase_no:
                            total_no += int(subcase_no)
                        else:
                            total_no += 1
                    elif input_tc.get("execution_type") == "auto":
                        subcase_no = input_tc.get("subcase")
                        if subcase_no:
                            total_no += int(subcase_no)
                        else:
                            total_no += 1

        output_root = ElementTree.parse(output_file)
        output_suite_node = output_root.find("suite")
        output_set_iter = output_suite_node.getiterator("set")

        for output_set_node in output_set_iter:
            #if output_set_node.get("type") == "ref":
            #    #skip ref auto cases
            #    continue
            output_tcs = output_set_node.getiterator("testcase")
            for output_tc in output_tcs:
               result_node = output_tc.find("result_info/actual_result")

               if result_node.text == "PASS":
                   pass_no += 1
               elif result_node.text == "FAIL":
                   fail_no += 1

        block_no = total_no - pass_no - fail_no

        print total_no, pass_no, fail_no, block_no

        return round(1.0 * block_no / total_no * 100)
    except:
        return 100


def get_detail_value(value, layers_list, test_name):
    dic = {}
    dic[test_name] = value

    for l in layers_list:
        tmp_dic = {}
        tmp_dic[l] = dic
        dic = tmp_dic
    return dic


def get_value(value, layer_list, test_name, i = None):
    result_dic = {}

    if i == 0:
        result_dic = get_detail_value(value, layer_list[:-1], test_name)
    elif i == 1:
        result_dic = get_detail_value(value, layer_list[:-2], test_name)
    elif i == 2:
        result_dic = get_detail_value(value, layer_list[:-3], test_name)
    elif i == 3:
        result_dic = get_detail_value(value, layer_list[:-4], test_name)
    else:
        result_dic = value

    return result_dic


def update_rerun_tests_dic(all_tests_dic, test_name, rerun_tests_dic):
    value_dic = all_tests_dic[test_name]
    layers_list = value_dic[layer].split('/')
    layer_num = len(layers_list)
    del value_dic[layer]

    assit_layers_list = []
    assit_layers_list[:] = layers_list
    assit_layers_list.reverse()

    index = 0

    if not rerun_tests_dic.has_key(layers_list[index]):
        rerun_tests_dic[layers_list[index]] = get_value(value_dic, assit_layers_list, test_name, index)
    else:
        second_tests_dic = rerun_tests_dic[layers_list[index]]
        index += 1

        if not second_tests_dic.has_key(layers_list[index]):
            second_tests_dic[layers_list[index]] = get_value(value_dic, assit_layers_list, test_name, index)
        else:
            third_tests_dic = second_tests_dic[layers_list[index]]
            index += 1

            if layer_num == index:
                third_tests_dic[test_name] = get_value(value_dic, assit_layers_list, test_name)
            else:
                if not third_tests_dic.has_key(layers_list[index]):
                    third_tests_dic[layers_list[index]] = get_value(value_dic, assit_layers_list, test_name, index)
                else:
                    fourth_tests_dic = third_tests_dic[layers_list[index]]
                    index += 1

                    if layer_num == index:
                        fourth_tests_dic[test_name] = get_value(value_dic, assit_layers_list, test_name)
                    else:
                        if not fourth_tests_dic.has_key(layers_list[index]):
                            fourth_tests_dic[layers_list[index]] = get_value(value_dic, assit_layers_list, test_name, index)
                        else:
                            fifth_tests_dic = fourth_tests_dic[layers_list[index]]
                            fifth_tests_dic[test_name] = get_value(value_dic, assit_layers_list, test_name)
    return rerun_tests_dic

def is_bottom_layer(keys_list):
    flag = 'timeout'
    if flag in keys_list:
        return True
    else:
        return False


def reoragnize_tests_dic(dic):
    reoragnize_tests_dic = {}

    for key, value in dic.iteritems():#"test_specs_list"
        for second_key, second_value in value.iteritems():#"WebAPI", "android"
            for third_key, third_value in second_value.iteritems():#"WebAPI"
                if not is_bottom_layer(third_value.keys()):
                    for fourth_key, fourth_value in third_value.iteritems():#"webapi-service-tests"
                        if not is_bottom_layer(fourth_value.keys()):
                            #special_test_specs_list/android/WebAPI/webapi-service-tests
                            for fifth_key, fifth_value in fourth_value.iteritems():
                                reoragnize_tests_dic[fifth_key] = fifth_value
                                reoragnize_tests_dic[fifth_key][layer] = "%s/%s/%s/%s" % (key, second_key, third_key, fourth_key)
                        else:
                            #special_test_specs_list/android/WRT/wrt-xxx-tests
                            reoragnize_tests_dic[fourth_key] = fourth_value
                            reoragnize_tests_dic[fourth_key][layer] = "%s/%s/%s" % (key, second_key, third_key)
                else:
                    #special_test_specs_list/WRT/wrt-xxx-tests
                    reoragnize_tests_dic[third_key] = third_value
                    reoragnize_tests_dic[third_key][layer] = "%s/%s" % (key, second_key)

    return reoragnize_tests_dic


def generate_rerun_tests_list(device_name, input_file, output_dir):
    output_json_file = "%s/tests_list.json" % output_dir
    base_tests_list_file = "../resources/%s/tests_list.json" % device_name

    try:
        with open(base_tests_list_file) as f:
            base_all_tests_dic = json.load(f)

        new_all_tests_dic = reoragnize_tests_dic(base_all_tests_dic)
        input_handle = open(input_file)
        rerun_tests_list = input_handle.readlines()
        input_handle.close()
        rerun_tests_dic = {}

        for rerun_test in rerun_tests_list:
            rerun_test_name = rerun_test.split('\n')[0]
            category = rerun_test_name.split('-')[0]
            if category not in ["tct", "webapi", "wrt", "embedding", "stability", "usecase", "apptools", "sampleapp", "cordova"]:
                rerun_test_name = "tct-%s" % rerun_test_name
            print ">>>>>>>>>>>>>>test name : %s" % rerun_test_name
            rerun_tests_dic = update_rerun_tests_dic(new_all_tests_dic, rerun_test_name, rerun_tests_dic)

        #write rerun_tests_dic infos into output_json_file
        output_handle = open(output_json_file, 'w')
        output_content = json.dumps(rerun_tests_dic, sort_keys = True, indent = 2)
        output_handle.write(output_content)
        output_handle.close()

        return "Yes"
    except Exception, e:
        print "fail to generate rerun tests_list: %s " % e
        return "No"



if __name__ == '__main__':
    device_name = sys.argv[1]
    input_file = sys.argv[2]
    output_dir = sys.argv[3]
    print sys.argv
    status = generate_rerun_tests_list(device_name, input_file, output_dir)
    print "Generate rerun tests_list: %s" % {"Yes": "Successfully", "No": "Fail"}[status]
