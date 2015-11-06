import threading
import commands
o = commands.getoutput('date')
print o

job_thread_list = []

def download(url, dist):
    o = commands.getoutput("wget -A zip -q --no-proxy -r -np -nH --cut-dirs=7  %s -P %s" % (url, dist))
    print o

url_list = [
    "http://jiaxxx-dev.sh.intel.com/ForNightlyAutoTest/android/master/17.45.422.0/crosswalk-tools/arm/",
    "http://jiaxxx-dev.sh.intel.com/ForNightlyAutoTest/android/master/17.45.422.0/crosswalk-tools/x86/",
]


#for i in url_list:
#    dist = i.rstrip('/').split('/')[-1]
#    test_thread = threading.Thread(target = download, args = (i, dist))
#    job_thread_list.append(test_thread)
#
#
#for job_thread in job_thread_list:
#    job_thread.start()
#
#for job_thread in job_thread_list:
#    job_thread.join()
for i in url_list:
    dist = "%s-1" % i.rstrip('/').split('/')[-1]
    download(i, dist)
o = commands.getoutput('date')
print o
