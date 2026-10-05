"""Living 1 (photos p25, p27): the existing teak floor finish gets, over the
room itself (plan: x 0.62..2.33, z 1.33..3.2), short-strip plank seams and a teak skirting;
two amber-glass lanterns hang on brass chains with a ceiling fan between
them; the glazed teak French doors to the lawn stand in the south wall's door
gap (plan: x 0.6..1.14 at z 3.2); and the big south window gets its
horizontal steel grille bars. Ground frame, Three.js units; slab top = 0."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix

from . import _trees

ROOM = (0.62, 1.33, 2.33, 3.2)     # the room itself per the plan; the finish rect also runs over the office toilet and the void
TOP = 0.0085                       # just above the 2 cm finish
DOOR = dict(x0=0.6, x1=1.14, z=3.2, h=84 / 96)
LANTERNS = [(1.45, 1.85), (1.45, 2.8)]
FAN = (1.45, 2.32)
SILL_H, WINDOW_H = 22 / 96, 0.86


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


def _box(bm, x0, x1, y0, y1, z0, z1):
    g = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
                        @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)), verts=g["verts"])


def build(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    coll, empty = ctx["colls"]["ground"], ctx["empties"]["ground"]
    teak = ctx["mats"]["Teak"]
    seam = _trees.material(ctx, "Teak Seam", "#3A2214", 0.6)
    amber = _trees.material(ctx, "Amber Glass", "#C9761E", 0.25)
    brass = _trees.material(ctx, "Brass", "#9C7A3C", 0.35)
    white = _trees.material(ctx, "Fan White", "#E4E2DC", 0.5)
    steel = ctx["mats"]["Charcoal Steel"]
    glass = ctx["mats"].get("Glass") or bpy.data.materials.get("Glass")
    wall_h = c["WALL_H"]
    rnd = random.Random(25)
    x0, z0, x1, z1 = ROOM

    # Plank seams: rows running toward the window (along z), staggered short strips
    bm = bmesh.new()
    x = x0 + 0.03
    while x < x1 - 0.01:
        _box(bm, x - 0.0015, x + 0.0015, -z1, -z0, TOP, TOP + 0.001)
        z = z0 + rnd.uniform(0.0, 0.2)
        while z < z1:
            _box(bm, x, min(x + 0.03, x1), -z - 0.0015, -z + 0.0015, TOP, TOP + 0.001)
            z += rnd.uniform(0.14, 0.32)
        x += 0.03
    _mesh("ground.Living1.seams", bm, coll, empty, seam)
    # Teak skirting on the side walls
    for xs in (x0, x1):
        h["add_box"]("ground.Living1.skirting", xs - 0.006 if xs == x0 else xs - 0.006, xs + 0.006,
                     -z1, -z0, 0.0, 0.035, coll, empty, teak)

    # Lanterns on chains, and the fan
    bm_glass, bm_brass = bmesh.new(), bmesh.new()
    for (lx, lz) in LANTERNS:
        y = -lz
        zb = wall_h - 0.42
        g = bmesh.ops.create_cone(bm_glass, cap_ends=True, segments=6, radius1=0.032, radius2=0.032, depth=0.075)
        bmesh.ops.translate(bm_glass, verts=g["verts"], vec=(lx, y, zb + 0.0375))
        for (zz, r) in ((zb - 0.006, 0.036), (zb + 0.081, 0.03)):
            g = bmesh.ops.create_cone(bm_brass, cap_ends=True, segments=6, radius1=r, radius2=r * 0.7, depth=0.012)
            bmesh.ops.translate(bm_brass, verts=g["verts"], vec=(lx, y, zz))
        g = bmesh.ops.create_cone(bm_brass, cap_ends=True, segments=4, radius1=0.003, radius2=0.003,
                                  depth=wall_h - (zb + 0.087))
        bmesh.ops.translate(bm_brass, verts=g["verts"], vec=(lx, y, (wall_h + zb + 0.087) / 2))
    _mesh("ground.Living1.lanternGlass", bm_glass, coll, empty, amber)
    _mesh("ground.Living1.lanternBrass", bm_brass, coll, empty, brass)
    bm = bmesh.new()
    fx, fy = FAN[0], -FAN[1]
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.006, radius2=0.006, depth=0.12)
    bmesh.ops.translate(bm, verts=g["verts"], vec=(fx, fy, wall_h - 0.06))
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.03, radius2=0.025, depth=0.03)
    bmesh.ops.translate(bm, verts=g["verts"], vec=(fx, fy, wall_h - 0.13))
    for k in range(3):
        a = k * 2 * math.pi / 3
        g = bmesh.ops.create_cube(bm, size=1.0)
        m = (Matrix.Translation((fx, fy, wall_h - 0.135)) @ Matrix.Rotation(a, 4, "Z")
             @ Matrix.Translation((0.2, 0, 0)) @ Matrix.Diagonal((0.34, 0.045, 0.004, 1)))
        bmesh.ops.transform(bm, matrix=m, verts=g["verts"])
    _mesh("ground.Living1.fan", bm, coll, empty, white)

    # French doors: two glazed teak leaves, closed, in the door gap
    d = DOOR
    yf = -d["z"]
    frame, panes = bmesh.new(), bmesh.new()
    w = (d["x1"] - d["x0"]) / 2
    t = 0.022
    for i in range(2):
        a, b = d["x0"] + i * w, d["x0"] + (i + 1) * w
        _box(frame, a, a + t, yf - 0.012, yf + 0.012, 0.0, d["h"])
        _box(frame, b - t, b, yf - 0.012, yf + 0.012, 0.0, d["h"])
        for (za, zb) in ((0.0, 0.1), (d["h"] - t, d["h"]), (0.42, 0.42 + t)):
            _box(frame, a, b, yf - 0.012, yf + 0.012, za, zb)
        _box(panes, a + t, b - t, yf - 0.003, yf + 0.003, 0.1, d["h"] - t)
        for zz in (0.18, 0.28, 0.55, 0.66, 0.77):          # horizontal grille bars, as in p25
            _box(frame, a + t, b - t, yf - 0.006, yf + 0.006, zz, zz + 0.008)
    _mesh("ground.Living1.doorFrames", frame, coll, empty, teak)
    if glass is not None:
        _mesh("ground.Living1.doorGlass", panes, coll, empty, glass)
    else:
        panes.free()

    # Grille bars on the south window: find its sill island near z = 3.2
    import __main__
    islands = getattr(__main__, "mesh_islands", None)
    sills = bpy.data.objects.get("ground.sills")
    n = 0
    if islands and sills is not None:
        verts = [v.co[:] for v in sills.data.vertices]
        polys = [p.vertices[:] for p in sills.data.polygons]
        bm = bmesh.new()
        for (ax, bx, ay, by) in islands(verts, polys):
            if bx - ax < 0.18 or by - ay > 0.2:
                continue
            if not (ax < x1 and bx > x0 and abs((ay + by) / 2 + z1) < 0.15):   # overlaps the room's south wall
                continue
            yc = (ay + by) / 2 + 0.035          # room side of the glass (+y is inside)
            zz = SILL_H + 0.08
            while zz < SILL_H + WINDOW_H - 0.04:
                _box(bm, ax + 0.02, bx - 0.02, yc - 0.004, yc + 0.004, zz, zz + 0.008)
                zz += 0.085
            n += 1
        _mesh("ground.Living1.windowGrille", bm, coll, empty, steel)
    h["info"]("living1: grille on %d south window(s)" % n)
    return []
