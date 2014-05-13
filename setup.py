from setuptools import setup, find_packages

setup(
    name='context.viewer',
    version='0.0',
    description='Context Viewer',
    classifiers=[
        "Programming Language :: Python",
    ],
    author='Shish',
    author_email='shish+context@shishnet.org',
    url='http://code.shishnet.org/context',
    keywords='profile',
    packages=["context"],
    namespace_packages=["context"],
    test_suite = "context.viewer.tests",
    zip_safe=True,
    install_requires=[
        "decorator",
    ],
    entry_points="""\
    [console_scripts]
    context-viewer = context.viewer.main:main
    context-compiler = context.compiler.main:main
    """,
)

