"""Neighbours: plain massing with compound walls, so the house stays the
subject (site/src/world/world.js 'neighbours'). Footprints and positions are
the site's; heights are scaled up to the two-to-four storeys of the photos
(p19, p03), where the site keeps them at one storey. Each block gets a dark
window band per storey on its street face and a thin parapet.
Site.Units frame (model units, street level).

The site's far row across the street (z = 15) is left out: the street camera
stands 56 m out, inside where that row would be, and even with camera and shadow
visibility off the blocks darkened the street in front of it."""
import random

import bpy

from . import _trees

# x, w, d, h(site), z  (Three.js; z toward the street = +)
NEIGHBOURS = [
    (-10.5, 6, 9, 1.3, -0.4), (10.8, 6.4, 9.4, 1.7, -0.2), (-18, 6.4, 9, 1.1, 0), (18.4, 6.2, 9.2, 1.5, -0.3),
    # far row from world.js, omitted (see docstring):
    # (-9, 6.5, 6, 1.2, 15), (-1.6, 6.8, 6, 1.6, 15), (5.6, 6.2, 6, 1.1, 15), (12.6, 6.6, 6, 1.4, 15),
]
HEIGHT_SCALE = 2.6          # site heights x this = 2.9 .. 4.4 units (7 .. 11 m)
STOREY = 1.45
WALL_H, WALL_T = 0.32, 0.08


def build(ctx):
    h = ctx["helpers"]
    units = bpy.data.objects.get("Site.Units")
    if units is None:
        h["warn"]("neighbour_massing: no Site.Units frame")
        return []
    coll = h["get_collection"]("Neighbours", ctx["site"])
    tones = [_trees.material(ctx, "Neighbour Plaster A", "#E6E3DC", 0.9),
             _trees.material(ctx, "Neighbour Plaster B", "#E1DDD5", 0.9)]
    wall_m = _trees.material(ctx, "Neighbour Wall", "#D4CFC5", 0.9)
    glass = _trees.material(ctx, "Neighbour Glass", "#3F4448", 0.3)
    rnd = random.Random(7)
    for i, (x, w, d, hs, z) in enumerate(NEIGHBOURS):
        H = hs * HEIGHT_SCALE
        m = tones[rnd.randrange(2)]
        x0, x1 = x - w / 2, x + w / 2
        y0, y1 = -(z + d / 2), -(z - d / 2)          # Blender y; street side is the -y face for z<10
        h["add_box"]("Site.Neighbour.%d" % i, x0, x1, y0, y1, 0.0, H, coll, units, m)
        h["add_box"]("Site.Neighbour.%d.parapet" % i, x0 - 0.03, x1 + 0.03, y0 - 0.03, y1 + 0.03,
                     H, H + 0.12, coll, units, m)
        across = z > 10
        face = y1 if across else y0                  # the face toward the street
        out = 1 if across else -1
        # Window bands per storey, set into a few bays
        storeys = max(1, int(H / STOREY + 0.3))
        for s in range(storeys):
            zb = s * STOREY + 0.45
            if zb + 0.5 > H:
                break
            bays = rnd.sample(range(4), rnd.choice((2, 3)))
            for b in bays:
                bx0 = x0 + 0.35 + b * (w - 0.7) / 4
                bx1 = bx0 + (w - 0.7) / 4 - 0.35
                h["add_box"]("Site.Neighbour.%d.win" % i, bx0, bx1,
                             min(face, face + out * 0.02), max(face, face + out * 0.02),
                             zb, zb + 0.55, coll, units, glass)
        # Compound wall toward the street
        wy = -(z - d / 2 - 0.4) if across else -(z + d / 2 + 0.3)
        h["add_box"]("Site.Neighbour.%d.wall" % i, x0, x1, wy - WALL_T / 2, wy + WALL_T / 2,
                     0.0, WALL_H, coll, units, wall_m)
    return []
