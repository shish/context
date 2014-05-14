#!/usr/bin/python

import base64

data = {
        "context_name": "images/context-name.gif",
        "end": "images/end.gif",
        "next": "images/next.gif",
        "prev": "images/prev.gif",
        "start": "images/start.gif",
        "README": "docs/README.txt",
        "LICENSE": "docs/LICENSE.txt",
}

for name, filename in data.items():
    print name, "=", "'%s'" % base64.b64encode(file(filename).read())
