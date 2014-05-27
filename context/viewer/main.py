#!/usr/bin/python

# todo:
# full-file navigation
# - cbtv_events logs can last for hours, but only a minute at a time is
#   sensibly viewable
# mark lock claim / release
# - seeing what is locking software is good

from __future__ import print_function

try:
    import pysqlite2.dbapi2 as sqlite3  # need this for rtree indexing on windows
except ImportError:
    import sqlite3

try:
    from Tkinter import Tk, Toplevel
    from Tkinter import DoubleVar, IntVar
    from Tkinter import Label, Scrollbar, Text, Menu, Frame, Spinbox, PhotoImage, Listbox, Canvas, Button
    from Tkinter import N, E, S, W, SW, NW, SE, ALL, END, VERTICAL, HORIZONTAL, CENTER, WORD, LEFT, RIGHT, BOTH, Y
    from tkMessageBox import showerror
    from tkFileDialog import askopenfilename  # , asksaveasfilename
    have_tk = True
except ImportError:
    have_tk = False

try:
    from ttk import Button, Sizegrip
    have_ttk = True
except ImportError:
    have_ttk = False

from optparse import OptionParser
from base64 import b64decode
import subprocess
import ConfigParser
import datetime
import sys
import time
import os

try:
    from context.version import VERSION
except ImportError as ie:
    VERSION = "v0.0.0"

from context.viewer.cbtk import set_icon, win_center, resource
from context.viewer.util import conditional, gen_colour, shrink
import context.viewer.data as data


NAME = "Context"
ROW_HEIGHT = 140
BLOCK_HEIGHT = 20
MIN_PPS = 1
MAX_PPS = 5000
MIN_SEC = 1
MAX_SEC = 600

if VERSION.endswith("-demo"):
    NAME = NAME + ": Non-commercial / Evaluation Version"

os.environ["PATH"] = os.environ.get("PATH", "") + ":%s" % os.path.dirname(sys.argv[0])


class Event(object):
    __slots__ = [
        "id", "thread_id",
        "start_location", "end_location",
        "start_time", "end_time",
        "start_type", "end_type",
        "start_text", "end_text",

        "text", "length",
    ]

    def __init__(self, row):
        (
            self.id,
            self.thread_id,
            self.start_location, self.end_location,
            self.start_time, self.end_time,
            self.start_type, self.end_type,
            self.start_text, self.end_text,
        ) = row

        if self.start_text == self.end_text or self.end_text == "":
            self.text = self.start_text
        else:
            self.text = self.start_text + "\n" + self.end_text

        self.length = self.end_time - self.start_time


