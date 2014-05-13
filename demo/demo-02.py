#!/usr/bin/env python

from threading import Thread
from time import sleep
import random
import sys
import time
import threading

sys.path.append("../../context-apis/python/")

import context.api as c

lock = c.LockWrapper(threading.Lock(), "Archive Lock")

def thread():
    c.log_bmark("Server thread spawned")

    for n in range(0, 4):
        time.sleep(random.random() * 0.5)

        c.log_start("Processing Video", bookmark=True)

        c.log_start("Reading file")
        time.sleep(1 + random.random() * 2.0)
        c.log_endok("")

        c.log_start("Waiting for lock")
        lock.acquire()
        c.log_endok("")

        c.log_start("Adding to archive")
        time.sleep(1 + random.random() * 2.0)
        lock.release()
        c.log_endok("")

        c.log_endok("")

if __name__ == "__main__":
    c.set_log("file://%s" % sys.argv[0].replace(".py", ".ctxt"))

    Thread(target=thread, name="Server-1").start()
    sleep(0.05)
    Thread(target=thread, name="Server-2").start()
    sleep(0.05)
    Thread(target=thread, name="Server-3").start()
    sleep(0.05)
    Thread(target=thread, name="Server-4").start()
