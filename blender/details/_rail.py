"""Shared post-and-bar railing builder. Coordinates are Blender-space in the
parent's units (x, y), z measured from the parent's origin."""


def run(h, name, p0, p1, z0, coll, parent, mat, height=0.36, bars=3, post_step=0.45,
        post=0.016, bar=0.012):
    """Straight railing from p0=(x, y) to p1=(x, y), axis-aligned."""
    (x0, y0), (x1, y1) = p0, p1
    along_x = abs(x1 - x0) >= abs(y1 - y0)
    a0, a1 = (min(x0, x1), max(x0, x1)) if along_x else (min(y0, y1), max(y0, y1))
    fixed = y0 if along_x else x0
    length = a1 - a0
    n = max(1, round(length / post_step))
    for i in range(n + 1):
        a = a0 + length * i / n
        if along_x:
            h["add_box"]("%s.post%d" % (name, i), a - post / 2, a + post / 2,
                         fixed - post / 2, fixed + post / 2, z0, z0 + height, coll, parent, mat)
        else:
            h["add_box"]("%s.post%d" % (name, i), fixed - post / 2, fixed + post / 2,
                         a - post / 2, a + post / 2, z0, z0 + height, coll, parent, mat)
    for b in range(bars):
        z = z0 + height * (b + 1) / bars - bar
        if along_x:
            h["add_box"]("%s.bar%d" % (name, b), a0, a1, fixed - bar / 2, fixed + bar / 2,
                         z, z + bar, coll, parent, mat)
        else:
            h["add_box"]("%s.bar%d" % (name, b), fixed - bar / 2, fixed + bar / 2, a0, a1,
                         z, z + bar, coll, parent, mat)
