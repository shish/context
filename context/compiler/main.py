#!/usr/bin/env python

import os
from time import time
import argparse
import sys
try:
    import pysqlite2.dbapi2 as sqlite3  # need this for rtree indexing on windows
except ImportError:
    import sqlite3


from context.types import LogEvent


def set_status(text):
    sys.stdout.write(text + "\n")
    sys.stdout.flush()


def create_tables(c):
    c.execute("""
        CREATE TABLE IF NOT EXISTS cbtv_events(
            id integer primary key,
            thread_id integer not null,
            start_location text not null,   end_location text,
            start_time float not null,      end_time float,
            start_type char(5) not null,    end_type char(5),
            start_text text,                end_text text
        );
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS cbtv_threads(
            id integer not null,
            node varchar(32) not null,
            process integer not null,
            thread varchar(32) not null
        );
    """)


def progress_file(log_file):
    fp = open(log_file)
    fp.seek(0, 2)
    f_size = fp.tell()
    fp.seek(0, 0)
    timestamp = 0
    for n, line in enumerate(fp):
        if n % 10000 == 0:
            time_taken = time() - timestamp
            set_status("Imported %d events (%d%%, %d/s)" % (n, fp.tell() * 100.0 / f_size, 1000/time_taken))
            timestamp = time()
        yield line
    fp.close()


class Thread(object):
    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.stack = []
        self.lock = None


def compile_log(log_file, database_file, append=False):
    if not append and os.path.exists(database_file):
        os.unlink(database_file)
    db = sqlite3.connect(database_file)
    c = db.cursor()
    create_tables(c)

    thread_name_to_id = {}
    #thread_names = list(c.execute("SELECT node, process, thread FROM cbtv_threads ORDER BY id"))
    threads = []
    thread_count = 0

    sqlInsertBookmark = """
        INSERT INTO cbtv_events(thread_id, start_location, start_time, start_type, start_text)
        VALUES(?, ?, ?, ?, ?)
    """
    sqlInsertEvent = """
        INSERT INTO cbtv_events(
            thread_id,
            start_location, start_time, start_type, start_text,
            end_location, end_time, end_type, end_text
        )
        VALUES(
            ?,
            ?, ?, ?, ?,
            ?, ?, ?, ?
        )
    """

    first_event_start = 0
    for line in progress_file(log_file):
        e = LogEvent(line.decode("utf-8"))

        thread_name = e.thread_id()
        if thread_name not in thread_name_to_id:
			threads.append(Thread(thread_count, thread_name))
			thread_name_to_id[thread_name] = thread_count
			thread_count += 1
        thread = threads[thread_name_to_id[thread_name]]

        if first_event_start == 0:
            first_event_start = e.timestamp

        if e.type == "START":
            thread.stack.append(e)

        if e.type == "ENDOK" or e.type == "ENDER":
            if len(thread.stack) > 0:
                s = thread.stack.pop()
                c.execute(
                    sqlInsertEvent, (
                        thread.id,
                        s.location, s.timestamp, s.type, s.text,
                        e.location, e.timestamp, e.type, e.text,
                    )
                )

        if e.type == "BMARK":
            c.execute(
                sqlInsertBookmark,
                (thread.id, e.location, e.timestamp, e.type, e.text)
            )

    c.execute("DELETE FROM cbtv_threads")
    for idx, thread in enumerate(threads):
        (node, process, osthread) = thread.name.split()
        c.execute("""
            INSERT INTO cbtv_threads(id, node, process, thread)
            VALUES(?, ?, ?, ?)
        """, (idx, node, process, osthread))

    set_status("Indexing bookmarks...")

    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_start_type_time ON cbtv_events(start_type, start_time)
    """)  # searching for bookmarks

    set_status("Indexing events...")

    c.execute("""
        CREATE VIRTUAL TABLE cbtv_events_index USING rtree(id, start_time, end_time)
    """)
    c.execute("""
        INSERT INTO cbtv_events_index
        SELECT id, start_time-?, end_time-?
        FROM cbtv_events
        WHERE start_time IS NOT NULL AND end_time IS NOT NULL
    """, (first_event_start, first_event_start))
    # c2 = db.cursor()
    # for row in c.execute("SELECT * FROM cbtv_events WHERE start_time IS NOT NULL AND end_time IS NOT NULL"):
    #    e = Event(row)
    #    print(type(e.id), type(e.start_time), type(e.end_time))
    #    c2.execute("INSERT INTO cbtv_events_index VALUES (?, ?, ?)", (e.id, e.start_time, e.end_time))
    # c2.close()

    c.close()
    db.commit()


def main(args=sys.argv):
    parser = argparse.ArgumentParser(description='Compile .ctxt to .cbin')
    parser.add_argument('log_file', help='a .ctxt file to compile')
    parser.add_argument('-o', '--output', help='.cbin file to write to')
    args = parser.parse_args()

    log_file = args.log_file
    database_file = args.output or log_file.replace(".ctxt", ".cbin")
    compile_log(log_file, database_file)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
