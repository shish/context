#!/usr/bin/python

# todo:
# full-file navigation
# - cbtv_events logs can last for hours, but only a minute at a time is
#   sensibly viewable
# mark lock claim / release
# - seeing what is locking software is good

from __future__ import print_function
import threading
import datetime
import sqlite3
import sys
import time


NAME = "Context"
ROW_HEIGHT = 140
BLOCK_HEIGHT = 20


#######################################################################
# Application API
#######################################################################

def compile_log(log_file, database_file):
    db = sqlite3.connect(database_file)
    c = db.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS cbtv_events(
            timestamp float not null,
            node varchar(32) not null,
            process integer not null,
            thread varchar(32) not null,
            type char(5) not null,
            function text not null,
            text text not null
        )
    """)
    for line in open(log_file):
        c.execute(
            "INSERT INTO cbtv_events VALUES(?, ?, ?, ?, ?, ?, ?)",
            line.strip().split(" ", 6)
        )
    c.execute("CREATE INDEX IF NOT EXISTS ts_idx ON cbtv_events(timestamp)")
    c.execute("CREATE INDEX IF NOT EXISTS ty_idx ON cbtv_events(type)")
    c.close()
    db.commit()


#######################################################################
# GUI Out
#######################################################################

try:
    from Tkinter import *
    from ttk import *
    have_tk = True
except ImportError:
    have_tk = False


class _App:
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
                ).pack(side="right")

        _la("  Start ")
        _sp(0, int(time.time()), 10, self.render_start, 15)
        _la("  Seconds ")
        _sp(1, 60, 1, self.render_len, 3)
        _la("  Pixels per second ")
        _sp(100, 5000, 100, self.scale, 5)

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

        db = sqlite3.connect(database_file)
        self.c = db.cursor()

        self.threads = [n[0] for n in self.c.execute("SELECT DISTINCT thread FROM cbtv_events ORDER BY thread")]
        self.render_start = DoubleVar(master, self.get_start(0))
        self.render_len = IntVar(master, 10)
        self.scale = IntVar(master, 1000)

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
        self.controls.grid(column=0, row=0, sticky=(W, E))
        self.canvas.grid(  column=0, row=1, sticky=(N, W, E, S))
        self.v.grid(       column=1, row=1, sticky=(N, S))
        self.h.grid(       column=0, row=2, sticky=(W, E))
        self.grip.grid(    column=1, row=2, sticky=(S, E))

        self.canvas.bind("<4>", lambda e: self.scale_view(e, 1.0 * 1.1))
        self.canvas.bind("<5>", lambda e: self.scale_view(e, 1.0 / 1.1))

        # in windows, mouse wheel events always go to the root window o_O
        self.master.bind("<MouseWheel>", lambda e: self.scale_view(e,
            ((1.0 * 1.1) if e.delta < 0 else (1.0 / 1.1))
        ))

        drag_move = """
        def _sm(e):
            self.st = self.render_start.get()
            self.sx = e.x
            self.sy = e.y
        def _cm(e):
            self.render_start.set(self.st + float(self.sx - e.x)/self.scale.get())
            self.render()
        self.canvas.bind("<1>", _sm)
        self.canvas.bind("<B1-Motion>", _cm)
        """

        self.update()

    def get_start(self, start_hint=1, io="START"):
        return list(self.c.execute(
            "SELECT min(timestamp) FROM cbtv_events WHERE timestamp > ? AND type = ?",
            [start_hint, io]
        ))[0][0]

    def get_end(self, end_hint=0, io="ENDOK"):
        return list(self.c.execute(
            "SELECT max(timestamp) FROM cbtv_events WHERE timestamp < ? AND type = ?",
            [end_hint, io]
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
        t.wm_attributes("-topmost", 1)
        t.title("Bookmarks")

        li = Listbox(t, height=10, width=40)
        li.grid(column=0, row=0, sticky=(N, E, S, W))

        sb = Scrollbar(t, orient=VERTICAL, command=li.yview)
        sb.grid(column=1, row=0, sticky=(N, S))

        li.config(yscrollcommand=sb.set)

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
        li.bind('<Double-Button-1>', _lbox_selected)

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
        self.data = list(self.c.execute("SELECT * FROM cbtv_events WHERE timestamp BETWEEN ? AND ?", (s, e)))
        self.render()

    def render(self, *args):
        """
        Render settings changed, re-render with existing data
        """
        if self.scale.get() < 100:
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
        thread_level_starts = [[] for n in range(len(self.threads))]

        for row in self.data:
            (_time, _node, _process, _thread, _io, _function, _text) = row
            _time = float(_time)
            thread_idx = threads.index(_thread)

            # when an event starts, take note of the start time
            if _io == "START":
                thread_level_starts[thread_idx].append(_time)

            # when the event ends, render it
            elif _io == "ENDOK" or _io == "ENDER":
                # if we start rendering mid-file, we may see the ends
                # of events that haven't started yet
                if len(thread_level_starts[thread_idx]):
                    event_start = thread_level_starts[thread_idx].pop()
                    event_end = _time
                    if event_start < _rs + _rl:
                        start_px  = (event_start - _rs) * _sc
                        end_px    = (event_end - _rs) * _sc
                        length_px = end_px - start_px
                        stack_len = len(thread_level_starts[thread_idx])
                        self.show(int(start_px), int(length_px), thread_idx, stack_len, _function, _text, _io=="ENDOK")

            elif _io == "!":
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

    root = Tk()
    root.title(NAME)
    #root.state("zoomed")
    #_center(root)
    _App(root, database_file)
    if geometry:
        root.geometry(geometry)
    root.mainloop()
    return 0
