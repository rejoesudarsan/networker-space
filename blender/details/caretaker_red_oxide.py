"""The caretaker room (photo p15; plan 7'8" x 9'6", ground frame about
x 1.56..2.58, z -4.9..-4.06, fitted to the walls in a top-down cutaway): polished red-oxide floor with a red-oxide
skirting band round the walls, and the small dark three-blade ceiling fan.
Ground frame, Three.js units; slab top = 0."""
import math

import bmesh
import bpy
from mathutils import Matrix

from . import _trees

ROOM = (1.56, -4.9, 2.58, -4.06)
SKIRT_H = 0.04


def build(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    coll, empty = ctx["colls"]["ground"], ctx["empties"]["ground"]
    red = ctx["mats"].get("Red Oxide") or _trees.material(ctx, "Red Oxide", "#884B45", 0.3)
    fan_m = _trees.material(ctx, "Fan Brown", "#3B2620", 0.5)
    x0, z0, x1, z1 = ROOM
    h["add_box"]("ground.Caretaker.floor", x0, x1, -z1, -z0, 0.0, 0.012, coll, empty, red)
    t = 0.006
    for (a, b, ya, yb) in ((x0, x1, -z1, -z1 + t), (x0, x1, -z0 - t, -z0),
                           (x0, x0 + t, -z1, -z0), (x1 - t, x1, -z1, -z0)):
        h["add_box"]("ground.Caretaker.skirting", a, b, ya, yb, 0.012, SKIRT_H, coll, empty, red)
    # Fan
    wall_h = c["WALL_H"]
    fx, fy = (x0 + x1) / 2, -(z0 + z1) / 2
    bm = bmesh.new()
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.005, radius2=0.005, depth=0.08)
    bmesh.ops.translate(bm, verts=g["verts"], vec=(fx, fy, wall_h - 0.04))
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.025, radius2=0.02, depth=0.025)
    bmesh.ops.translate(bm, verts=g["verts"], vec=(fx, fy, wall_h - 0.09))
    for k in range(3):
        g = bmesh.ops.create_cube(bm, size=1.0)
        m = (Matrix.Translation((fx, fy, wall_h - 0.095)) @ Matrix.Rotation(k * 2 * math.pi / 3, 4, "Z")
             @ Matrix.Translation((0.13, 0, 0)) @ Matrix.Diagonal((0.2, 0.04, 0.004, 1)))
        bmesh.ops.transform(bm, matrix=m, verts=g["verts"])
    me = bpy.data.meshes.new("ground.Caretaker.fan")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(fan_m)
    ob = bpy.data.objects.new(me.name, me)
    coll.objects.link(ob)
    ob.parent = empty
    ob.matrix_parent_inverse = Matrix.Identity(4)
    return []
