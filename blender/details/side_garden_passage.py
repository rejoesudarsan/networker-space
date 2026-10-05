"""The west side passage (photos p9, p36, p5; ground plan's west strip).

The street gate opens at street level (p5) onto a kota path that climbs to
the ground floor in two flights of four risers (the ground plan draws two
three-tread flights in the strip, at z 2.47..2.94 and 0.83..1.19; p36 sees
the lower one from the front with the boundary wall and its handrail on the
left; p9 looks down the passage at it). Eight risers of 0.091 units (22 cm)
make the 0.73-unit climb from street to floor.

The model used to put the gate on top of four outside steps; those steps go,
and the gate and its piers come down to street level. The passage is cut out
of the ground slab, retained on the house side, walled on the west with a
steel handrail by the flights, and lined with potted plants (p9), with p36's
ochre planter of pots beside the lower flight. Ground frame, Three.js units;
slab top = 0, street = -LEVEL."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _cut, _trees

X0, X1 = -2.95, -2.32          # passage between the west boundary and the house
Z_FRONT = 4.97
FLIGHTS = [(2.94, 2.47), (1.19, 0.83)]   # (bottom z, top z): rising north
RISERS = 4
WALL_X = (-3.14, -3.06)        # west boundary wall (encloses the plinth skirt at -3.13..-3.07; coplanar faces rendered dark)
GATE_X = (-3.075, -2.38)       # gate piers (centres)
PIER = (0.1, 0.12)             # w, d
ZF = 4.9                       # gate line


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


def _rod(bm, a, b, r):
    d = b - a
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=g["verts"])


def _levels(street):
    """Floor level along the passage: (z0, z1, top) segments, south to north."""
    rise = -street / (2 * RISERS)
    lo, mid = street, street + RISERS * rise
    (b2, t2), (b1, t1) = FLIGHTS
    return rise, [(b2, Z_FRONT, lo), (b1, t2, mid)], lo, mid


def build(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    coll, empty = ctx["colls"]["ground"], ctx["empties"]["ground"]
    street = -c["FLOORS"]["ground"]["level"]
    kota = _trees.material(ctx, "Kota", "#B9A68A", 0.6)
    brick = _trees.material(ctx, "Brick", "#8E4B32", 0.85)
    plaster = ctx["mats"]["Lime White"]
    shade = ctx["mats"]["Lime White Shade"]
    ochre = _trees.material(ctx, "Ochre Plaster", "#D9A441", 0.85)
    steel = ctx["mats"]["Charcoal Steel"]
    terracotta = ctx["mats"]["Terracotta"]
    leaf = _trees.material(ctx, "Pot Plant", "#4F7A3A", 0.75)
    leaf2 = _trees.material(ctx, "Pot Plant Light", "#6E9A45", 0.75)
    rise, segs, lo, mid = _levels(street)

    # The outside gate steps go: the gate is at street level
    old = bpy.data.objects.get("ground.gateSteps")
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)

    # Floors: solid kota-topped fills down to street level
    for (za, zb, top) in segs:
        h["add_box"]("ground.Passage.floor", X0, X1, -zb, -za, street, top + 0.012, coll, empty, kota)
    # Flights: stone treads on brick risers, rising north
    for (zb, zt), base in zip(FLIGHTS, (lo, mid)):
        run = (zb - zt) / RISERS
        for i in range(RISERS):
            z_lo = zb - (i + 1) * run
            z_hi = zb - i * run
            top = base + (i + 1) * rise
            h["add_box"]("ground.Passage.riser", X0, X1, -z_hi, -z_lo, street, top - 0.02, coll, empty, brick)
            h["add_box"]("ground.Passage.tread", X0 - 0.005, X1 + 0.005, -z_hi - 0.015, -z_lo, top - 0.02, top + 0.012,
                         coll, empty, kota)
    # Retaining wall on the house side, street to slab top
    h["add_box"]("ground.Passage.retaining", X1, X1 + 0.04, -Z_FRONT, -0.83, street, 0.0, coll, empty, shade)
    # West boundary wall: street up to ~1.7 m above the ground floor, as in p9
    h["add_box"]("ground.Passage.boundary", WALL_X[0], WALL_X[1], -Z_FRONT, -0.8, street, 0.7, coll, empty, plaster)
    h["add_box"]("ground.Passage.boundaryCap", WALL_X[0] - 0.01, WALL_X[1] + 0.01, -Z_FRONT, -0.8, 0.7, 0.72,
                 coll, empty, shade)

    # Handrail on the boundary wall along each flight, on brackets
    bm = bmesh.new()
    xr = WALL_X[1] + 0.035
    for (zb, zt), base in zip(FLIGHTS, (lo, mid)):
        a = Vector((xr, -(zb + 0.1), base + 0.36))
        b = Vector((xr, -(zt - 0.1), base + RISERS * rise + 0.36))
        _rod(bm, a, b, 0.009)
        for t in (0.15, 0.85):
            p = a.lerp(b, t)
            _rod(bm, p, Vector((WALL_X[1], p.y, p.z)), 0.006)
    _mesh("ground.Passage.handrail", bm, coll, empty, steel)

    # Gate at street level: new piers; the old ones on the plinth are cut away in finish()
    for x in GATE_X:
        h["add_box"]("ground.GatePier", x - PIER[0] / 2, x + PIER[0] / 2, -(ZF + PIER[1] / 2), -(ZF - PIER[1] / 2),
                     street, street + 0.8, coll, empty, plaster)
        h["add_box"]("ground.GatePier.cap", x - 0.065, x + 0.065, -(ZF + 0.075), -(ZF - 0.075),
                     street + 0.8, street + 0.825, coll, empty, shade)
    gate = bpy.data.objects.get("ground.streetGate")
    if gate is not None:
        gate.location.z = street

    # p36's ochre planter of pots on the east side, beside the lower flight
    h["add_box"]("ground.Passage.ochrePlanter", X1 - 0.16, X1, -3.25, -2.4, lo, mid + 0.06, coll, empty, ochre)
    # Potted plants: along the boundary on each level, on the planter, and by the house wall
    rnd = random.Random(9)
    pots, leaves, leaves2 = bmesh.new(), bmesh.new(), bmesh.new()

    def pot(x, z, y0, s):
        g = bmesh.ops.create_cone(pots, cap_ends=True, segments=10, radius1=0.035 * s, radius2=0.05 * s, depth=0.1 * s)
        bmesh.ops.translate(pots, verts=g["verts"], vec=(x, -z, y0 + 0.05 * s))
        for k in range(6):
            tgt = leaves if k % 3 else leaves2
            g = bmesh.ops.create_icosphere(tgt, subdivisions=1, radius=1.0)
            q = rnd.uniform(0.045, 0.075) * s
            # tall strappy clumps (bird of paradise, philodendron) read as stacked, leaning blobs
            m = Matrix.Translation((x + rnd.uniform(-0.05, 0.05) * s, -z + rnd.uniform(-0.05, 0.05) * s,
                                    y0 + (0.14 + rnd.uniform(0, 0.25)) * s)) @ Matrix.Diagonal((q, q, q * 1.3, 1))
            bmesh.ops.transform(tgt, matrix=m, verts=g["verts"])

    def level_at(z):
        if z > FLIGHTS[0][0]:
            return lo
        if z > FLIGHTS[1][0]:
            return mid
        return 0.0
    for z in (4.6, 4.2, 3.7, 3.25, 2.25, 1.85, 1.45):
        pot(-2.98, z, level_at(z) + 0.012, rnd.uniform(0.9, 1.3))
    for z in (4.4, 3.8, 2.0):
        pot(X1 - 0.07, z, level_at(z) + 0.012, rnd.uniform(1.0, 1.4))
    for z in (3.15, 2.85, 2.55):
        pot(X1 - 0.08, z, mid + 0.06, 0.8)
    _mesh("ground.Passage.pots", pots, coll, empty, terracotta)
    _mesh("ground.Passage.plants", leaves, coll, empty, leaf)
    _mesh("ground.Passage.plantsLight", leaves2, coll, empty, leaf2)
    return []


def finish(ctx):
    """Open the slab over the passage, cut the plinth skirt between the gate
    piers, and cut the old piers and copings off the plinth top."""
    street = -ctx["constants"]["FLOORS"]["ground"]["level"]
    big = 2.0
    ok = _cut.cut_box(ctx, "ground.slab", X0, X1, -(Z_FRONT + 0.1), -0.83, -big, big)
    _cut.cut_box(ctx, "ground.plinthSkirt", GATE_X[0] + 0.05, GATE_X[1] - 0.05, -(ZF + 0.2), -(ZF - 0.05), street - 0.01, big)
    _cut.cut_box(ctx, "ground.frontWall", GATE_X[0] - 0.08, GATE_X[1] + 0.06, -(ZF + 0.1), -(ZF - 0.1), -0.05, big)
    _cut.cut_box(ctx, "ground.copings", GATE_X[0] - 0.08, GATE_X[1] + 0.07, -(ZF + 0.1), -(ZF - 0.1), -0.05, big)
    ctx["helpers"]["info"]("side_garden_passage: passage opened in the ground slab (%s), gate brought to street level" % ok)
