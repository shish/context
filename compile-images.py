#!/usr/bin/python

import base64

images = ["context-name", "end", "next", "prev", "start"]

for img in images:
    data = file("images/"+img+".gif").read()

    print img.replace("-", "_"), "=", "'%s'" % base64.b64encode(data)
