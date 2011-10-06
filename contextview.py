#!/usr/bin/python

# todo:
# full-file navigation
# - cbtv_events logs can last for hours, but only a minute at a time is
#   sensibly viewable
# mark lock claim / release
# - seeing what is locking software is good

from __future__ import print_function
from optparse import OptionParser
import ConfigParser
import threading
import datetime
import sqlite3
import sys
import time
import os


NAME = "Context"
ROW_HEIGHT = 140
BLOCK_HEIGHT = 20


#######################################################################
# Application API
#######################################################################

def compile_log(log_file, database_file, append=False):
    root = Tk()
    if os.name == "nt":
        root.wm_iconbitmap(default="images/boomtools.ico")
    root.title("Importing .ctxt")
    label = Label(root, text="Loading", width=30, anchor=CENTER)
    label.pack(padx=5, pady=5)
    root.update()

    if not append and os.path.exists(database_file):
        os.unlink(database_file)
    db = sqlite3.connect(database_file)
    c = db.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cbtv_events(
            start float not null,
            end float,
            node varchar(32) not null,
            process integer not null,
            thread varchar(32) not null,
            type char(5) not null,
            function text not null,
            text text not null
        )
    """)

    thread_names = []
    thread_stacks = []

    fp = open(log_file)
    fp.seek(0, 2)
    f_size = fp.tell()
    fp.seek(0, 0)
    for n, line in enumerate(fp):
        if n % 1000 == 0:
            label.configure(text="Loaded %d events (%d%%)" % (n, fp.tell()*100.0/f_size))
            root.update()

        parts = (timestamp, node, process, thread, type, function, text) = line.strip().split(" ", 6)

        thread_name = node+process+thread
        if thread_name not in thread_names:
            thread_names.append(thread_name)
            thread_stacks.append([])
        thread_id = thread_names.index(thread_name)

        if type == "BMARK":
            c.execute(
                "INSERT INTO cbtv_events VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (timestamp, timestamp, node, process, thread, type, function, text)
            )

        if type == "START":
            thread_stacks[thread_id].append(timestamp)

        if type == "ENDOK" or type == "ENDER":
            sp = thread_stacks[thread_id].pop()
            c.execute(
                "INSERT INTO cbtv_events VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
                (sp, timestamp, node, process, thread, type, function, text)
            )
    fp.close()

    label.configure(text="Indexing data...")
    root.update()

    c.execute("CREATE INDEX IF NOT EXISTS ts_idx ON cbtv_events(start, end)")
    c.execute("CREATE INDEX IF NOT EXISTS ty_idx ON cbtv_events(type)")
    c.close()
    db.commit()

    root.destroy()


#######################################################################
# GUI Out
#######################################################################

try:
    from Tkinter import *
    from ttk import *
    from tkMessageBox import *
    from tkFileDialog import askopenfilename, asksaveasfilename
    have_tk = True
except ImportError:
    try:
        from tkinter import *
        from tkinter.ttk import *
        #from tkMessageBox import * # python 3?
        have_tk = True
    except ImportError:
        have_tk = False


class _App:
    #########################################################################
    # GUI setup
    #########################################################################

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
                Button(f,
                    image=t, command=c, padding=0
                ).pack(side="right")
            else:
                Button(f,
                    text=t, command=c, padding=0
                ).pack(side="right", fill=Y)

        _la("  Start ")
        _sp(0, int(time.time()), 10, self.render_start, 15)
        _la("  Seconds ")
        _sp(1, 60, 1, self.render_len, 3)
        _la("  Pixels per second ")
        _sp(50, 5000, 100, self.scale, 5)

        _bu(self.img_end, self.end_event)
        _bu(self.img_next, self.next_event)
        _bu("Bookmarks", self.open_bookmarks)
        _bu(self.img_prev, self.prev_event)
        _bu(self.img_start, self.start_event)

        f.pack()
        return f

    def __init__(self, master, database_file):
        self.master = master
        self.char_w = -1

        try:
            os.makedirs(os.path.expanduser(os.path.join("~", ".config")))
        except OSError as e:
            pass
        self.config_file = os.path.expanduser(os.path.join("~", ".config", "context.cfg"))

        db = sqlite3.connect(database_file)
        self.c = db.cursor()

        self.threads = [n[0] for n in self.c.execute("SELECT DISTINCT thread FROM cbtv_events ORDER BY thread")]
        self.render_start = DoubleVar(master, 0)
        self.render_len = IntVar(master, 10)
        self.scale = IntVar(master, 1000)

        self.load_settings()
        master.protocol("WM_DELETE_WINDOW", self.save_settings_and_quit)

        self.render_start.trace_variable("w", self.update)
        self.render_len.trace_variable("w", self.update)
        self.scale.trace_variable("w", self.render)

        self.img_start = PhotoImage(file="images/start.gif")
        self.img_prev = PhotoImage(file="images/prev.gif")
        self.img_next = PhotoImage(file="images/next.gif")
        self.img_end = PhotoImage(file="images/end.gif")

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
        self.grip = Sizegrip(master)

        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(1, weight=1)
        self.controls.grid(column=0, row=0, sticky=(W, E), columnspan=2)
        self.canvas.grid(  column=0, row=1, sticky=(N, W, E, S))
        self.v.grid(       column=1, row=1, sticky=(N, S))
        self.h.grid(       column=0, row=2, sticky=(W, E))
        self.grip.grid(    column=1, row=2, sticky=(S, E))

        self.canvas.bind("<4>", lambda e: self.scale_view(e, 1.0 * 1.1))
        self.canvas.bind("<5>", lambda e: self.scale_view(e, 1.0 / 1.1))

        # in windows, mouse wheel events always go to the root window o_O
        self.master.bind("<MouseWheel>", lambda e: self.scale_view(e,
            ((1.0 * 1.1) if e.delta > 0 else (1.0 / 1.1))
        ))

        # Drag based movement
        #def _sm(e):
        #    self.st = self.render_start.get()
        #    self.sx = e.x
        #    self.sy = e.y
        #def _cm(e):
        #    self.render_start.set(self.st + float(self.sx - e.x)/self.scale.get())
        #    self.render()
        #self.canvas.bind("<1>", _sm)
        #self.canvas.bind("<B1-Motion>", _cm)

        self.render_start.set(self.get_start(0))

    def load_settings(self):
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.readfp(file(self.config_file))
            self.render_len.set(cp.getint("gui", "render_len"))
            self.scale.set(cp.getint("gui", "scale"))
            #self._file_opts['initialdir'] = cp.get("gui", "last-log-dir")
        except Exception as e:
            print("Error loading settings from %s:\n  %s" % (self.config_file, e))

    def save_settings(self):
        try:
            cp = ConfigParser.SafeConfigParser()
            cp.add_section("gui")
            cp.set("gui", "render_len", str(self.render_len.get()))
            cp.set("gui", "scale", str(self.scale.get()))
            #cp.set("gui", "last-log-dir", self._file_opts['initialdir'])
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

    def get_start(self, start_hint=1, io=None):
        if io:
            return list(self.c.execute(
                "SELECT min(start) FROM cbtv_events WHERE start > ? AND type = ?",
                [start_hint, io]
            ))[0][0]
        else:
            return list(self.c.execute(
                "SELECT min(start) FROM cbtv_events WHERE start > ?",
                [start_hint, ]
            ))[0][0]

    def get_end(self, end_hint=0, io=None):
        if io:
            return list(self.c.execute(
                "SELECT max(end) FROM cbtv_events WHERE end < ? AND type = ?",
                [end_hint, io]
            ))[0][0]
        else:
            return list(self.c.execute(
                "SELECT max(end) FROM cbtv_events WHERE end < ?",
                [end_hint, ]
            ))[0][0]

    def end_event(self):
        next_ts = self.get_end(sys.maxint, "BMARK")
        if next_ts:
            self.render_start.set(next_ts)
        self.canvas.xview_moveto(0)

    def next_event(self):
        next_ts = self.get_start(self.render_start.get(), "BMARK")
        if next_ts:
            self.render_start.set(next_ts)
        self.canvas.xview_moveto(0)

    def prev_event(self):
        prev_ts = self.get_end(self.render_start.get(), "BMARK")
        if prev_ts:
            self.render_start.set(prev_ts)
        self.canvas.xview_moveto(0)

    def start_event(self):
        next_ts = self.get_start(0, "BMARK")
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
        for ts, tx in self.c.execute("SELECT timestamp, text FROM cbtv_events WHERE type = 'BMARK' ORDER BY timestamp"):
            bm_values.append(ts)
            tss = datetime.datetime.fromtimestamp(ts).strftime("%Y/%m/%d %H:%M:%S")  # .%f
            li.insert(END, "%s: %s" % (tss, tx))

        # load events
        def _lbox_selected(*args):
            selected_idx = int(li.curselection()[0])
            self.render_start.set(bm_values[selected_idx])
            self.canvas.xview_moveto(0)
        li.bind('<Double-Button-1>', _lbox_selected)

    #########################################################################
    # Rendering
    #########################################################################

    def scale_view(self, e=None, n=1):
        # get the old pos
        if e:
            _xv = self.canvas.xview()
            left_edge = _xv[0]
            width = _xv[1] - _xv[0]
            width_fraction = float(e.x) / self.canvas.winfo_width()
            x_pos = left_edge + width * width_fraction
        # scale
        if n != 1:
            self.canvas.scale(ALL, 0, 0, n, 1)
            for t in self.canvas.find_withtag("event_tip"):
                self.canvas.itemconfigure(t, width=float(self.canvas.itemcget(t, 'width'))*n)  # this seems slow? sure something similar was faster...
            for t in self.canvas.find_withtag("event_label"):
                self.canvas.itemconfigure(t, width=float(self.canvas.itemcget(t, 'width'))*n)  # this seems slow? sure something similar was faster...
                w = int(self.canvas.itemcget(t, 'width'))
                tx = self.truncate_text(self.original_texts[t], w)
                self.canvas.itemconfigure(t, text=tx)  # this seems slow? sure something similar was faster...
            self.canvas.configure(scrollregion=self.canvas.bbox("grid"))
        # scroll the canvas so that the mouse still points to the same place
        if e:
            _xv = self.canvas.xview()
            new_width = _xv[1] - _xv[0]
            self.canvas.xview_moveto(x_pos - new_width * width_fraction)

    def truncate_text(self, text, w):
        return text[:w / self.char_w]

    def update(self, *args):
        """
        Data settings changed, get new data and re-render
        """
        s = self.render_start.get() - 1
        e = self.render_start.get() + self.render_len.get() + 1
        self.data = list(self.c.execute("SELECT * FROM cbtv_events WHERE end > ? AND start < ? ORDER BY start ASC, end DESC", (s, e)))
        self.render()

    def render(self, *args):
        """
        Render settings changed, re-render with existing data
        """
        if self.scale.get() < 50:
            return
        self.render_clear()
        self.render_base()
        self.render_data()

    def render_clear(self):
        """
        clear the canvas and any cached variables
        """
        self.canvas.delete(ALL)
        self.original_texts = {}
        self.canvas.configure(scrollregion=(
            0, 0,
            self.render_len.get() * self.scale.get(),
            len(self.threads)*ROW_HEIGHT+20
        ))
        if self.char_w == -1:
            t = self.canvas.create_text(0, 0, font="TkFixedFont", text="_", anchor=NW)
            bb = self.canvas.bbox(t)
            # [2]-[0]=10, but trying by hand, 8px looks better on win7
            # 7px looks right on linux, not sure what [2]-[0] is there,
            # hopefully 9px, so "-2" always helps?
            self.char_w = bb[2] - bb[0] - 2
            self.canvas.delete(t)

    def render_base(self):
        """
        Render grid lines and markers
        """
        _rs = self.render_start.get()
        _rl = self.render_len.get()
        _sc = self.scale.get()

        rs_px = int(_rl * _sc)
        rl_px = int(_rl * _sc)

        for n in range(rs_px, rs_px+rl_px, 100):
            label = " +%.3f" % (float(n) / _sc - _rl)
            self.canvas.create_line(n-rs_px, 0, n-rs_px, 20+len(self.threads)*ROW_HEIGHT, fill="#CCC", tags="grid")
            self.canvas.create_text(n-rs_px, 5, text=label, anchor="nw")

        for n in range(0, len(self.threads)):
            self.canvas.create_line(0, 20+ROW_HEIGHT*n, rl_px, 20+ROW_HEIGHT*n, tags="grid")
            self.canvas.create_text(0, 20+ROW_HEIGHT*(n+1)-5, text=" "+self.threads[n], anchor="sw")

    def render_data(self):
        """
        add the event rectangles
        """
        _rs = self.render_start.get()
        _rl = self.render_len.get()
        _sc = self.scale.get()

        threads = self.threads
        #thread_level_starts = [[], ] * len(self.threads)  # this bug is subtle and hilarious
        thread_level_ends = [[] for n in range(len(self.threads))]

        for row in self.data:
            (_start, _end, _node, _process, _thread, _io, _function, _text) = row
            _start = float(_start)
            _end = float(_end)
            thread_idx = threads.index(_thread)

            # when the event ends, render it
            if _io == "ENDOK" or _io == "ENDER":
                while thread_level_ends[thread_idx] and thread_level_ends[thread_idx][-1] <= _start:
                    thread_level_ends[thread_idx].pop()
                thread_level_ends[thread_idx].append(_end)
                start_px  = (_start - _rs) * _sc
                end_px    = (_end - _rs) * _sc
                length_px = end_px - start_px
                stack_len = len(thread_level_ends[thread_idx]) - 1
                self.show(int(start_px), int(length_px), thread_idx, stack_len, _function, _text, _io=="ENDOK")

            elif _io == "BMARK":
                pass  # render bookmark

    def show(self, start, length, thread, level, function, text, ok):
        text = " " + text
        _time_mult = float(self.scale.get()) / 1000.0
        tip = "%dms @%dms: %s\n%s" % (float(length) / _time_mult, float(start) / _time_mult, function, text)

        fill = "#CFC" if ok else "#FCC"
        outl = "#484" if ok else "#844"
        r = self.canvas.create_rectangle(
            start,        20+thread*ROW_HEIGHT+level*BLOCK_HEIGHT,
            start+length, 20+thread*ROW_HEIGHT+level*BLOCK_HEIGHT+BLOCK_HEIGHT,
            fill=fill, outline=outl,
        )
        t = self.canvas.create_text(
            start, 20+thread*ROW_HEIGHT+level*BLOCK_HEIGHT+3,
            text=self.truncate_text(text, length), tags="event_label", anchor="nw", width=length,
            font="TkFixedFont",
            state="disabled",
        )
        self.canvas.tag_raise(r)
        self.canvas.tag_raise(t)

        self.original_texts[t] = text

        r2 = self.canvas.create_rectangle(
            start,                  20+thread*ROW_HEIGHT+level*BLOCK_HEIGHT+BLOCK_HEIGHT+2,
            start+max(length, 200), 20+thread*ROW_HEIGHT+level*BLOCK_HEIGHT+BLOCK_HEIGHT*6+2,
            state="hidden", fill="#FFA", outline="#AA8"
        )
        t2 = self.canvas.create_text(
            start+2, 20+thread*ROW_HEIGHT+level*BLOCK_HEIGHT+BLOCK_HEIGHT+2,
            text=tip, width=max(length, 200), tags="event_tip", anchor="nw",
            justify="left", state="hidden",
        )

        def ttip_show():
            self.canvas.itemconfigure(r2, state="disabled")
            self.canvas.itemconfigure(t2, state="disabled")
            self.canvas.tag_raise(r2)
            self.canvas.tag_raise(t2)

        def ttip_hide():
            self.canvas.itemconfigure(r2, state="hidden")
            self.canvas.itemconfigure(t2, state="hidden")

        def focus():
            # scale the canvas so that the (selected item width + padding == screen width)
            canvas_w = self.canvas.bbox("grid")[2]
            view_w = self.canvas.winfo_width()
            rect_x = self.canvas.bbox(r)[0]
            rect_w = max(self.canvas.bbox(r)[2] - self.canvas.bbox(r)[0] + 20, 10)
            self.scale_view(n=float(view_w)/rect_w)

            # move the view so that the selected (item x1 = left edge of screen + padding)
            canvas_w = self.canvas.bbox("grid")[2]
            rect_x = self.canvas.bbox(r)[0] - 5
            self.canvas.xview_moveto(float(rect_x)/canvas_w)

        self.canvas.tag_bind(r, "<Enter>", lambda e: ttip_show())
        self.canvas.tag_bind(r, "<Leave>", lambda e: ttip_hide())
        self.canvas.tag_bind(r, "<1>",     lambda e: focus())


def _center(root):
    w = 800
    h = 600
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))


def display(database_file, geometry=None):
    if not have_tk:
        print("Couldn't find Tk libraries")
        return 1

    # set up the root window early, so we can control it (and hide it)
    # by default, showerror() will create a random blank window as root
    root = Tk()
    if os.name == "nt":
        root.wm_iconbitmap(default="images/boomtools.ico")
    root.title(NAME)

    if not os.path.exists(database_file):
        root.withdraw()
        root.overrideredirect(True)
        showerror("Error", "Context dump file '%s' does not exist" % database_file)
        return 2

    try:
        sqlite3.connect(database_file).execute("SELECT * FROM cbtv_events LIMIT 1")
    except sqlite3.OperationalError as e:
        root.withdraw()
        root.overrideredirect(True)
        showerror("Error", "'%s' is not a valid context dump" % database_file, parent=None)
        return 3

    #root.state("zoomed")
    #_center(root)
    _App(root, database_file)
    if geometry:
        root.geometry(geometry)
    root.mainloop()
    return 0


def main(argv):
    parser = OptionParser()
    parser.add_option("-g", "--geometry", dest="geometry",
            help="location and size of window", metavar="GM")
    parser.add_option("-r", "--row-height", dest="row_height", default=140,
            type=int, help="height of the rows", metavar="PX")
    (options, args) = parser.parse_args(argv)

    # lol constants
    ROW_HEIGHT=options.row_height

    if len(args) > 1:
        filename = args[1]
    else:
        root = Tk()
        if os.name == "nt":
            root.wm_iconbitmap(default="images/boomtools.ico")
        root.withdraw()
        root.overrideredirect(True)
        filename = askopenfilename(
            filetypes = [("All Supported Types", "*.ctxt *.cbin"), ("Context Text", "*.ctxt"), ("Context Binary", "*.cbin")],
        )
        root.destroy()
        if not filename:
            return 1

    path, ext = os.path.splitext(filename)
    if ext == ".ctxt":
        compile_log(path+".ctxt", path+".cbin")
        ext = ".cbin"

    if ext == ".cbin":
        display(path+ext, options.geometry)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
