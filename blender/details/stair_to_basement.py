"""The inside stair down to basement Court 1 (photo p20; site details.js
PLAN.stair). Twenty kota risers in the south strip of the double-height void,
from a landing at basement level rising west to arrive at ground level on the
void's west edge; treads only where they pass over the rooms the plan draws
below. Teak handrail on its court side. Round the void at ground level, a
teak balustrade of turned balusters, open on the west where the stair arrives
(the opening on the right in p20). The blue glass lantern hangs in the foyer
by the void. Stair in the basement frame, balustrade and lantern in the
ground frame; Three.js units."""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _trees

ST = dict(bottom=1.69, landing=2.05, z0=-0.97, z1=-0.6, risers=20, open=0.84)
VOID_G = (0.56, -0.65, 1.99, 0.8)       # ground-frame void over Court 1
ARRIVE = 0.42                           # west rail stops here; the stair arrives beyond
RAIL_H = 0.37
LANTERN = (0.32, 0.1)                   # ground frame x, z


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


def _rod(bm, a, b, r, segs=8):
    d = b - a
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=g["verts"])


def _baluster(bm, x, y, z0, h):
    """A turned baluster: stacked lathe segments (base, bulb, neck, top)."""
    prof = [(0.0, 0.011), (0.06, 0.011), (0.08, 0.007), (0.16, 0.016), (0.24, 0.007), (0.30, 0.009), (1.0, 0.009)]
    for (t0, r0), (t1, r1) in zip(prof, prof[1:]):
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=r0, radius2=r1, depth=(t1 - t0) * h)
        bmesh.ops.translate(bm, verts=g["verts"], vec=(x, y, z0 + (t0 + t1) / 2 * h))


def _balustrade(bm, a, b, h, step=0.065):
    """Straight run from a to b (Vector, z = base level): rail, base rail, balusters."""
    _rod(bm, a + Vector((0, 0, h)), b + Vector((0, 0, h)), 0.018, 6)
    _rod(bm, a + Vector((0, 0, 0.02)), b + Vector((0, 0, 0.02)), 0.012, 6)
    n = max(1, round((b - a).length / step))
    for i in range(n + 1):
        p = a.lerp(b, i / n)
        _baluster(bm, p.x, p.y, p.z + 0.03, h - 0.045)


def build(ctx):
    c = ctx["constants"]
    floors = c["FLOORS"]
    teak = ctx["mats"]["Teak"]
    kota = _trees.material(ctx, "Kota", "#B9A68A", 0.6)
    blue = _trees.material(ctx, "Blue Glass", "#2F9DA6", 0.15)
    brass = _trees.material(ctx, "Brass", "#9C7A3C", 0.35)
    b_info, g_info = floors["basement"], floors["ground"]
    # Ground void in the basement frame
    sx = g_info["offset"][0] - b_info["offset"][0]
    sz = g_info["offset"][1] - b_info["offset"][1]
    vx0, vz0, vx1, vz1 = VOID_G
    top = vx0 + sx
    upstairs = g_info["level"] - b_info["level"]
    st = ST
    z0s, z1s = st["z0"], min(st["z1"], vz1 + sz - 0.015)
    rise = (upstairs - 0.004) / st["risers"]
    run = (st["bottom"] - top) / st["risers"]
    bcoll, bempty = ctx["colls"]["basement"], ctx["empties"]["basement"]
    gcoll, gempty = ctx["colls"]["ground"], ctx["empties"]["ground"]

    stair = bmesh.new()
    _box(stair, st["bottom"], st["landing"], -z1s, -z0s, 0.0, 0.012)          # landing
    for i in range(st["risers"]):
        xa = st["bottom"] - (i + 1) * run
        hh = (i + 1) * rise
        y0 = 0.0 if xa + run / 2 > st["open"] else max(0.0, hh - 0.14)
        _box(stair, xa, xa + run, -z1s, -z0s, y0, hh)
    _mesh("basement.InsideStair", stair, bcoll, bempty, kota)

    rail = bmesh.new()
    yb = -(z0s - 0.015)
    r0 = Vector((st["bottom"], yb, 0.0))
    r1 = Vector((top + 0.05, yb, upstairs - rise))
    _rod(rail, r0 + Vector((0, 0, 0.36)), r1 + Vector((0, 0, 0.36)), 0.014)
    _rod(rail, Vector((st["landing"], yb, 0.36)), r0 + Vector((0, 0, 0.36)), 0.014)
    for i in range(0, st["risers"], 2):
        x = st["bottom"] - (i + 0.5) * run
        y = (i + 1) * rise
        _rod(rail, Vector((x, yb, y)), Vector((x, yb, y + 0.34)), 0.008)
    for x in (st["landing"], st["bottom"]):
        _box(rail, x - 0.015, x + 0.015, yb - 0.015, yb + 0.015, 0.0, 0.37)
    _mesh("basement.InsideStair.rail", rail, bcoll, bempty, teak)

    # Ground-level balustrade round the void, open on the west beyond ARRIVE
    o = 0.03
    bal = bmesh.new()
    P = lambda x, z: Vector((x, -z, 0.0))
    _balustrade(bal, P(vx0 - o, vz0 - o), P(vx0 - o, ARRIVE - 0.06), RAIL_H)     # west, part
    _balustrade(bal, P(vx1 + o, vz0 - o), P(vx1 + o, vz1 + o), RAIL_H)          # east
    _balustrade(bal, P(vx0 - o, vz0 - o), P(vx1 + o, vz0 - o), RAIL_H)          # north
    _balustrade(bal, P(vx0 + 0.2, vz1 + o), P(vx1 + o, vz1 + o), RAIL_H)        # south, clear of the arrival
    _mesh("ground.VoidBalustrade", bal, gcoll, gempty, teak)

    # Blue glass lantern in the foyer
    wall_h = c["WALL_H"]
    lx, ly = LANTERN[0], -LANTERN[1]
    gl, br = bmesh.new(), bmesh.new()
    zb = wall_h - 0.5
    g = bmesh.ops.create_icosphere(gl, subdivisions=2, radius=1.0)
    bmesh.ops.transform(gl, matrix=Matrix.Translation((lx, ly, zb + 0.07)) @ Matrix.Diagonal((0.045, 0.045, 0.075, 1)),
                        verts=g["verts"])
    for (zz, r1, r2, d) in ((zb - 0.012, 0.012, 0.03, 0.03), (zb + 0.14, 0.03, 0.02, 0.025)):
        g = bmesh.ops.create_cone(br, cap_ends=True, segments=10, radius1=r1, radius2=r2, depth=d)
        bmesh.ops.translate(br, verts=g["verts"], vec=(lx, ly, zz))
    for k in range(3):
        a = k * 2 * math.pi / 3
        _rod(br, Vector((lx + 0.022 * math.cos(a), ly + 0.022 * math.sin(a), zb + 0.15)),
             Vector((lx, ly, wall_h - 0.06)), 0.0025, 4)
    g = bmesh.ops.create_icosphere(br, subdivisions=1, radius=0.025)
    bmesh.ops.translate(br, verts=g["verts"], vec=(lx, ly, wall_h - 0.04))
    _mesh("ground.BlueLantern.glass", gl, gcoll, gempty, blue)
    _mesh("ground.BlueLantern.brass", br, gcoll, gempty, brass)
    return []
