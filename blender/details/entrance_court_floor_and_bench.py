"""The entrance court (photo p24): large brown stone slabs underfoot, the green
slatted bench with its footstool against the court's east wall beside the door
into the house, and the low plank shelf of potted plants along the north wall.
Stone extent from site/src/world/details.js (entrance court stone,
x -2.3..-1.55, z -0.3..1.3). Ground frame, Three.js units; slab top = 0."""
import random

import bmesh
import bpy
from mathutils import Matrix

from . import _trees

STONE = (-2.3, -0.3, -1.55, 1.3)     # x0, z0, x1, z1
TOP = 0.012
BENCH = dict(x=-1.66, z=0.78, length=0.5, depth=0.2, seat=0.19, back=0.36)   # back to the east wall
STOOL = dict(x=-1.92, z=0.62, length=0.26, depth=0.12, h=0.15)
SHELF = dict(x0=-2.28, x1=-1.75, z=-0.22, depth=0.12, h=0.07)


def _slats(h, name, x0, x1, y0, y1, z, coll, empty, mat, n, along_y=True):
    """n slats with gaps across the short side."""
    span = (x1 - x0) if along_y else (y1 - y0)
    w = span / n * 0.72
    for i in range(n):
        c = (i + 0.5) / n
        if along_y:
            xc = x0 + c * (x1 - x0)
            h["add_box"](name, xc - w / 2, xc + w / 2, y0, y1, z, z + 0.012, coll, empty, mat)
        else:
            yc = y0 + c * (y1 - y0)
            h["add_box"](name, x0, x1, yc - w / 2, yc + w / 2, z, z + 0.012, coll, empty, mat)


def build(ctx):
    h = ctx["helpers"]
    coll, empty = ctx["colls"]["ground"], ctx["empties"]["ground"]
    stone = _trees.material(ctx, "Entrance Stone", "#A08066", 0.8)
    joint = _trees.material(ctx, "Stone Joint", "#8C7F6C", 0.9)
    green = _trees.material(ctx, "Bench Green", "#1F6B4E", 0.45)
    white = _trees.material(ctx, "Bench Frame", "#D9D9D4", 0.5)
    teak = ctx["mats"]["Teak"]
    terracotta = ctx["mats"]["Terracotta"]
    leaf = _trees.material(ctx, "Pot Plant", "#4F7A3A", 0.75)

    # Stone floor in large irregular slabs
    x0, z0, x1, z1 = STONE
    h["add_box"]("ground.EntranceStone", x0, x1, -z1, -z0, 0.0, TOP, coll, empty, stone)
    rnd = random.Random(24)
    z = z0
    while z < z1 - 0.05:
        zn = min(z + rnd.uniform(0.22, 0.32), z1)
        h["add_box"]("ground.EntranceStone.joint", x0, x1, -zn - 0.004, -zn + 0.004, TOP, TOP + 0.002,
                     coll, empty, joint)
        x = x0 + rnd.uniform(0.12, 0.3)
        while x < x1 - 0.08:
            h["add_box"]("ground.EntranceStone.joint", x - 0.004, x + 0.004, -zn, -z, TOP, TOP + 0.002,
                         coll, empty, joint)
            x += rnd.uniform(0.25, 0.4)
        z = zn

    # Bench: back against the east wall, seat facing west (Blender x = Three x, y = -z)
    b = BENCH
    bx1 = b["x"] + b["depth"] / 2          # back edge (east)
    bx0 = b["x"] - b["depth"] / 2
    by0, by1 = -(b["z"] + b["length"] / 2), -(b["z"] - b["length"] / 2)
    for y in (by0 + 0.015, by1 - 0.015):   # cast end frames: legs, arm, back post
        h["add_box"]("ground.Bench.frame", bx0, bx0 + 0.012, y - 0.006, y + 0.006, TOP, b["seat"], coll, empty, white)
        h["add_box"]("ground.Bench.frame", bx1 - 0.012, bx1, y - 0.006, y + 0.006, TOP, b["back"], coll, empty, white)
        h["add_box"]("ground.Bench.frame", bx0, bx1, y - 0.006, y + 0.006, b["seat"] - 0.012, b["seat"], coll, empty, white)
        h["add_box"]("ground.Bench.frame", bx0, bx1 - 0.02, y - 0.006, y + 0.006, b["seat"] + 0.07, b["seat"] + 0.08, coll, empty, white)
    _slats(h, "ground.Bench.seat", bx0, bx1 - 0.015, by0, by1, b["seat"], coll, empty, green, 4)
    for i in range(5):                     # back slats, stacked
        zz = b["seat"] + 0.03 + i * (b["back"] - b["seat"] - 0.03) / 5
        h["add_box"]("ground.Bench.back", bx1 - 0.02, bx1 - 0.008, by0 + 0.01, by1 - 0.01, zz, zz + 0.022,
                     coll, empty, green)

    # Footstool
    s = STOOL
    sx0, sx1 = s["x"] - s["depth"] / 2, s["x"] + s["depth"] / 2
    sy0, sy1 = -(s["z"] + s["length"] / 2), -(s["z"] - s["length"] / 2)
    for (xx, yy) in ((sx0, sy0), (sx1, sy0), (sx0, sy1), (sx1, sy1)):
        h["add_box"]("ground.Stool.leg", xx - 0.005, xx + 0.005, yy - 0.005, yy + 0.005, TOP, s["h"], coll, empty, white)
    _slats(h, "ground.Stool.top", sx0, sx1, sy0, sy1, s["h"], coll, empty, green, 3)

    # Plank shelf with pots along the north wall
    sh = SHELF
    yb0, yb1 = -(sh["z"] + sh["depth"] / 2), -(sh["z"] - sh["depth"] / 2)
    h["add_box"]("ground.PlantShelf", sh["x0"], sh["x1"], yb0, yb1, sh["h"] - 0.015, sh["h"], coll, empty, teak)
    for xx in (sh["x0"] + 0.03, sh["x1"] - 0.03):
        h["add_box"]("ground.PlantShelf.leg", xx - 0.015, xx + 0.015, yb0, yb1, TOP, sh["h"] - 0.015, coll, empty, teak)
    pots, leaves = bmesh.new(), bmesh.new()
    n = 4
    for i in range(n):
        cx = sh["x0"] + (i + 0.5) * (sh["x1"] - sh["x0"]) / n
        cy = (yb0 + yb1) / 2
        r = rnd.uniform(0.035, 0.045)
        g = bmesh.ops.create_cone(pots, cap_ends=True, segments=10, radius1=r * 0.75, radius2=r, depth=0.07)
        bmesh.ops.translate(pots, verts=g["verts"], vec=(cx, cy, sh["h"] + 0.035))
        for k in range(5):
            g = bmesh.ops.create_icosphere(leaves, subdivisions=1, radius=1.0)
            q = rnd.uniform(0.035, 0.06)
            m = Matrix.Translation((cx + rnd.uniform(-0.04, 0.04), cy + rnd.uniform(-0.04, 0.04),
                                    sh["h"] + 0.09 + rnd.uniform(0, 0.08))) @ Matrix.Diagonal((q, q, q * 0.8, 1))
            bmesh.ops.transform(leaves, matrix=m, verts=g["verts"])
    for bm, nm, mat in ((pots, "ground.PlantShelf.pots", terracotta), (leaves, "ground.PlantShelf.plants", leaf)):
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        ob = bpy.data.objects.new(nm, me)
        coll.objects.link(ob)
        ob.parent = empty
        ob.matrix_parent_inverse = Matrix.Identity(4)
    return []
