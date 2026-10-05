"""Gulmohar trees on the street (photos p19, p21, p03; board). Positions and
sizes from site/src/world/world.js, in ground-floor units at street level:
two flowering trees flanking the house in front, two further along the street.
Gulmohar crowns are broad and flat-topped, so the crown is flattened more than
the site's generic tree."""
import bpy

from . import _trees

TREES = [  # Three.js x, z, height, spread, flowers
    (-4.6, 6.3, 3.6, 1.5, 70),
    (5.8, 6.3, 3.3, 1.35, 55),
    (-9.5, 9.4, 3.4, 1.4, 40),
    (9.8, 9.4, 3.1, 1.3, 0),
]


def build(ctx):
    units = bpy.data.objects.get("Site.Units")
    if units is None:
        ctx["helpers"]["warn"]("gulmohar_trees: no Site.Units frame")
        return []
    coll = ctx["helpers"]["get_collection"]("Trees", ctx["site"])
    for i, (x, z, h, s, f) in enumerate(TREES):
        _trees.tree(ctx, "Site.Gulmohar.%d" % i, (x, -z, 0.0), coll, units,
                    height=h, spread=s, flowers=f * 3, flatten=0.5, seed=11 + i,
                    crown_scale=1.45, flower_size=0.55)
    return []
