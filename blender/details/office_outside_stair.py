"""The office's own entrance (basement plan, photo p03): the open-to-sky court
in front of the office, floored in flagstones, and its outside stair of ten
kota-stone risers up to street level along the basement's front wall, with a
steel handrail on the court side. Positions from site/src/world/details.js
(PLAN.openCourt, PLAN.officeStair). Basement frame, Three.js units."""
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _trees

STAIR_X = (1.28, 2.14)       # bottom .. top of the flight
RISERS = 10
STAIR_W = 0.42               # across the flight (z)
OPEN_COURT = (0.94, 1.92, 2.2)   # x0, z0, x1; z1 is the stair's court side
RAIL_H = 0.34


def _rod(bm, a, b, r):
    d = b - a
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r, radius2=r, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=g["verts"])


def build(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    b = c["FLOORS"]["basement"]
    hw, hd = b["width"] / 2, b["depth"] / 2
    rise_total = -b["level"]                 # basement floor to street level
    coll, empty = ctx["colls"]["basement"], ctx["empties"]["basement"]
    kota = _trees.material(ctx, "Kota", "#B9A68A", 0.6)
    flag = _trees.material(ctx, "Flagstone", "#BFAE92", 0.85)
    joint = _trees.material(ctx, "Flagstone Joint", "#A39478", 0.9)
    steel = _trees.material(ctx, "Steel", "#4A4D4F", 0.45)

    z1 = hd - 0.02
    z0 = z1 - STAIR_W
    x0, x1 = STAIR_X
    step = (x1 - x0) / RISERS
    for i in range(RISERS):
        top = (i + 1) * rise_total / RISERS
        h["add_box"]("basement.OfficeStair.%02d" % i, x0 + i * step, x0 + (i + 1) * step,
                     -z1, -z0, 0.0, top, coll, empty, kota)
    # Landing at the top, to the basement's east edge
    h["add_box"]("basement.OfficeStair.landing", x1, hw, -z1, -z0, 0.0, rise_total, coll, empty, kota)

    # Handrail on the court side: a sloped rod on three posts
    hz = -(z0 - 0.015)
    bm = bmesh.new()
    _rod(bm, Vector((x0, hz, RAIL_H)), Vector((x1, hz, rise_total + RAIL_H)), 0.01)
    _rod(bm, Vector((x1, hz, rise_total + RAIL_H)), Vector((hw - 0.03, hz, rise_total + RAIL_H)), 0.01)
    for (x, y) in ((x0, 0.0), ((x0 + x1) / 2, rise_total / 2), (x1, rise_total), (hw - 0.03, rise_total)):
        _rod(bm, Vector((x, hz, y)), Vector((x, hz, y + RAIL_H)), 0.01)
    me = bpy.data.meshes.new("basement.OfficeStairRail")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(steel)
    ob = bpy.data.objects.new(me.name, me)
    coll.objects.link(ob)
    ob.parent = empty
    ob.matrix_parent_inverse = Matrix.Identity(4)

    # The open court floor: flagstones in rows with joints
    cx0, cz0, cx1 = OPEN_COURT
    cz1 = z0 - 0.01
    t = 0.01
    h["add_box"]("basement.OpenCourt.floor", cx0, cx1, -cz1, -cz0, 0.0, t, coll, empty, flag)
    rnd = random.Random(3)
    zrow = cz0
    while zrow < cz1 - 0.05:
        zn = min(zrow + 0.3, cz1)
        h["add_box"]("basement.OpenCourt.joint", cx0, cx1, -zn - 0.006, -zn + 0.006, t, t + 0.003,
                     coll, empty, joint)
        x = cx0 + rnd.uniform(0.1, 0.35)
        while x < cx1 - 0.08:
            h["add_box"]("basement.OpenCourt.joint", x - 0.006, x + 0.006, -zn, -zrow, t, t + 0.003,
                         coll, empty, joint)
            x += rnd.uniform(0.3, 0.5)
        zrow = zn
    return []
