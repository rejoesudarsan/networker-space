"""Environment (Astra comps home-03, home-19): the street gulmohars rebuilt as
airy trees instead of the low-poly blob crowns of gulmohar_trees.

Same four trees (positions, heights, flower counts from gulmohar_trees.TREES).
Each one is a slim trunk forking at about 40% of its height into three or
four limbs that branch three more times into a vase/umbrella; the crown is a
few hundred fine feathery fronds (gulmohar leaves are bipinnate) sprayed from
the twig tips and the outer branches, with gaps the sky shows through, and
small orange-red blossom clusters on the outer and upper shell.

Built for the light bake: bake_site joins everything under Site.Units into
one atlas, so each frond is a single edge-connected strip (a narrow spine
with leaflet triangles hanging off it) and each blossom cluster a single
triangle fan: one UV island each, not one per leaflet. Branch cylinders are
open-ended and thin ones have four sides. Replaces the objects
Site.Gulmohar.<i>.* with .wood, .leaf, .leaf2, .blossom0, .blossom1.
Model units (1 = 8 ft), parented to Site.Units like the originals."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

from . import _trees
from .gulmohar_trees import TREES

UP = Vector((0, 0, 1))
LEAF_DARK = ("Gulmohar Leaf", "#4C5A3A", 0.75)
LEAF_LIGHT = ("Gulmohar Leaf Light", "#6A7A4C", 0.75)
BLOSSOM = (("Gulmohar Blossom", "#D9472A", 0.6), ("Gulmohar Blossom Light", "#EE7A3A", 0.6))


def _branch(bm, a, b, r0, r1, segs):
    d = b - a
    g = bmesh.ops.create_cone(bm, cap_ends=False, segments=segs, radius1=r0, radius2=r1, depth=d.length)
    rot = UP.rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=g["verts"])


def _deviate(d, angle, spin):
    """d turned by `angle` away from itself, toward azimuth `spin` around it."""
    side = d.cross(UP if abs(d.z) < 0.95 else Vector((1, 0, 0))).normalized()
    side.rotate(Quaternion(d, spin))
    return (Quaternion(side, angle) @ d).normalized()


def _frond(bm, o, f, length, width, roll, segs=7):
    """A feathery leaf spray: a narrow spine from o along f, drooping, with
    forward-swept leaflet triangles on both edges. One connected strip."""
    s = f.cross(UP)
    if s.length < 1e-4:
        s = Vector((1, 0, 0))
    s.normalize()
    s.rotate(Quaternion(f, roll))
    n = s.cross(f).normalized()
    spine = 0.0045
    left, right = [], []
    pts = []
    for i in range(segs + 1):
        t = i / segs
        c = o + f * length * t - UP * 0.28 * length * t * t
        pts.append(c)
        left.append(bm.verts.new(c + s * spine * (1 - 0.7 * t)))
        right.append(bm.verts.new(c - s * spine * (1 - 0.7 * t)))
    for i in range(segs):
        bm.faces.new((left[i], right[i], right[i + 1], left[i + 1]))
        t = (i + 0.5) / segs
        w = width * (0.55 + 1.6 * t * (1 - t)) * (1 - 0.35 * t)
        tip = pts[i] + (pts[i + 1] - pts[i]) * 1.6
        for side, row in ((1, left), (-1, right)):
            v = bm.verts.new(tip + s * side * w + n * 0.004 * side)
            if side == 1:
                bm.faces.new((row[i + 1], row[i], v))
            else:
                bm.faces.new((row[i], row[i + 1], v))


def _blossom(bm, c, nrm, r, rnd):
    """A flat cluster of petals: one triangle fan, ragged rim."""
    t1 = nrm.cross(Vector((1, 0, 0)) if abs(nrm.x) < 0.9 else Vector((0, 1, 0))).normalized()
    t2 = nrm.cross(t1)
    centre = bm.verts.new(c + nrm * r * 0.6)
    k = 7
    rim = []
    for j in range(k):
        a = j / k * math.tau + rnd.uniform(-0.2, 0.2)
        rr = r * (1.0 if j % 2 == 0 else rnd.uniform(0.45, 0.7))
        rim.append(bm.verts.new(c + (t1 * math.cos(a) + t2 * math.sin(a)) * rr + nrm * rnd.uniform(-0.2, 0.2) * r))
    for j in range(k):
        bm.faces.new((centre, rim[j], rim[(j + 1) % k]))


def gulmohar(ctx, name, loc, coll, parent, height, flowers, seed):
    rnd = random.Random(seed)
    H = height
    wood, leaves, leaves2 = bmesh.new(), bmesh.new(), bmesh.new()
    blossoms = [bmesh.new(), bmesh.new()]
    tips = []         # (point, direction)
    twigs = []        # (a, b) of the outer two branch orders, for fronds along them

    # Trunk: slim, slightly leaning, in three pieces.
    lean = Vector((rnd.uniform(-0.06, 0.06), rnd.uniform(-0.04, 0.04), 1)).normalized()
    fork = Vector((0, 0, 0)) + lean * H * rnd.uniform(0.4, 0.46)
    _branch(wood, Vector((0, 0, -0.05)), fork * 0.5, 0.07, 0.058, 7)
    _branch(wood, fork * 0.5, fork, 0.058, 0.048, 7)

    crown_r = 0.5 * H

    def grow(p, d, length, r, depth):
        mid = p + d * length * 0.5
        bend = (d + Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), -0.12))).normalized()
        end = mid + bend * length * 0.5
        # Keep the crown inside its umbrella: pull far reaches back in.
        hz = Vector((end.x, end.y, 0))
        if hz.length > crown_r:
            end = Vector((hz.x * crown_r / hz.length, hz.y * crown_r / hz.length, end.z))
        segs = 6 if depth < 2 else (4 if depth < 4 else 3)
        _branch(wood, p, mid, r, r * 0.85, segs)
        _branch(wood, mid, end, r * 0.85, r * 0.7, segs)
        if depth >= 2:
            twigs.append((p, end, depth))
        if depth == 5:
            tips.append((end, (end - p).normalized()))
            return
        n = 2 if rnd.random() < 0.55 else 3
        for k in range(n):
            nd = _deviate(bend, rnd.uniform(0.3, 0.62), k * math.tau / n + rnd.uniform(-0.6, 0.6))
            out = Vector((end.x, end.y, 0))
            if out.length > 1e-3:
                nd = (nd + out.normalized() * 0.15 + UP * (0.35 if k == 0 else 0.0)).normalized()
            nd.z = max(min(nd.z, 0.8), -0.2)
            nd.normalize()
            grow(end, nd, length * rnd.uniform(0.66, 0.78), r * 0.66, depth + 1)

    limbs = 4 if rnd.random() < 0.5 else 5
    az0 = rnd.uniform(0, math.tau)
    for i in range(limbs):
        az = az0 + i * math.tau / limbs + rnd.uniform(-0.35, 0.35)
        el = math.radians(rnd.uniform(32, 52) if i else rnd.uniform(68, 80))
        d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
        grow(fork, d, H * rnd.uniform(0.19, 0.23), 0.03, 1)

    # Foliage: sprays of fronds at every tip, a few more along the outer twigs.
    def spray(p, d, n):
        out = Vector((p.x, p.y, 0))
        out = out.normalized() if out.length > 1e-3 else d
        for _ in range(n):
            f = (d * 0.5 + out * 0.5 + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.3, 0.6)))).normalized()
            f.z = max(min(f.z, 0.45), -0.35)
            f.normalize()
            o = p + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.5, 0.5))) * 0.05
            L = rnd.uniform(0.2, 0.32)
            target = leaves if rnd.random() < 0.62 else leaves2
            _frond(target, o, f, L, L * rnd.uniform(0.22, 0.3), rnd.uniform(-0.5, 0.5), segs=6)
            ends.append(o + f * L - UP * 0.28 * L)

    ends = []
    for p, d in tips:
        spray(p, d, rnd.randint(4, 6))
    for a, b, depth in twigs:
        for _ in range(2 if depth >= 4 else 1):
            u = rnd.uniform(0.35, 0.95)
            spray(a + (b - a) * u, (b - a).normalized(), 1)

    # Blossom clusters on the outer and upper shell of the crown.
    if flowers:
        zs = [p.z for p in ends]
        z_mid = (min(zs) + max(zs)) / 2
        shell = [p for p in ends if p.z > z_mid or Vector((p.x, p.y, 0)).length > crown_r * 0.7]
        for i in range(flowers):
            p = rnd.choice(shell)
            c = p + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 1))) * 0.04
            out = Vector((c.x, c.y, 0))
            out = out.normalized() if out.length > 1e-3 else Vector((0, -1, 0))
            nrm = (UP * 1.2 + out * 0.5 + Vector((0, -0.35, 0)) +
                   Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0)) * 0.3).normalized()
            _blossom(blossoms[0 if i % 3 else 1], c, nrm, rnd.uniform(0.03, 0.045), rnd)

    stats = {}
    parts = [(".wood", wood, _trees.material(ctx, "Bark", "#5A4636", 0.9)),
             (".leaf", leaves, _trees.material(ctx, *LEAF_DARK)),
             (".leaf2", leaves2, _trees.material(ctx, *LEAF_LIGHT))]
    for j, (mname, hx, rough) in enumerate(BLOSSOM):
        parts.append((".blossom%d" % j, blossoms[j], _trees.material(ctx, mname, hx, rough)))
    for suffix, bm, mat in parts:
        if not len(bm.faces):
            bm.free()
            continue
        stats[suffix] = len(bm.faces)
        _trees._obj(name + suffix, bm, coll, parent, mat, loc)
    return stats


def build(ctx):
    units = bpy.data.objects.get("Site.Units")
    if units is None:
        ctx["helpers"]["warn"]("gulmohar_refine: no Site.Units frame")
        return []
    coll = ctx["helpers"]["get_collection"]("Trees", ctx["site"])
    for o in [o for o in bpy.data.objects if o.name.startswith("Site.Gulmohar.")]:
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    for i, (x, z, h, s, f) in enumerate(TREES):
        stats = gulmohar(ctx, "Site.Gulmohar.%d" % i, (x, -z, 0.0), coll, units,
                         height=h, flowers=int(f * 4), seed=31 + i)
        ctx["helpers"]["info"]("gulmohar_refine: tree %d faces %d (%s)"
                               % (i, sum(stats.values()), ", ".join("%s %d" % kv for kv in stats.items())))
    return []
