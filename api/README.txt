
All the language APIs have a fairly similar set of functions, though the
specifics will be changed to fit with each language's coding standards
(eg set_log in Python is setLog in Java, or ctx_set_log in PHP)



set_log(filename)
    - tell context to start logging events into this file
    - if filename is null / None / 0 / etc, stop logging to file

    Implemented by: all APIs


set_server(url)
    - set a central server to send events to
       udp://192.168.123.456:1234
       tcp://192.168.123.456:1234
    - if url is null / None / 0 / etc, stop logging to server

    Implemented by: nothing yet


set_profile(enabled)
    - hook into the language runtime to automatically log when
      every function starts and ends
    - enabled = boolean, true to start profiling, false to stop

    Implemented by: Python


log_msg(location, text, marker)
    - location = where the code is
    - text     = freeform text description of what's happening
    - marker   = BMARK, START, ENDOK, ENDER, CLEAR

    Implemented by: ?


log_start(text)
    - log that an event has started
    - shortcut to log_msg(getCurrentFunction(), text, "START")

log_endok(text)
    - log that an event has finished successfully

log_ender(text)
    - log that an event has finished with an error

log_bmark(text)
    - add a bookmark to the log

log_clear(text)
    - clear the stack (it's possible that an app crash could cause
      a START event to be logged with no matching ENDOK; CLEAR
      will turn any currently unfinished events into ENDER)


log(text or callback)
    - a decorator to log at the start and end of a function
    - if a callback is specified, it will be passed the function
      name and paramaters, and it should return some text

    Implemented by: Python
