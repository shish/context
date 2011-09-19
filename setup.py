from distutils.core import setup
from distutils.extension import Extension

try:
    from Cython.Distutils import build_ext
except ImportError:
    build_ext = None

try:
    import py2exe
except ImportError:
    pass


setup(
    # metadata
    name = 'Context',
    version = "0.9.0",
    author = "Shish",
    author_email = "shish@civicboom.com",
    url = "http://www.boomtools.co.uk/context",

    # cython
    cmdclass = {'build_ext': build_ext},
    #ext_modules = [Extension("contextview", ["contextview.py"]), ],
    py_modules = ["contextview", ],

    # py2exe
    windows = [
        {
            "script": "context",
            "icon_resources": [(1, "images/boomtools.ico")],
        }
    ],
    zipfile = None,
    options = {
        "py2exe": {
            "optimize": 2,
            "bundle_files": 3, # 1 (bundle all) would be nicer, but no win64 support :(
            "compressed": True,
            "excludes": ["doctest", "pdb", "unittest", "difflib", "inspect"],
        }
    },

    # common
    scripts = ["context", ],
    data_files = [
        ('images', ['images/boomtools.ico', 'images/end.gif', 'images/next.gif', 'images/prev.gif', 'images/start.gif']),
        ('api', ["context.py", ]),
    ],
)
