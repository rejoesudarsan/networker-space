"""Basement Court 1 and its big tree (photo p20 looks down at it; site
world.js / details.js). The tree stands at x 0.85, z -1.55 (basement frame)
in a kota-edged bed of earth and rises through the double-height void, its
crown just above the ground floor and below the first-floor slab (2.75 units
above the basement floor). The court floor is flagstone (site PLAN.court,
x 0.2..2.0, z -2.08..-1.0). Basement frame, Three.js units."""
import random

import bmesh
import bpy
from mathutils import Matrix

from . import _trees

TREE = (0.85, -1.55)
COURT = (0.2, -2.08, 2.0, -1.0)


def build(ctx):
    h = ctx["helpers"]
    coll, empty = ctx["colls"]["basement"], ctx["empties"]["basement"]
    flag = _trees.material(ctx, "Flagstone", "#BFAE92", 0.85)
    joint = _trees.material(ctx, "Flagstone Joint", "#A39478", 0.9)
    kota = _trees.material(ctx, "Kota", "#B9A68A", 0.6)
    soil = _trees.material(ctx, "Soil", "#4A3426", 0.95)
    x0, z0, x1, z1 = COURT
    tx, tz = TREE
    h["add_box"]("basement.Court1.floor", x0, x1, -z1, -z0, 0.0, 0.008, coll, empty, flag)
    rnd = random.Random(1)
    z = z0
    while z < z1 - 0.05:
        zn = min(z + 0.32, z1)
        h["add_box"]("basement.Court1.joint", x0, x1, -zn - 0.004, -zn + 0.004, 0.008, 0.01, coll, empty, joint)
        x = x0 + rnd.uniform(0.1, 0.35)
        while x < x1 - 0.08:
            h["add_box"]("basement.Court1.joint", x - 0.004, x + 0.004, -zn, -z, 0.008, 0.01, coll, empty, joint)
            x += rnd.uniform(0.3, 0.5)
        z = zn
    # Bed: earth with a low kota kerb
    h["add_box"]("basement.Court1.bed", tx - 0.24, tx + 0.24, -(tz + 0.24), -(tz - 0.24), 0.008, 0.016, coll, empty, soil)
    for (a, b, c0, c1) in ((-0.28, 0.28, -0.28, -0.24), (-0.28, 0.28, 0.24, 0.28),
                           (-0.28, -0.24, -0.24, 0.24), (0.24, 0.28, -0.24, 0.24)):
        h["add_box"]("basement.Court1.kerb", tx + a, tx + b, -(tz + c1), -(tz + c0), 0.0, 0.05, coll, empty, kota)
    _trees.tree(ctx, "basement.Court1Tree", (tx, -tz, 0.0), coll, empty,
                height=2.4, spread=0.72, flowers=0, flatten=0.7, seed=31,
                tone="#3F5E33", tone_light="#5D7F45", crown_scale=1.0)
    return []
