import common
x86_url_list = common.get_packages_url("../../resources/ASUS_MeMO_Pad_8_K011/tests_list.spec", "http://jiaxxx-dev.sh.intel.com/ForNightlyAutoTest/android/master/17.45.429.0/testsuites-embedded/x86/")

arm_url_list = common.get_packages_url("../../resources/ASUS_MeMO_Pad_8_K011/tests_list.spec", "http://jiaxxx-dev.sh.intel.com/ForNightlyAutoTest/android/master/17.45.429.0/testsuites-embedded/arm/")

print "============================================================="
print len(x86_url_list)
print "============================================================="
print len(arm_url_list)

import threading
import commands
o = commands.getoutput('date')
print o

job_thread_list = []

def download(url, dist):
    o = commands.getoutput("wget -A zip -q --no-proxy -r -np -nH --cut-dirs=7  %s -P %s" % (url, dist))
    print o


for i in x86_url_list:
    test_thread = threading.Thread(target = download, args = (i, "17.45.429.0/testsuites-embedded/x86"))
    job_thread_list.append(test_thread)


for i in arm_url_list:
    test_thread = threading.Thread(target = download, args = (i, "17.45.429.0/testsuites-embedded/arm"))
    job_thread_list.append(test_thread)


for job_thread in job_thread_list:
    job_thread.start()

for job_thread in job_thread_list:
    job_thread.join()
o = commands.getoutput('date')
print o
