from distutils.core import setup
from distutils.extension import Extension
try:
    from Cython.Distutils import build_ext
except ImportError:
    build_ext = None

setup(
    name = 'Context',
    version = "0.9.0",
    author = "Shish",
    author_email = "shish@civicboom.com",
    url = "http://www.boomtools.co.uk/context",
    cmdclass = {'build_ext': build_ext},

    scripts = ["launcher", ],
    ext_modules = [Extension("contextview", ["contextview.py"]), ],
    data_files = [
        ('images', ['images/boomtools.ico', 'images/end.gif', 'images/next.gif', 'images/prev.gif', 'images/start.gif']),
        ('api', ["context.py", ]),
    ],
)
