import os

try:
    from Tkinter import *
    from tkMessageBox import *
    from tkFileDialog import askopenfilename, asksaveasfilename
    have_tk = True
except ImportError:
    have_tk = False

try:
    from ttk import *
    have_ttk = True
except ImportError:
    have_ttk = False


class ProgressDialog:
    def __init__(self, master, title):
        if master:
            self.root = Toplevel(master)
            self.root.transient(master)
        else:
            self.root = Tk()
            set_icon(self.root, "images/tools-icon")
        self.root.title(title)
        self.label = Label(self.root, text=title, width=30, anchor=CENTER)
        self.label.pack(padx=5, pady=5)
        self.root.update()

    def update(self, text):
        self.label.configure(text=text)
        self.root.update()

    def destroy(self):
        self.root.destroy()

def set_icon(root, basename):
    if os.name == "nt":
        root.wm_iconbitmap(default=resource("%s.ico" % basename))

def win_center(root):
    root.update()
    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()
    ws = root.winfo_screenwidth()
    hs = root.winfo_screenheight()
    x = (ws/2) - (w/2)
    y = (hs/2) - (h/2)
    root.geometry('%dx%d+%d+%d' % (w, h, x, y))

def resource(path):
    ideas = [
        os.path.join(os.path.dirname(sys.argv[0]), path),
        os.path.join(os.environ.get("_MEIPASS2", "/"), path),
        os.path.join("..", "..", "..", path),
        path,
    ]
    for p in ideas:
        if os.path.exists(p):
            return p
    return None

