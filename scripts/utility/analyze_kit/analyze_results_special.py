from xml.etree import ElementTree
import sys

def main(xml_file):
    total_no = 0
    pass_no = 0
    fail_no = 0
    block_no = 0

    root = ElementTree.fromstring(open(xml_file).read())
    suite_node = root.find("suite")
    set_iter = suite_node.getiterator("set")

    for set_node in set_iter:
        tcs = set_node.getiterator("testcase")
        for tc in tcs:
           total_no += 1
           result_node = tc.find("result_info/actual_result")
        
           if result_node.text == "PASS":
               pass_no += 1
           elif result_node.text == "FAIL":
               fail_no += 1
           else:
               block_no += 1
    
    print total_no, pass_no, fail_no, block_no

if __name__ == '__main__':
    xml_file = sys.argv[1]
    main(xml_file)
