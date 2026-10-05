"""Family 2 (photo p16; walls measured top-down: x 0.81..2.62,
z -2.83..-1.34, open to the south hall west of x 1.45). On the south wall,
the big teak sliding panel in horizontal boards, parked left of the opening
it closes, with four small coloured picture frames; a dropped bulkhead along
the south wall with a cove light washing the ceiling; the floating teak
shelf on a dark panel on the west wall; a woven blind on the east wall's
narrow window; the ceiling fan. First frame, Three.js units."""
import math

import bmesh
import bpy
from mathutils import Matrix

from . import _trees

ROOM = (0.81, -2.83, 2.62, -1.34)
DOOR = dict(x0=1.47, x1=2.08, h=0.9)
BULK_Z0 = 1.1
EAST_WIN = (-1.68, -1.40)


def _box(bm, x0, x1, y0, y1, z0, z1):
    g = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
                        @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)), verts=g["verts"])


def _mesh(name, bm, coll, empty, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.parent = empty
    ob.matrix_parent_inverse = Matrix.Identity(4)
    return ob


def _glow(ctx):
    m = bpy.data.materials.get("Cove Glow")
    if m:
        return m
    m, nt, bsdf = ctx["helpers"]["new_material"]("Cove Glow")
    col = (1.0, 0.86, 0.66, 1.0)
    bsdf.inputs["Base Color"].default_value = col
    for name in ("Emission Color", "Emission"):
        if name in bsdf.inputs:
            bsdf.inputs[name].default_value = col
            break
    if "Emission Strength" in bsdf.inputs:
        bsdf.inputs["Emission Strength"].default_value = 4.0
    m.diffuse_color = col
    return m


def build(ctx):
    c = ctx["constants"]
    coll, empty = ctx["colls"]["first"], ctx["empties"]["first"]
    teak = ctx["mats"]["Teak"]
    seam = _trees.material(ctx, "Teak Seam", "#3A2214", 0.6)
    plaster = ctx["mats"]["Lime White"]
    dark = _trees.material(ctx, "Shelf Panel", "#4A4C4E", 0.6)
    weave = _trees.material(ctx, "Woven Blind", "#A88A5E", 0.9)
    fan_m = _trees.material(ctx, "Fan White", "#E4E2DC", 0.5)
    frames = [_trees.material(ctx, "Frame %s" % hx, hx, 0.5) for hx in ("#C23B32", "#E0B32E", "#3A62B8", "#D9772B")]
    wall_h = c["WALL_H"]
    x0, z0, x1, z1 = ROOM
    ys = 1.375                                 # south wall room-side face (z -1.375, measured), room is y > ys
    wood, seams, misc, bulk = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()

    # Sliding panel, 3 cm off the wall on the room side, on a top track
    d = DOOR
    _box(wood, d["x0"], d["x1"], ys + 0.012, ys + 0.034, 0.0, d["h"])
    yy = 0.075
    while yy < d["h"]:
        _box(seams, d["x0"], d["x1"], ys + 0.034, ys + 0.036, yy - 0.002, yy + 0.002)
        yy += 0.075
    _box(misc, 1.4, 2.6, ys + 0.004, ys + 0.03, d["h"] + 0.005, d["h"] + 0.025)    # track
    fb = [bmesh.new() for _ in frames]
    for i in range(4):
        cx = d["x0"] + 0.14 + i * 0.11
        _box(fb[i], cx - 0.035, cx + 0.035, ys + 0.034, ys + 0.042, 0.5, 0.57)
    # Bulkhead along the south wall, with the cove strip on top
    _box(bulk, x0, x1, ys, ys + 0.18, BULK_Z0, wall_h)
    glow = bmesh.new()
    _box(glow, x0, x1, ys + 0.18, ys + 0.2, wall_h - 0.03, wall_h - 0.01)
    # Floating shelf on a dark panel, west wall
    _box(misc, x0, x0 + 0.01, -(-1.7), -(-2.3), 0.36, 0.5)
    _box(wood, x0, x0 + 0.13, -(-1.75), -(-2.25), 0.34, 0.37)
    # Woven blind on the east window
    _box(bmesh_blind := bmesh.new(), x1 - 0.03, x1 - 0.02, -EAST_WIN[1], -EAST_WIN[0], 0.2, 1.05)
    # Fan
    fan = bmesh.new()
    fx, fy = (x0 + x1) / 2, -(z0 + z1) / 2
    g = bmesh.ops.create_cone(fan, cap_ends=True, segments=10, radius1=0.03, radius2=0.025, depth=0.03)
    bmesh.ops.translate(fan, verts=g["verts"], vec=(fx, fy, wall_h - 0.14))
    g = bmesh.ops.create_cone(fan, cap_ends=True, segments=6, radius1=0.006, radius2=0.006, depth=0.12)
    bmesh.ops.translate(fan, verts=g["verts"], vec=(fx, fy, wall_h - 0.06))
    for k in range(3):
        g = bmesh.ops.create_cube(fan, size=1.0)
        m = (Matrix.Translation((fx, fy, wall_h - 0.145)) @ Matrix.Rotation(k * 2 * math.pi / 3, 4, "Z")
             @ Matrix.Translation((0.2, 0, 0)) @ Matrix.Diagonal((0.34, 0.045, 0.004, 1)))
        bmesh.ops.transform(fan, matrix=m, verts=g["verts"])
    _mesh("first.Family2.slidingDoor", wood, coll, empty, teak)
    _mesh("first.Family2.doorSeams", seams, coll, empty, seam)
    _mesh("first.Family2.trackAndPanel", misc, coll, empty, dark)
    for i, (b, m) in enumerate(zip(fb, frames)):
        _mesh("first.Family2.frame%d" % i, b, coll, empty, m)
    _mesh("first.Family2.bulkhead", bulk, coll, empty, plaster)
    _mesh("first.Family2.coveGlow", glow, coll, empty, _glow(ctx))
    _mesh("first.Family2.blind", bmesh_blind, coll, empty, weave)
    _mesh("first.Family2.fan", fan, coll, empty, fan_m)
    return []