class _App:
    #########################################################################
    # GUI setup
    #########################################################################
    def __menu(self, master):
        menubar = Menu(master)

        def file_menu():
            menu = Menu(menubar, tearoff=0)
            menu.add_command(label="Open ctxt / cbin", command=self.open_file)
            # menu.add_command(label="Append ctxt", command=self.append_file)
            menu.add_separator()
            menu.add_command(label="Exit", command=self.save_settings_and_quit)
            return menu
        menubar.add_cascade(label="File", menu=file_menu())

        def view_menu():
            menu = Menu(menubar, tearoff=0)
            menu.add_checkbutton(label="Auto-render", variable=self.render_auto)
            # menu.add_command(label="Filter threads", command=None)
            return menu
        menubar.add_cascade(label="View", menu=view_menu())

        def analyse_menu():
            # def timechart():
            #    _TimeChart(master, self.output.get("0.0", END))
            menu = Menu(menubar, tearoff=0)
            # menu.add_command(label="Time Chart", command=timechart)
            return menu
        # menubar.add_cascade(label="Analyse", menu=analyse_menu())

        def help_menu():
            def show_about():
                t = Toplevel(master)
                t.title("About")
                t.transient(master)
                t.resizable(False, False)
                Label(t, image=self.img_logo).grid(column=0, row=0, sticky=(E, W))
                Label(t, text="Context %s" % VERSION, anchor=CENTER).grid(column=0, row=1, sticky=(E, W))
                Label(t, text="(c) 2011-2014 Shish", anchor=CENTER).grid(column=0, row=2, sticky=(E, W))
                Button(t, text="Close", command=t.destroy).grid(column=0, row=3, sticky=(E,))
                win_center(t)

            def show_docs():
                t = Toplevel(master)
                t.title("Context Documentation")
                t.transient(master)
                scroll = Scrollbar(t, orient=VERTICAL)
                tx = Text(
                    t,
                    wrap=WORD,
                    yscrollcommand=scroll.set,
                )
                scroll['command'] = tx.yview
                scroll.pack(side=RIGHT, fill=Y, expand=1)
                tx.pack(fill=BOTH, expand=1)
                tx.insert("0.0", b64decode(data.README).replace("\r", ""))
                tx.configure(state="disabled")
                tx.focus_set()
                win_center(t)

            def show_license():
                t = Toplevel(master)
                t.title("Context Licenses")
                t.transient(master)
                scroll = Scrollbar(t, orient=VERTICAL)
                tx = Text(
                    t,
                    wrap=WORD,
                    yscrollcommand=scroll.set,
                )
                scroll['command'] = tx.yview
                scroll.pack(side=RIGHT, fill=Y, expand=1)
                tx.pack(fill=BOTH, expand=1)
                tx.insert("0.0", b64decode(data.LICENSE).replace("\r", ""))
                tx.configure(state="disabled")
                tx.focus_set()
                win_center(t)

            helpmenu = Menu(menubar, tearoff=0)
            helpmenu.add_command(label="About", command=show_about)
            helpmenu.add_command(label="Documentation", command=show_docs)
            helpmenu.add_command(label="License", command=show_license)
            return helpmenu
        menubar.add_cascade(label="Help", menu=help_menu())

        master.config(menu=menubar)

        return menubar

    def __control_box(self, master):
        f = Frame(master)

        def _la(t):
            Label(f,
                text=t
            ).pack(side="left")

        def _sp(fr, t, i, v, w=10):
            Spinbox(f,
                from_=fr, to=t, increment=i,
                textvariable=v, width=w
            ).pack(side="left")

        def _bu(t, c):
            if isinstance(t, PhotoImage):
                if have_ttk:
                    Button(f,
                        image=t, command=c, padding=0
                    ).pack(side="right")
                else:
                    Button(f,
                        image=t, command=c,
                    ).pack(side="right")
            else:
                if have_ttk:
                    Button(f,
                        text=t, command=c, padding=0
                    ).pack(side="right", fill=Y)
                else:
                    Button(f,
                        text=t, command=c,
                    ).pack(side="right", fill=Y)

        _la("  Start ")
        _sp(0, int(time.time()), 10, self.render_start, 15)
        _la("  Seconds ")
        _sp(MIN_SEC, MAX_SEC, 1, self.render_len, 3)
        _la("  Pixels per second ")
        _sp(MIN_PPS, MAX_PPS, 100, self.scale, 5)
        _la("  Cutoff (ms) ")
        _sp(0, 1000, 1, self.render_cutoff, 3)
        Button(f, text="Render", command=self.update).pack(side=LEFT)  # padding=0

        _bu(self.img_end, self.end_event)
        _bu(self.img_next, self.next_event)
        _bu("Bookmarks", self.open_bookmarks)
        _bu(self.img_prev, self.prev_event)
        _bu(self.img_start, self.start_event)

        f.pack()
        return f

    def __scrubber(self, master):
        sc = Canvas(
            master,
            width=800, height=20,
            background="white",
        )

        def sc_goto(e):
            width_fraction = float(e.x) / sc.winfo_width()
            ev_s = self.get_earliest_bookmark_after(0)
            ev_e = self.get_latest_bookmark_before(sys.maxint)
            ev_l = ev_e - ev_s
            self.render_start.set(ev_s + ev_l * width_fraction - float(self.render_len.get()) / 2)
            if not self.render_auto.get():
                self.update()
            self.canvas.xview_moveto(0.5)
        sc.bind("<1>", sc_goto)

        def resize(event):
            if self.c:
                self.render_scrubber_activity()
                self.render_scrubber_arrow()
            # sc.coords(line, 0, 0, event.width, event.height)
        sc.bind("<Configure>", resize)

        return sc

    def __init__(self, master, database_file):
        self.master = master
        self.char_w = -1
        self.soft_scale = 1.0
        self.window_ready = False
        self.data = []
        self.scrubber = None  # render is called before init finished?
        self.sc_activity = None
        self.event_idx_offset = 0
        self._last_log_dir = os.path.expanduser("~/")
        self.c = None  # database connection
        self.compiler = None

        try:
            os.makedirs(os.path.expanduser(os.path.join("~", ".config")))
        except OSError:
            pass
        self.config_file = os.path.expanduser(os.path.join("~", ".config", "context.cfg"))

        self.threads = []
        self.render_start = DoubleVar(master, 0)
        self.render_len = IntVar(master, 10)
        self.render_cutoff = IntVar(master, 1)
        self.render_auto = IntVar(master, 1)
        self.scale = IntVar(master, 1000)

        self.load_settings()
        master.protocol("WM_DELETE_WINDOW", self.save_settings_and_quit)

        self.render_start.trace_variable("w", lambda *x: conditional(self.render_auto, self.update))
        self.render_len.trace_variable("w", lambda *x: conditional(self.render_auto, self.update))
        self.render_cutoff.trace_variable("w", lambda *x: conditional(self.render_auto, self.render))
        self.scale.trace_variable("w", lambda *x: conditional(self.render_auto, self.render))

        self.img_start = PhotoImage(data=data.start)
        self.img_prev = PhotoImage(data=data.prev)
        self.img_next = PhotoImage(data=data.next)
        self.img_end = PhotoImage(data=data.end)
        self.img_logo = PhotoImage(data=data.context_name)

        self.h = Scrollbar(master, orient=HORIZONTAL)
        self.v = Scrollbar(master, orient=VERTICAL)
        self.canvas = Canvas(
            master,
            width=800, height=600,
            background="white",
            xscrollcommand=self.h.set,
            yscrollcommand=self.v.set,
        )
        self.h['command'] = self.canvas.xview
        self.v['command'] = self.canvas.yview

        self.controls = self.__control_box(master)
        self.menu = self.__menu(master)
        if have_ttk:
            self.grip = Sizegrip(master)
        self.scrubber = self.__scrubber(master)
        self.status = Label(master, text="")

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)
        self.controls.grid(column=0, row=0, sticky=(W, E), columnspan=2)
        self.canvas.grid(column=0, row=1, sticky=(N, W, E, S))
        self.v.grid(column=1, row=1, sticky=(N, S))
        self.h.grid(column=0, row=2, sticky=(W, E))
        self.scrubber.grid(column=0, row=3, sticky=(W, E), columnspan=2)
        self.status.grid(column=0, row=4, sticky=(W, E))
        if have_ttk:
            self.grip.grid(column=1, row=4, sticky=(S, E))

        self.canvas.bind("<4>", lambda e: self.scale_view(e, 1.0 * 1.1))
        self.canvas.bind("<5>", lambda e: self.scale_view(e, 1.0 / 1.1))

        # in windows, mouse wheel events always go to the root window o_O
        self.master.bind("<MouseWheel>", lambda e: self.scale_view(e,
            ((1.0 * 1.1) if e.delta > 0 else (1.0 / 1.1))
        ))

        # Drag based movement
        # def _sm(e):
        #    self.st = self.render_start.get()
        #    self.sx = e.x
        #    self.sy = e.y
        # def _cm(e):
        #    self.render_start.set(self.st + float(self.sx - e.x)/self.scale.get())
        #    self.render()
        # self.canvas.bind("<1>", _sm)
        # self.canvas.bind("<B1-Motion>", _cm)

        self.master.update()

        self.window_ready = True

        if database_file:
            self.load_file(database_file)

    def set_status(self, text):
        if text:
            print(text)
        self.status.config(text=text)
        self.master.update()

    def open_file(self):
        filename = askopenfilename(
            filetypes=[("All Supported Types", "*.ctxt *.cbin"), ("Context Text", "*.ctxt"), ("Context Binary", "*.cbin")],
            initialdir=self._last_log_dir
        )
        if filename:
            try:
                self.load_file(filename)
            except Exception as e:
                self.set_status("Error loading file: %s" % str(e))

    def load_file(self, given_file):
        if not os.path.exists(given_file):
            showerror("Error", "Context dump file '%s' does not exist" % given_file)
            return

        self._last_log_dir = os.path.dirname(given_file)

        path, _ext = os.path.splitext(given_file)

        log_file = path + ".ctxt"
        database_file = path + ".cbin"

        # if the user picked a log file, compile it (unless an
        # up-to-date version already exists)
        if given_file == log_file:
            needs_recompile = False

            if not os.path.exists(database_file):
                needs_recompile = True
                self.set_status("Compiled log not found, compiling")
            elif os.stat(log_file).st_mtime > os.stat(database_file).st_mtime:
                needs_recompile = True
                self.set_status("Compiled log is out of date, recompiling")

            if needs_recompile:
                #self.compiler = subprocess.Popen(["context-compiler", log_file, "-o", database_file], stdout=subprocess.PIPE)
                self.compiler = subprocess.Popen(["context-compiler", log_file], stdout=subprocess.PIPE)
                while True:
                    line = self.compiler.stdout.readline()
                    if line:
                        self.set_status(line.strip())
                    else:
                        break

        self.c = sqlite3.connect(database_file)

        try:
            self.c.execute("SELECT * FROM cbtv_events LIMIT 1")
        except sqlite3.OperationalError:
            showerror("Error", "'%s' is not a valid context dump" % database_file, parent=self.master)
            return

        # fast because the data is split off into a tiny table
        self.threads = [
            "-".join([str(c) for c in r])
            for r
            in self.c.execute("SELECT node, process, thread FROM cbtv_threads ORDER BY id")
        ]

        self.event_idx_offset = self.get_earliest_bookmark_after(0)

        self.master.title(NAME + ": " + database_file)

        self.render_start.set(self.get_earliest_bookmark_after(0))

    def load_settings(self):
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.readfp(file(self.config_file))
            if cp.has_section("gui"):
                if cp.has_option("gui", "render_len"):
                    self.render_len.set(cp.getint("gui", "render_len"))
                if cp.has_option("gui", "scale"):
                    self.scale.set(cp.getint("gui", "scale"))
                if cp.has_option("gui", "render_cutoff"):
                    self.render_cutoff.set(cp.getint("gui", "render_cutoff"))
                if cp.has_option("gui", "render_auto"):
                    self.render_auto.set(cp.getint("gui", "render_auto"))
                if cp.has_option("gui", "last_log_dir"):
                    self._last_log_dir = cp.get("gui", "last_log_dir")
        except Exception as e:
            print("Error loading settings from %s:\n  %s" % (self.config_file, e))

    def save_settings(self):
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.add_section("gui")
            cp.set("gui", "render_len", str(self.render_len.get()))
            cp.set("gui", "scale", str(self.scale.get()))
            cp.set("gui", "render_cutoff", str(self.render_cutoff.get()))
            cp.set("gui", "render_auto", str(self.render_auto.get()))
            cp.set("gui", "last_log_dir", self._last_log_dir)
            cp.write(file(self.config_file, "w"))
        except Exception as e:
            print("Error writing settings to %s:\n  %s" % (self.config_file, e))

    def save_settings_and_quit(self):
        self.save_settings()
        self.master.destroy()
        self.master.quit()

    #########################################################################
    # Navigation
    #########################################################################

    def get_earliest_bookmark_after(self, start_hint=0):
        return list(self.c.execute(
            "SELECT min(start_time) FROM cbtv_events WHERE start_time > ? AND start_type = 'BMARK'",
            [start_hint, ]
        ))[0][0]

    def get_latest_bookmark_before(self, end_hint=0):
        return list(self.c.execute(
            "SELECT max(start_time) FROM cbtv_events WHERE start_time < ? AND start_type = 'BMARK'",
            [end_hint, ]
        ))[0][0]

    def end_event(self):
        next_ts = self.get_latest_bookmark_before(sys.maxint)
        if next_ts:
            self.render_start.set(next_ts)
        self.canvas.xview_moveto(0)

    def next_event(self):
        next_ts = self.get_earliest_bookmark_after(self.render_start.get())
        if next_ts:
            self.render_start.set(next_ts)
        self.canvas.xview_moveto(0)

    def prev_event(self):
        prev_ts = self.get_latest_bookmark_before(self.render_start.get())
        if prev_ts:
            self.render_start.set(prev_ts)
        self.canvas.xview_moveto(0)

    def start_event(self):
        next_ts = self.get_earliest_bookmark_after(0)
        if next_ts:
            self.render_start.set(next_ts)
        self.canvas.xview_moveto(0)

    def open_bookmarks(self):
        # base gui
        t = Toplevel(self.master)
        t.lift(self.master)
        t.grid_columnconfigure(0, weight=1)
        t.grid_rowconfigure(0, weight=1)
        t.transient(self.master)
        t.title("Bookmarks")

        li = Listbox(t, height=10, width=40)
        li.grid(column=0, row=0, sticky=(N, E, S, W))

        sb = Scrollbar(t, orient=VERTICAL, command=li.yview)
        sb.grid(column=1, row=0, sticky=(N, S))

        li.config(yscrollcommand=sb.set)

        # render the laid out window before adding data;
        # the alternative is rendering the non-laid-out window
        t.update()

        # load data
        bm_values = []
        for ts, tx, et in self.c.execute("SELECT start_time, start_text, end_text FROM cbtv_events WHERE start_type = 'BMARK' ORDER BY start_time"):
            bm_values.append(ts)
            tss = datetime.datetime.fromtimestamp(ts).strftime("%Y/%m/%d %H:%M:%S")  # .%f
            li.insert(END, "%s: %s" % (tss, tx or et))

        # load events
        def _lbox_selected(*args):
            selected_idx = int(li.curselection()[0])
            self.render_start.set(bm_values[selected_idx])
            self.canvas.xview_moveto(0)
        li.bind('<Double-Button-1>', _lbox_selected)

    #########################################################################
    # Rendering
    #########################################################################

    def _count_events_at(self, n, m):
        try:
            count = self.c.execute(
                "SELECT count(*) FROM cbtv_events_index WHERE start_time < ? AND end_time > ?",
                (m - self.event_idx_offset, n - self.event_idx_offset)
            ).fetchone()[0]
            # print("Found", count ,"events at", n)
            return count
        except sqlite3.OperationalError:
            return 0

    def scale_view(self, e=None, n=1.0):
        # get the old pos
        if e:
            _xv = self.canvas.xview()
            left_edge = _xv[0]
            width = _xv[1] - _xv[0]
            width_fraction = float(e.x) / self.canvas.winfo_width()
            x_pos = left_edge + width * width_fraction
        # scale
        if n != 1:
            self.soft_scale *= n
            self.canvas.scale("event", 0, 0, n, 1)
            self.canvas.scale("lock", 0, 0, n, 1)
            for t in self.canvas.find_withtag("time_label"):
                val = self.canvas.itemcget(t, 'text')[2:]
                self.canvas.itemconfigure(t, text=" +%.4f" % (float(val) / n))
            for t in self.canvas.find_withtag("event_tip"):
                self.canvas.itemconfigure(t, width=float(self.canvas.itemcget(t, 'width')) * n)  # this seems slow? sure something similar was faster...
            for t in self.canvas.find_withtag("event_label"):
                self.canvas.itemconfigure(t, width=float(self.canvas.itemcget(t, 'width')) * n)  # this seems slow? sure something similar was faster...
                w = int(self.canvas.itemcget(t, 'width'))
                tx = self.truncate_text(" " + self.original_texts[t], w)
                self.canvas.itemconfigure(t, text=tx)  # this seems slow? sure something similar was faster...
            self.canvas.delete("grid")
            self.render_base()
            self.canvas.configure(scrollregion=shrink(self.canvas.bbox("grid"), 2))
        # scroll the canvas so that the mouse still points to the same place
        if e:
            _xv = self.canvas.xview()
            new_width = _xv[1] - _xv[0]
            self.canvas.xview_moveto(x_pos - new_width * width_fraction)

    def truncate_text(self, text, w):
        return text.split("\n")[0][:w / self.char_w]

    def update(self):
        self.update_events()
        self.update_scrubber()
        self.render()

    def update_events(self):
        """
        Data settings changed, get new data and re-render
        """
        if not self.window_ready:
            # update() is called a couple of times during init()
            return

        try:
            s = self.render_start.get()
            e = self.render_start.get() + self.render_len.get()
        except ValueError:
            return

        try:
            self.n = 0

            def progress(*args):
                try:
                    self.n += 1
                    self.set_status("Loading... (%dk opcodes)" % (self.n * 10))
                    return 0
                except Exception as e:
                    return 1  # non-zero = cancel query
            self.c.set_progress_handler(progress, 10000)

            try:
                self.data = [Event(row) for row in self.c.execute(
                    """
                        SELECT *
                        FROM cbtv_events
                        WHERE id IN (SELECT id FROM cbtv_events_index WHERE end_time > ? AND start_time < ?)
                        AND (end_time - start_time) * 1000 >= ?
                        ORDER BY start_time ASC, end_time DESC
                    """,
                    (s - self.event_idx_offset, e - self.event_idx_offset, self.render_cutoff.get())
                )]
            except sqlite3.OperationalError:
                self.data = []

            self.c.set_progress_handler(None, 0)
        finally:
            self.set_status("")

    def update_scrubber(self):
        sc = self.scrubber

        if not sc:
            return

        # events start / end / length
        ev_s = self.get_earliest_bookmark_after(0)
        ev_e = self.get_latest_bookmark_before(sys.maxint)
        ev_l = ev_e - ev_s

        if self.sc_activity is None:
            # self.sc_activity = [self._count_events_at(ev_s + (ev_l * float(n)/sc_w)) for n in range(0, sc_w)]
            self.sc_activity = [0] * 1000

            self._scrubber_data_point = 0

            def task():
                if self._scrubber_data_point >= len(self.sc_activity):
                    return
                self.sc_activity[self._scrubber_data_point] = self._count_events_at(
                    ev_s + (ev_l * float(self._scrubber_data_point) / len(self.sc_activity)),
                    ev_s + (ev_l * float(self._scrubber_data_point + 1) / len(self.sc_activity))
                )
                self._scrubber_data_point = self._scrubber_data_point + 1
                if self._scrubber_data_point % 10 == 0:
                    self.render_scrubber_activity(self._scrubber_data_point)
                    self.render_scrubber_arrow()
                self.master.after(2, task)
            task()

    def render(self):
        """
        Render settings changed, re-render with existing data
        """
        if not MIN_PPS < self.scale.get() < MAX_PPS:
            return
        self.soft_scale = 1.0
        self.render_clear()
        self.render_scrubber_activity()
        self.render_scrubber_arrow()
        self.render_base()
        self.render_data()

    def render_clear(self):
        """
        clear the canvas and any cached variables
        """
        self.canvas.delete(ALL)
        self.original_texts = {}
        self.tooltips = {}
        self.canvas.configure(scrollregion=(
            0, 0,
            self.render_len.get() * self.scale.get(),
            len(self.threads) * ROW_HEIGHT + 20
        ))
        if self.char_w == -1:
            t = self.canvas.create_text(0, 0, font="TkFixedFont", text="_", anchor=NW)
            bb = self.canvas.bbox(t)
            # [2]-[0]=10, but trying by hand, 8px looks better on win7
            # 7px looks right on linux, not sure what [2]-[0] is there,
            # hopefully 9px, so "-2" always helps?
            self.char_w = bb[2] - bb[0] - 2
            self.canvas.delete(t)

    def render_scrubber_activity(self, length=None):
        sc = self.scrubber

        if not sc:
            return

        if self.sc_activity is not None:
            sc.delete("activity")
            activity_peak = max(self.sc_activity)
            if activity_peak == 0:
                return
            for n in range(0, length or len(self.sc_activity)):
                col = gen_colour(self.sc_activity[n], activity_peak)
                sc.create_rectangle(
                    int(float(n) / len(self.sc_activity) * sc.winfo_width()), 1,
                    int(float(n + 1) / len(self.sc_activity) * sc.winfo_width()), 20,
                    fill=col, outline=col, tags="activity",
                )

    def render_scrubber_arrow(self):
        sc = self.scrubber

        if not self.window_ready:
            return

        if not sc:
            return

        # events start / end / length
        ev_s = self.get_earliest_bookmark_after(0)
        ev_e = self.get_latest_bookmark_before(sys.maxint)
        ev_l = ev_e - ev_s

        if ev_l == 0:  # only one bookmark
            return

        # view start / end / length
        vi_s = self.render_start.get()
        vi_e = self.render_start.get() + self.render_len.get()
        # vi_l = vi_e - vi_s

        # scrubber width
        sc_w = sc.winfo_width()

        sc.delete("arrow")

        # arrow
        start_abs = vi_s
        start_rel = start_abs - ev_s
        start_fraction = start_rel / ev_l
        start_scaled = start_fraction * sc_w
        start = start_scaled

        end_abs = vi_e
        end_rel = end_abs - ev_s
        end_fraction = end_rel / ev_l
        end_scaled = end_fraction * sc_w
        end = end_scaled

        # left edge
        sc.create_line(
            start, 1,
            start, 20,
            fill="#000", tags="arrow",
        )
        sc.create_line(
            start, 10,
            start + 5, 15,
            fill="#000", tags="arrow",
        )
        sc.create_line(
            start, 10,
            start + 5, 5,
            fill="#000", tags="arrow",
        )

        # right edge
        sc.create_line(
            end, 1,
            end, 20,
            fill="#000", tags="arrow",
        )
        sc.create_line(
            end, 10,
            end - 5, 15,
            fill="#000", tags="arrow",
        )
        sc.create_line(
            end, 10,
            end - 5, 5,
            fill="#000", tags="arrow",
        )

        # join
        sc.create_line(
            start, 10,
            end, 10,
            fill="#000", tags="arrow",
        )

    def render_base(self):
        """
        Render grid lines and markers
        """
        _rs = self.render_start.get()
        _rl = self.render_len.get()
        _sc = self.scale.get() * self.soft_scale

        rs_px = int(_rl * _sc)
        rl_px = int(_rl * _sc)

        for n in range(rs_px, rs_px + rl_px, 100):
            label = " +%.4f" % (float(n) / _sc - _rl)
            self.canvas.create_line(n - rs_px, 0, n - rs_px, 20 + len(self.threads) * ROW_HEIGHT, fill="#CCC", tags="grid")
            self.canvas.create_text(n - rs_px, 5, text=label, anchor=NW, tags="time_label grid")

        for n in range(0, len(self.threads)):
            self.canvas.create_line(0, 20 + ROW_HEIGHT * n, rl_px, 20 + ROW_HEIGHT * n, tags="grid")
            self.canvas.create_text(0, 20 + ROW_HEIGHT * (n + 1) - 5, text=" " + self.threads[n], anchor=SW, tags="grid")

        self.canvas.tag_lower("grid")

    def render_data(self):
        """
        add the event rectangles
        """
        if not self.window_ready:
            # update() is called a couple of times during init()
            return

        _rs = self.render_start.get()
        _rc = self.render_cutoff.get()
        _sc = self.scale.get()

        # thread_level_starts = [[], ] * len(self.threads)  # this bug is subtle and hilarious
        thread_level_ends = [[] for n in range(len(self.threads))]

        event_count = len(self.data) - 1
        shown = 0
        for n, event in enumerate(self.data):
            if n % 1000 == 0 or n == event_count:
                self.set_status("Rendered %d events (%d%%)" % (n, float(n) * 100 / event_count))
                self.master.update()
            thread_idx = event.thread_id

            if event.start_type == "START":
                while thread_level_ends[thread_idx] and thread_level_ends[thread_idx][-1] <= event.start_time:
                    thread_level_ends[thread_idx].pop()
                thread_level_ends[thread_idx].append(event.end_time)
                stack_len = len(thread_level_ends[thread_idx]) - 1
                if (event.end_time - event.start_time) * 1000 < _rc:
                    continue
                shown += 1
                if shown == 500 and VERSION.endswith("-demo"):
                    showerror("Demo Limit", "The evaluation build is limited to showing 500 events at a time, so rendering has stopped")
                    break
                self.show_event(
                    event, _rs, _sc,
                    thread_idx, stack_len,
                )

            elif event.start_type == "BMARK":
                # note that when loading data, we currently filter for
                # "start_type=START" for a massive indexed speed boost
                # so there are no bookmarks. We may want to load bookmarks
                # into a separate array?
                pass  # render bookmark

            elif event.start_type == "LOCKW" or event.start_type == "LOCKA":
                self.show_lock(
                    event, _rs, _sc,
                    thread_idx,
                )

        self.set_status("")

    def show_event(self, event, offset_time, scale_factor, thread, level):
        function = event.start_location
        ok = event.end_type == "ENDOK"

        start_px = int((event.start_time - offset_time) * scale_factor)
        length_px = int(event.length * scale_factor)

        tip = "%dms @%dms: %s\n%s" % (
            (event.end_time - event.start_time) * 1000,
            (event.start_time - offset_time) * 1000,
            function, event.text
        )

        fill = "#CFC" if ok else "#FCC"
        outl = "#484" if ok else "#844"
        r = self.canvas.create_rectangle(
            start_px, 20 + thread * ROW_HEIGHT + level * BLOCK_HEIGHT,
            start_px + length_px, 20 + thread * ROW_HEIGHT + level * BLOCK_HEIGHT + BLOCK_HEIGHT,
            fill=fill, outline=outl, tags="event",
        )
        t = self.canvas.create_text(
            start_px, 20 + thread * ROW_HEIGHT + level * BLOCK_HEIGHT + 3,
            text=self.truncate_text(" " + event.text, length_px), tags="event event_label", anchor=NW, width=length_px,
            font="TkFixedFont",
            state="disabled",
        )
        self.canvas.tag_raise(r)
        self.canvas.tag_raise(t)

        self.canvas.tag_bind(r, "<1>", lambda e: self._focus(r))

        self.original_texts[t] = event.text
        self.tooltips[r] = tip

        self.canvas.tag_bind(r, "<Enter>", lambda e: self._ttip_show(r))
        self.canvas.tag_bind(r, "<Leave>", lambda e: self._ttip_hide())

    def show_lock(self, event, offset_time, scale_factor, thread):
        start_px = int((event.start_time - offset_time) * scale_factor)
        length_px = int(event.length * scale_factor)

        fill = "#FDD" if event.start_type == "LOCKW" else "#DDF"
        r = self.canvas.create_rectangle(
            start_px, 20 + thread * ROW_HEIGHT,
            start_px + length_px, 20 + (thread + 1) * ROW_HEIGHT,
            fill=fill, outline=fill, tags="lock",
        )
        t = self.canvas.create_text(
            start_px + length_px, 20 + (thread + 1) * ROW_HEIGHT,
            text=self.truncate_text(event.text, length_px),
            tags="lock lock_label", anchor=SE, width=length_px,
            font="TkFixedFont",
            state="disabled",
            fill="#888",
        )
        self.canvas.tag_lower(t)
        self.canvas.tag_lower(r)

    def _focus(self, r):
        # scale the canvas so that the (selected item width + padding == screen width)
        canvas_w = self.canvas.bbox("grid")[2]
        view_w = self.canvas.winfo_width()
        rect_x = self.canvas.bbox(r)[0]
        rect_w = max(self.canvas.bbox(r)[2] - self.canvas.bbox(r)[0] + 20, 10)
        self.scale_view(n=float(view_w) / rect_w)

        # move the view so that the selected (item x1 = left edge of screen + padding)
        canvas_w = self.canvas.bbox("grid")[2]
        rect_x = self.canvas.bbox(r)[0] - 5
        self.canvas.xview_moveto(float(rect_x) / canvas_w)

    def _ttip_show(self, r):
        tip = self.tooltips[r]

        x0, y0, x1, y1 = self.canvas.bbox(r)

        if x0 < 0:
            x1 = x1 - x0
            x0 = x0 - x0

        t2 = self.canvas.create_text(
            x0 + 4, y0 + BLOCK_HEIGHT + 4,
            text=tip.strip(), width=400, tags="tooltip", anchor=NW,
            justify="left", state="disabled",
        )

        x0, y0, x1, y1 = self.canvas.bbox(t2)

        r2 = self.canvas.create_rectangle(
            x0 - 2, y0 - 1, x1 + 2, y1 + 2,
            state="disabled", fill="#FFA", outline="#AA8", tags="tooltip"
        )

        self.canvas.tag_raise(t2)

    def _ttip_hide(self):
        self.canvas.delete("tooltip")


def main(argv=sys.argv):
    filename = None

    parser = OptionParser()
    parser.add_option("-g", "--geometry", dest="geometry", default="770x600",
            help="location and size of window", metavar="GM")
    parser.add_option("-r", "--row-height", dest="row_height", default=140,
            type=int, help="height of the rows", metavar="PX")
    (options, args) = parser.parse_args(argv)

    # lol constants
    global ROW_HEIGHT
    ROW_HEIGHT = options.row_height

    if len(args) > 1:
        filename = args[1]

    if not have_tk:
        print("Couldn't find Tk libraries")
        return 1

    # set up the root window early, so we can control it (and hide it)
    # by default, showerror() will create a random blank window as root
    root = Tk()
    set_icon(root, "images/tools-icon")
    root.title(NAME)

    _App(root, filename)
    if options.geometry:
        root.geometry(options.geometry)
    root.mainloop()

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
