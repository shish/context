from __future__ import print_function
from decorator import decorator
import time
import platform
import threading
import os
import sys


#######################################################################
# Library API
#######################################################################

_output = None


def set_log(fn):
    """
    set the filename of the telemetry log
    """
    global _output
    _output = open(fn, "a", 1)


def log_msg(function, text, io):
    """
    Log a bit of text with a given type
    """
    tn = threading.current_thread().name.replace(" ", "-")
    if _output:
        print("%f %s %d %s %s %s %s\n" % (
            time.time(),
            platform.node(), os.getpid(), tn,
            io, function, text
        ), file=_output, end='')


def log(text, bookmark=False, exceptions=True, clear=False):
    """Decorator to log event-start at the start of a function
    call and event-end at the end, optionally with a bookmark
    at the start"""
    @decorator
    def _log(function, *args, **kwargs):
        if callable(text):
            _text = text(function, args, kwargs)
        else:
            _text = text
        try:
            if clear:
                log_msg(function.func_name, None, "CLEAR")
            if bookmark:
                log_msg(function.func_name, _text, "START")
            log_msg(function.func_name, _text, "START")
            d = function(*args, **kwargs)
            log_msg(function.func_name, None, "ENDOK")
            return d
        except Exception as e:
            if exceptions:
                log_msg(function.func_name, str(e), "ENDER")
            else:
                log_msg(function.func_name, None, "ENDOK")
            raise
    return _log


#######################################################################
# Library Convenience
#######################################################################

def log_start(function, text=None, bookmark=False, clear=False):
    """Shortcut to log some text with the event-start type"""
    if clear:
        log_msg(function, text, "CLEAR")
    if bookmark:
        log_msg(function, text, "BMARK")
    log_msg(function, text, "START")


def log_endok(function, text=None):
    """Shortcut to log some text with the event-end (success) type"""
    log_msg(function, text, "ENDOK")


def log_ender(function, text=None):
    """Shortcut to log some text with the event-end (error) type"""
    log_msg(function, text, "ENDER")


#######################################################################
# Automatic Profiling Mode
#######################################################################

def _profile(frame, action, params):
    if action == 'call':
        log_msg(
            "%s:%d" % (frame.f_code.co_filename, frame.f_code.co_firstlineno),
            frame.f_code.co_name,
            "START"
        )
    if action == 'return':
        log_msg(
            "%s:%d" % (frame.f_code.co_filename, frame.f_code.co_firstlineno),
            frame.f_code.co_name,
            "ENDOK"
        )

def set_profile(active=False):
    if active:
        log_start("context.py", "Profiling init", True)
        sys.setprofile(_profile)
    else:
        sys.setprofile(None)
        log_endok("context.py", "Profiling exit")
