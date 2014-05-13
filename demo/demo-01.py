#!/usr/bin/env python

from threading import Thread
from time import sleep
import sys

sys.path.append("../../context-apis/python/")

import context.api as c


def thread_1():
    c.log_bmark("Server thread spawned")

    c.log_start("Logging in", bookmark=True)
    sleep(0.1)
    c.log_start("Search database")
    sleep(0.3)
    c.log_endok("Search database")
    c.log_start("Initialise session for 'daniel'")
    sleep(0.3)
    c.log_endok("Initialise session for 'daniel'")
    c.log_start("Render")
    sleep(0.1)
    c.log_endok("Render")
    c.log_endok("Logging in")

    sleep(0.2)

    c.log_start("Repeat login", bookmark=True)
    sleep(0.3)
    c.log_ender("Repeat login")

    sleep(0.1)

    c.log_start("Read article", bookmark=True)
    sleep(0.05)
    c.log_start("Search database")
    sleep(0.3)
    c.log_endok("Search database")
    c.log_start("Render")
    sleep(0.1)
    c.log_endok("Render")
    sleep(0.05)
    c.log_endok("Read article")

def thread_2():
    c.log_bmark("Server thread spawned")

    sleep(0.7)

    c.log_start("User profile", bookmark=True)
    sleep(0.1)
    c.log_start("Search database")
    sleep(0.3)
    c.log_endok("Search database")
    c.log_start("Render")
    sleep(0.1)
    c.log_endok("Render")
    c.log_endok("Logging in")

def thread_3():
    c.log_bmark("Server thread spawned")

    sleep(0.2)

    c.log_start("Read article", bookmark=True)
    sleep(0.05)
    c.log_start("Search database")
    sleep(0.3)
    c.log_endok("Search database")
    c.log_start("Render")
    sleep(0.1)
    c.log_endok("Render")
    sleep(0.05)
    c.log_endok("Read article")

    sleep(0.4)

    c.log_start("Post comment", bookmark=True)
    sleep(0.05)
    c.log_start("Create")
    sleep(0.3)
    c.log_endok("Create")
    c.log_start("Render")
    sleep(0.1)
    c.log_endok("Render")
    sleep(0.05)
    c.log_endok("Post comment")

def thread_4():
    c.log_bmark("Server thread spawned")

    c.log_start("Logging in", bookmark=True)
    sleep(0.1)
    c.log_start("Search database")
    sleep(0.3)
    c.log_endok("Search database")
    c.log_start("Initialise session for 'laura'")
    sleep(0.3)
    c.log_endok("Initialise session for 'laura'")
    c.log_start("Render")
    sleep(0.1)
    c.log_endok("Render")
    c.log_endok("Logging in")

    sleep(0.2)

    c.log_start("Repeat login", bookmark=True)
    sleep(0.2)
    c.log_ender("Repeat login")

    sleep(0.2)

    c.log_start("Read article", bookmark=True)
    sleep(0.05)
    c.log_start("Search database")
    sleep(0.3)
    c.log_endok("Search database")
    c.log_start("Render")
    sleep(0.1)
    c.log_endok("Render")
    sleep(0.05)
    c.log_endok("Read article")

if __name__ == "__main__":
    c.set_log("file://%s" % sys.argv[0].replace(".py", ".ctxt"))

    Thread(target=thread_1, name="Server-1").start()
    sleep(0.05)
    Thread(target=thread_2, name="Server-2").start()
    sleep(0.05)
    Thread(target=thread_3, name="Server-3").start()
    sleep(0.05)
    Thread(target=thread_4, name="Server-4").start()
