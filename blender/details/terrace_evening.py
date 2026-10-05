"""Club fit-out: the second-floor terrace for evenings (18:00-23:00).

The terrace runs x -2.22..-0.95, z -3.48..3.43 (second frame, measured top-
down 5 Oct 2026), terracotta floor, the weathered bench at the north end
(terrace_terracotta.py, z -3.3..-2.25 on the house wall). Along it, from
north to south: a lounge group of three linen armchairs round a low teak
table, two bistro tables for two, and a cushioned banquette on the house
wall with two more tables. Planters stand against the parapet, and a festoon
of warm bulbs hangs on black steel posts down the middle -- the light the
night bake picks up. Second frame, Three.js units."""
import math

from . import _furniture as F

E, W, N, S = math.pi / 2, -math.pi / 2, math.pi, 0.0
M = F.M


def build(ctx):
    k = F.Kit(ctx, "second", "second.TerraceEvening")
    east = F.wall(ctx, "second", -1.6, 2.4, "east")
    west = F.wall(ctx, "second", -1.6, 0.6, "west", h=0.3)
    mid = (east + west) / 2

    # Lounge: three armchairs round a low table.
    F.side_table(k, mid, -1.55, h=0.4, r=0.36)
    F.armchair(k, mid - 0.32, -1.55, E, fabric="Linen")
    F.armchair(k, mid + 0.3, -1.4, W, fabric="Linen")
    F.armchair(k, mid, -1.95, S, fabric="Linen")
    F.rug(k, mid - 0.5, -2.05, mid + 0.5, -1.05, mat="Linen")

    # Bistro tables for two.
    for z in (-0.25, 0.75):
        F.bistro(k, mid, z, r=0.3, seed=int(z * 10) + 40)
        F.chair(k, mid, z - 0.19, S)
        F.chair(k, mid, z + 0.19, N)

    # Banquette on the house wall with two tables.
    F.banquette(k, east - 0.226, 1.7, east, 3.2, back="east")
    for z in (2.05, 2.85):
        F.bistro(k, east - 0.42, z, r=0.27, seed=int(z * 10) + 50)
        F.chair(k, east - 0.66, z, E)

    # Planters against the parapet.
    for i, z in enumerate((-2.9, -0.75, 0.25, 1.4, 3.2)):
        F.plant(k, west + 0.1, z, h=1.0 + 0.3 * (i % 2), pot_r=0.22, seed=60 + i)

    # Festoon: posts down the parapet side, a sagging line of bulbs.
    top = 2.35
    posts = [-3.2, -1.0, 1.2, 3.3]
    for z in posts:
        k.at(west + 0.06, z)
        k.cyl("Black Steel", 0, 0, 0, top + 0.1, 0.025, 0.025, 8)
    for a, b in zip(posts, posts[1:]):
        n = 9
        pts = []
        for i in range(n + 1):
            u = i / n
            z = a + (b - a) * u
            x = west + 0.06 + (mid - (west + 0.06)) * math.sin(math.pi * u) * 0.9
            y = top - 0.35 * math.sin(math.pi * u)
            pts.append((x, z, y))
        k.at(0, 0)
        for (x0, z0, y0), (x1, z1, y1) in zip(pts, pts[1:]):
            k.cyl("Black Steel", 0, 0, 0, 0, 0.003, 0.003, 4,
                  a=(x0 / M, -z0 / M, y0), b=(x1 / M, -z1 / M, y1))
        for (x, z, y) in pts[1:-1]:
            k.ball("Lamp Glow", x / M, -z / M, y - 0.05, 0.035, 1.2, 1)

    objs = k.done()
    ctx["helpers"]["info"]("terrace_evening: %d objects; terrace x %.3f..%.3f" % (len(objs), west, east))
    return []
