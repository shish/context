

def conditional(v, f):
    if v.get() == 1:
        f()


_colours = [(n, 255 - n, 0) for n in range(0, 255 + 1)]

def gen_colour(p0, pN):
    idx = int(float(p0) / float(pN) * 255)
    return "#%02X%02X%02X" % _colours[min(idx, len(_colours))]


def shrink(box, n):
    return (box[0] + n, box[1] + n, box[2] - n, box[3] - n)
