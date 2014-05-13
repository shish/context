import os
from time import time
try:
    import pysqlite2.dbapi2 as sqlite3  # need this for rtree indexing on windows
except ImportError:
    import sqlite3


from .types import LogEvent


def store(c, events):
    c.executemany(
        """
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
        """, events
    )


def compile_log(log_file, database_file, app=None, append=False):
    if not append and os.path.exists(database_file):
        os.unlink(database_file)
    db = sqlite3.connect(database_file)
    c = db.cursor()
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

    thread_names = list(c.execute("SELECT node, process, thread FROM cbtv_threads ORDER BY id"))
    thread_stacks = []

    fp = open(log_file)
    fp.seek(0, 2)
    f_size = fp.tell()
    fp.seek(0, 0)
    first_event_start = 0
    events = []
    timestamp = time()
    for n, line in enumerate(fp):
        if n % 10000 == 0:
            time_taken = time() - timestamp
            app.set_status("Imported %d events (%d%%, %d/s)" % (n, fp.tell() * 100.0 / f_size, 1000/time_taken))
            timestamp = time()

        e = LogEvent(line.decode("utf-8"))

        thread_name = e.thread_id()
        if thread_name not in thread_names:
            thread_names.append(thread_name)
            thread_stacks.append([])
        thread_id = thread_names.index(thread_name)

        if first_event_start == 0:
            first_event_start = e.timestamp

        if e.type == "BMARK":
            c.execute(
                """
                INSERT INTO cbtv_events(thread_id, start_location, start_time, start_type, start_text)
                VALUES(?, ?, ?, ?, ?)
                """,
                (thread_id, e.location, e.timestamp, e.type, e.text)
            )

        if e.type == "START":
            thread_stacks[thread_id].append(e)

        if e.type == "ENDOK" or e.type == "ENDER":
            try:
                s = thread_stacks[thread_id].pop()
            except IndexError:
                # the log started with an END
                continue
            events.append((
                thread_id,
                s.location, s.timestamp, s.type, s.text,
                e.location, e.timestamp, e.type, e.text,
            ))
            if len(events) == 1000:
                store(c, events)
                events = []
    if events:
        store(c, events)
    fp.close()

    c.execute("DELETE FROM cbtv_threads")
    for idx, thr in enumerate(thread_names):
        (node, process, thread) = thr.split()
        c.execute("""
            INSERT INTO cbtv_threads(id, node, process, thread)
            VALUES(?, ?, ?, ?)
        """, (idx, node, process, thread))

    app.set_status("Indexing bookmarks...")

    c.execute("CREATE INDEX IF NOT EXISTS idx_start_type_time ON cbtv_events(start_type, start_time)")

    app.set_status("Indexing events...")

    c.execute("CREATE VIRTUAL TABLE cbtv_events_index USING rtree(id, start_time, end_time)")
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

    app.set_status("")
