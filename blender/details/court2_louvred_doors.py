"""The Double HT Court's east wall (photos p11, p14): three bays of teak
louvred shutter pairs over a red-oxide plastered dado, a steel bar across
each, between plaster piers. The CAD draws this wall solid, so they are
mounted on its court face. Also the woven roman blinds on Living 2's south
window, seen through the court's open south side in p14 (the "teak blinds").
First frame, Three.js units."""
import bmesh
import bpy
from mathutils import Matrix

from . import _trees

WALL_X = 2.51
BAYS = [(0.3, 0.7), (0.8, 1.2), (1.3, 1.62)]   # z ranges on the east wall
DADO_H = 0.36
TOP_H = 1.02
LIVING2_WIN = (1.52, 2.67, 4.07)               # x0, x1, z of the south window (openings.json)
SILL_H, WINDOW_H = 22 / 96, 0.86


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


def build(ctx):
    coll, empty = ctx["colls"]["first"], ctx["empties"]["first"]
    teak = ctx["mats"]["Teak"]
    red = ctx["mats"].get("Red Oxide") or _trees.material(ctx, "Red Oxide", "#884B45", 0.3)
    steel = ctx["mats"]["Charcoal Steel"]
    weave = _trees.material(ctx, "Woven Blind", "#A88A5E", 0.9)
    x = WALL_X
    frame, slats, dado, bars, blinds = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    for (za, zb) in BAYS:
        ya, yb = -zb, -za
        _box(dado, x - 0.02, x, ya, yb, 0.0, DADO_H)                      # red-oxide dado
        _box(frame, x - 0.03, x, ya, yb, DADO_H, DADO_H + 0.03)           # sill
        _box(frame, x - 0.03, x, ya, yb, TOP_H - 0.03, TOP_H)             # head
        ym = (ya + yb) / 2
        for yy in (ya, ym - 0.008, ym + 0.008, yb):                       # stiles
            _box(frame, x - 0.03, x, yy - 0.012, yy + 0.012, DADO_H, TOP_H)
        z = DADO_H + 0.06
        while z < TOP_H - 0.05:                                           # louvres, tilted by stepping
            _box(slats, x - 0.026, x - 0.004, ya + 0.012, yb - 0.012, z, z + 0.012)
            _box(slats, x - 0.018, x - 0.004, ya + 0.012, yb - 0.012, z + 0.012, z + 0.02)
            z += 0.035
        _box(bars, x - 0.05, x - 0.04, ya + 0.01, yb - 0.01, DADO_H + 0.12, DADO_H + 0.13)
    _mesh("first.Court2.louvreFrames", frame, coll, empty, teak)
    _mesh("first.Court2.louvres", slats, coll, empty, teak)
    _mesh("first.Court2.dado", dado, coll, empty, red)
    _mesh("first.Court2.louvreBars", bars, coll, empty, steel)

    # Roman blinds on Living 2's south window, four panels, part lowered
    x0, x1, z = LIVING2_WIN
    y = -z + 0.05
    n = 4
    w = (x1 - x0) / n
    for i in range(n):
        a, b = x0 + i * w + 0.01, x0 + (i + 1) * w - 0.01
        drop = (0.55, 0.75, 0.0, 0.7)[i]                                  # one raised, as in p14
        top = SILL_H + WINDOW_H
        _box(blinds, a, b, y - 0.006, y, top - 0.06 - drop if drop else top - 0.08, top)
    _mesh("first.Living2.blinds", blinds, coll, empty, weave)
    return []
