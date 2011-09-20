from __future__ import print_function
from decorator import decorator
import time
import platform
import os


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


def log_bookmark(function, text=None):
    """Shortcut to log some text with the bookmark type"""
    log_msg(function, text, "BMARK")


def log_start(function, text=None):
    """Shortcut to log some text with the event-start type"""
    log_msg(function, text, "START")


def log_end(function, text=None):
    """Shortcut to log some text with the event-end (success) type"""
    log_msg(function, text, "ENDOK")


def log_error(function, text=None):
    """Shortcut to log some text with the event-end (error) type"""
    log_msg(function, text, "ENDER")


def log(text, bookmark=False, exceptions=True):
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
            if bookmark:
                log_bookmark(function.func_name, _text)
            log_start(function.func_name, _text)
            d = function(*args, **kwargs)
            log_end(function.func_name, _text)
            return d
        except Exception as e:
            if exceptions:
                log_error(functions.func_name, _text)
            else:
                log_end(functions.func_name, _text)
            raise
    return _log
