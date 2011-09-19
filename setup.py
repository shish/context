from distutils.core import setup
from distutils.extension import Extension
try:
    from Cython.Distutils import build_ext
except ImportError:
    build_ext = None

ext_modules = [Extension("contextview", ["contextview.py"])]

setup(
  name = 'Context Viewer',
  cmdclass = {'build_ext': build_ext},
  ext_modules = ext_modules
)
