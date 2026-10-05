"""The street front by the gate (photo p05): the house number '1172' in dark
raised numerals and the letter slot on the plaster face right of the gate,
and two big terracotta pots of asparagus fern on the street against it.

The gate, piers and the low front wall already come from build_house.py
(ground.streetGate, ground.frontWall, ground.copings); this only checks
they exist. Ground frame, Three.js units; street level is -LEVEL locally."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _trees

FACE_Z = 5.0                  # plinth / wall face toward the street (ground frame z)
PLATE_X = -2.08               # centre of the number, right of the gate steps
PLATE_Y = 0.52                # above street level, units (~1.27 m)
POTS = [(-2.2, 5.16, 0.095), (-1.96, 5.2, 0.085)]   # x, z, radius (units)
POT_H = 0.15
FRONDS = 36


def _link(ob, coll, parent):
    coll.objects.link(ob)
    ob.parent = parent
    ob.matrix_parent_inverse = Matrix.Identity(4)
    return ob


def _mesh_obj(name, bm, coll, parent, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    return _link(bpy.data.objects.new(name, me), coll, parent)


def _pot(bm, cx, cy, z0, r):
    geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=r * 0.72,
                                 radius2=r, depth=POT_H)
    bmesh.ops.translate(bm, verts=geom["verts"], vec=(cx, cy, z0 + POT_H / 2))
    # rim
    geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=r * 1.06,
                                 radius2=r * 1.06, depth=0.018)
    bmesh.ops.translate(bm, verts=geom["verts"], vec=(cx, cy, z0 + POT_H - 0.009))


def _fern(bm, cx, cy, z_top, r, rnd):
    """Arching fronds: each a short tapered rise then a long droop over the rim."""
    def seg(a, b, r0, r1):
        d = b - a
        geom = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=r0,
                                     radius2=r1, depth=d.length)
        rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=geom["verts"])
    base = Vector((cx, cy, z_top))
    # a mound in the middle
    geom = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(base + Vector((0, 0, 0.03)))
                        @ Matrix.Diagonal((r * 0.9, r * 0.9, r * 0.55, 1)), verts=geom["verts"])
    for i in range(FRONDS):
        a = i / FRONDS * 2 * math.pi + rnd.uniform(-0.15, 0.15)
        out = Vector((math.cos(a), math.sin(a), 0))
        length = rnd.uniform(1.6, 2.6) * r
        rise = rnd.uniform(0.06, 0.16)
        # Points along an arching curve: up and out, then drooping over the rim
        n = 14
        pts = []
        for k in range(n + 1):
            t = k / n
            pts.append(base + out * (r * 0.15 + length * t)
                       + Vector((0, 0, rise * math.sin(math.pi * t * 0.8) - 0.12 * t * t)))
        # Overlapping elongated tufts along the frond, tapering to the tip: a soft plume
        for k in range(1, n + 1):
            d = (pts[k] - pts[k - 1])
            tuft = 0.026 * (1.2 - 0.75 * k / n)
            rot = Vector((1, 0, 0)).rotation_difference(d.normalized()).to_matrix().to_4x4()
            g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
            m = (Matrix.Translation((pts[k] + pts[k - 1]) / 2) @ rot
                 @ Matrix.Diagonal((max(d.length * 0.9, tuft * 1.4), tuft, tuft * 0.8, 1)))
            bmesh.ops.transform(bm, matrix=m, verts=g["verts"])


def build(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    for name in ("ground.streetGate", "ground.frontWall", "ground.copings"):
        if bpy.data.objects.get(name) is None:
            h["warn"]("front wall check: %s is missing" % name)
    g = c["FLOORS"]["ground"]
    street = -g["level"]
    coll, empty = ctx["colls"]["ground"], ctx["empties"]["ground"]
    face_y = -FACE_Z
    dark = ctx["mats"]["Charcoal Steel"]

    # House number: raised numerals on the face
    cu = bpy.data.curves.new("ground.HouseNumber", "FONT")
    cu.body = "1172"
    cu.size = 0.075
    cu.extrude = 0.004
    cu.align_x = "CENTER"
    num = _link(bpy.data.objects.new("ground.HouseNumber", cu), coll, empty)
    num.location = (PLATE_X, face_y - 0.003, street + PLATE_Y)   # raised just proud of the face
    num.rotation_euler = (math.pi / 2, 0, 0)
    cu.materials.append(dark)
    # Letter slot below it: a dark recess with a steel lip
    h["add_box"]("ground.LetterSlot", PLATE_X - 0.08, PLATE_X + 0.08, face_y - 0.006, face_y + 0.004,
                 street + PLATE_Y - 0.17, street + PLATE_Y - 0.14, coll, empty, dark)

    # Fern pots on the street
    terracotta = ctx["mats"].get("Terracotta") or _trees.material(ctx, "Terracotta", "#B66E51")
    fern = _trees.material(ctx, "Fern", "#5E8C3A", 0.7)
    rnd = random.Random(5)
    pots, fronds = bmesh.new(), bmesh.new()
    for (x, z, r) in POTS:
        _pot(pots, x, -z, street, r)
        _fern(fronds, x, -z, street + POT_H, r, rnd)
    _mesh_obj("ground.FernPots", pots, coll, empty, terracotta)
    _mesh_obj("ground.Ferns", fronds, coll, empty, fern)
    return []
