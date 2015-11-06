import threading
import commands

o = commands.getoutput('date')
print o
job_thread_list = []

def download(url):
    o = commands.getoutput("axel -N -n 10 %s -o haha" % url)
    print o

url_list = [
    "http://jiaxxx-dev.sh.intel.com/ForNightlyAutoTest/android/master/17.45.422.0/crosswalk-tools/x86/crosswalk-apks-17.45.422.0-x86.zip",
    "http://jiaxxx-dev.sh.intel.com/ForNightlyAutoTest/android/master/17.45.422.0/crosswalk-tools/x86/crosswalk-cordova-17.45.422.0-x86.zip",
    "http://jiaxxx-dev.sh.intel.com/ForNightlyAutoTest/android/master/17.45.422.0/crosswalk-tools/x86/crosswalk-test-apks-17.45.422.0-x86.zip"
]


for i in url_list:
    test_thread = threading.Thread(target = download, args = (i, ))
    job_thread_list.append(test_thread)


for job_thread in job_thread_list:
    job_thread.start()

for job_thread in job_thread_list:
    job_thread.join()
o = commands.getoutput('date')
print o
