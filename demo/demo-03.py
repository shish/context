#!/usr/bin/env python

from threading import Thread
from time import sleep
import random
import sys
import time
import threading

sys.path.append("../../context-apis/python/")

import context.api as c

if __name__ == "__main__":
    c.set_log("file://%s" % sys.argv[0].replace(".py", ".ctxt"))

    c.log_start("Rendering", bookmark=True)
    for n in range(0, 1000):
        c.log_start("Frame")
        time.sleep(0.001)
        c.log_endok("")
    c.log_endok()
