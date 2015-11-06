#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import threading
import multiprocessing

count_process = 0

# worker function
def worker1(sign, v, lock):
    lock.acquire()
    if not os.path.exists(v):
        os.mkdir(v)
    print(sign, os.getpid())
    lock.release()

def worker2(sign, lock):
    global count_process
    lock.acquire()
    count_process += 1
    record = []
    tlock  = threading.Lock()
    dic = {'i0': "aaa", 'i1': "bbb", 'i2': "ccc", 'i3': "ddd", 'i4': "eee"}
    for i in range(5):
        v = dic["i%d" % i]
        thread = threading.Thread(target=worker1,args=('thread',v, tlock))
        thread.start()
        record.append(thread)

    for thread in record:
        thread.join()

    print(sign, os.getpid())
    lock.release()
# Main
print('Main:',os.getpid())


# Multi-process
record = []
lock = multiprocessing.Lock()
for i in range(5):
    process = multiprocessing.Process(target=worker2,args=('process',lock))
    process.start()
    record.append(process)

for process in record:
    process.join()


#print count_thread
print count_process
