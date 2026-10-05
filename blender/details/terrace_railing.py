"""Terrace railing: steel rail on top of the second-floor terrace parapet
(board, photo p03 top left). Open sides: the west edge (x = -width/2) and the
north and south edges from the west edge to TERRACE_X1. Posts plus three
horizontal bars, 0.35 units above the parapet. Floor-local, parented to
Floor.second."""

RAIL_H = 0.35        # above the parapet top, units
BARS = 3
BAR = 0.012          # bar section, units (~3 cm)
POST = 0.016
POST_STEP = 0.45


def _run(h, name, a0, a1, fixed, along_x, z0, coll, empty, mat):
    """Posts and bars along one parapet edge."""
    length = a1 - a0
    n = max(1, round(length / POST_STEP))
    for i in range(n + 1):
        a = a0 + length * i / n
        if along_x:
            h["add_box"]("%s.post%d" % (name, i), a - POST / 2, a + POST / 2,
                         fixed - POST / 2, fixed + POST / 2, z0, z0 + RAIL_H, coll, empty, mat)
        else:
            h["add_box"]("%s.post%d" % (name, i), fixed - POST / 2, fixed + POST / 2,
                         a - POST / 2, a + POST / 2, z0, z0 + RAIL_H, coll, empty, mat)
    for b in range(BARS):
        z = z0 + RAIL_H * (b + 1) / BARS - BAR
        if along_x:
            h["add_box"]("%s.bar%d" % (name, b), a0, a1, fixed - BAR / 2, fixed + BAR / 2,
                         z, z + BAR, coll, empty, mat)
        else:
            h["add_box"]("%s.bar%d" % (name, b), fixed - BAR / 2, fixed + BAR / 2, a0, a1,
                         z, z + BAR, coll, empty, mat)


def build(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    sec = c["FLOORS"]["second"]
    shw, shd = sec["width"] / 2, sec["depth"] / 2
    t, z0 = c["PARAPET_T"], c["PARAPET_H"]
    tx0, tx1 = -shw, c["TERRACE_X1"]
    coll, empty = ctx["colls"]["second"], ctx["empties"]["second"]
    mat = ctx["mats"]["Charcoal Steel"]
    mid = t / 2
    _run(h, "second.TerraceRail.W", -shd + mid, shd - mid, tx0 + mid, False, z0, coll, empty, mat)
    _run(h, "second.TerraceRail.S", tx0 + mid, tx1, -shd + mid, True, z0, coll, empty, mat)
    _run(h, "second.TerraceRail.N", tx0 + mid, tx1, shd - mid, True, z0, coll, empty, mat)
    return []
