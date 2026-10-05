"""Club fit-out: reading seats in the first-floor Double HT court and the
library off the hall.

Court (x 0.81..2.51, z 0.18..1.69; flagstones, olive, nest pendants and
louvred doors come from the court2_* modules): the crowd's path runs from
the north doorway (x 1.0..1.25) straight south into Living 2, so the reading
corner keeps to the east band: two low olive-velvet armchairs with their
backs to the louvred dado (x 2.49), a teak side table between them and a
second one by the south chair, facing the olive and the court.

Library: the plan's LIBRARY label sits in the alcove between Kitchen 2 and
Family 2 (x 0.073..0.729, z -1.827..-1.30, open south to the Dining 2 hall,
the corridor from the foyer ending at it). Teak bookshelves wrap the alcove's
three walls; the reading room spills into the west end of the hall in front
of Kitchen 2's south wall (z -1.302), which gets two more bookshelves: a
long teak reading table with two brass banker's lamps and four chairs, two
velvet armchairs by its east end with a side table, on a linen rug. Kept
clear: Kitchen 2's doorway (x < -1.12), the westward passage (z > -0.45)
and the foyer corridor (x 0.07..0.73). First frame, Three.js units."""
import math

from . import _furniture as F

E, W, N, S = math.pi / 2, -math.pi / 2, math.pi, 0.0      # facing
M = F.M


def bankers_lamp(kit, x, z, rot, y0):
    """Brass banker's lamp standing on a surface y0 metres above the floor."""
    kit.at(x, z, rot)
    kit.cyl("Brass", 0, 0, y0, y0 + 0.02, 0.07, 0.07, 14)
    kit.cyl("Brass", 0, 0, y0 + 0.02, y0 + 0.3, 0.008, 0.008, 6)
    kit.box("Olive Velvet", 0, 0, y0 + 0.33, 0.3, 0.12, 0.06)
    kit.box("Lamp Glow", 0, 0, y0 + 0.297, 0.26, 0.09, 0.008)


def books(kit, x, z, rot, y0, n=3, seed=0):
    """A small stack of books lying on a surface y0 metres up."""
    kit.at(x, z, rot)
    mats = ("Book Spines", "Linen", "Cushion", "Olive Velvet")
    y = y0
    for i in range(n):
        t = 0.03 + 0.01 * ((seed + i) % 2)
        kit.box(mats[(seed + i) % 4], 0.01 * (i % 2), 0, y + t / 2, 0.22 - 0.02 * i, 0.16, t, rz=0.15 * ((seed + i) % 3 - 1))
        y += t


def build(ctx):
    k = F.Kit(ctx, "first", "first.CourtLibrary")
    wall = lambda x, z, side, h=1.2: F.wall(ctx, "first", x, z, side, h=h)

    # ---- Court: reading corner on the east band, on the flagstones
    dado = wall(1.9, 1.0, "east", h=0.5)            # 2.49, louvred dado face
    k.base = 0.012                                  # flagstone top
    ax = dado - 0.47 * M
    F.armchair(k, ax, 0.98, W - 0.12)
    F.armchair(k, ax, 1.48, W + 0.12)
    F.side_table(k, dado - 0.25 * M, 1.23, h=0.5, r=0.2)
    books(k, dado - 0.25 * M, 1.23, 0.4, 0.5, n=2, seed=1)
    F.side_table(k, dado - 0.2 * M, 0.74, h=0.45, r=0.17)
    k.base = 0.0085

    # ---- Library alcove: shelves on three walls
    a_n = wall(0.4, -1.5, "north")                  # -1.827
    a_w = wall(0.4, -1.5, "west")                   # 0.073
    a_e = wall(0.4, -1.5, "east")                   # 0.729
    sd = 0.16 * M                                   # half the shelf depth
    F.bookshelf(k, (a_w + a_e) / 2, a_n + sd, S, w=(a_e - a_w) / M - 0.04, h=2.2, seed=31)
    side_z0, side_z1 = a_n + 2 * sd + 0.01, -1.31
    side_w = (side_z1 - side_z0) / M
    F.bookshelf(k, a_w + sd, (side_z0 + side_z1) / 2, E, w=side_w, h=2.2, seed=32)
    F.bookshelf(k, a_e - sd, (side_z0 + side_z1) / 2, W, w=side_w, h=2.2, seed=33)

    # ---- Reading room at the west end of the hall
    k_s = wall(-0.5, -0.9, "north")                 # -1.302, Kitchen 2 south wall
    F.bookshelf(k, -0.835, k_s + sd, S, w=1.3, h=2.1, seed=34)
    F.bookshelf(k, -0.30, k_s + sd, S, w=1.3, h=2.1, seed=35)
    F.rug(k, -1.06, -1.13, 0.04, -0.47, mat="Linen")
    tx, tz = -0.70, -0.80
    F.long_table(k, tx, tz, S, length=1.3, width=0.8)
    for sx in (-0.17, 0.17):
        F.chair(k, tx + sx, tz - 0.245, S)
        F.chair(k, tx + sx, tz + 0.245, N)
        bankers_lamp(k, tx + sx * 1.3, tz - 0.06, S, 0.75)
    books(k, tx + 0.02, tz + 0.04, 0.3, 0.75, n=3, seed=2)
    F.armchair(k, -0.16, -1.0, W + 0.25)
    F.armchair(k, -0.16, -0.6, W - 0.25)
    F.side_table(k, -0.09, -0.8, h=0.5, r=0.17)
    F.plant(k, -1.045, -1.12, h=1.0, pot_r=0.16, seed=36)

    objs = k.done()
    ctx["helpers"]["info"]("court_library: %d objects; court dado %.3f, alcove n %.3f w %.3f e %.3f, kitchen s %.3f"
                           % (len(objs), dado, a_n, a_w, a_e, k_s))
    return []
