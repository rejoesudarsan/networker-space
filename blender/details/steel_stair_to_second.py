"""The steel stair from the first floor to the second (photos p8, p35).
A dog-leg from the CAD's tread lines on both floor plans: flight one against
the court's north wall (first frame z -0.32..0.09) rising east from x 1.56 to
2.32, a landing at the east end (to the wall at 2.5), flight two beside it
(z -0.8..-0.38) rising west back to x 1.56 and the second floor. Eight
risers each (22 cm). Open steel stair as in p8: dark steel stringer plates,
teak treads, a steel rail of posts and thin rods on the open side. The
second-floor slab is opened over the stairwell (second frame x 0.83..1.88,
z -1.43..-0.53) in finish(). First frame, Three.js units."""
import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _cut, _trees

X_LO, X_HI, X_WALL = 1.56, 2.32, 2.6
F1 = (-0.32, 0.09)
F2 = (-0.8, -0.38)
N = 8
WELL_SECOND = (0.83, -1.43, 1.88, -0.53)


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


def _plate(bm, a, b, y, depth=0.09, t=0.012):
    """A sloped stringer plate from a to b (x, z) at Blender y."""
    d = Vector((b[0] - a[0], 0, b[1] - a[1]))
    g = bmesh.ops.create_cube(bm, size=1.0)
    rot = Vector((1, 0, 0)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    m = Matrix.Translation(((a[0] + b[0]) / 2, y, (a[1] + b[1]) / 2 - depth / 2)) @ rot @ Matrix.Diagonal((d.length, t, depth, 1))
    bmesh.ops.transform(bm, matrix=m, verts=g["verts"])


def _rod(bm, a, b, r):
    d = b - a
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=g["verts"])


def build(ctx):
    c = ctx["constants"]
    coll, empty = ctx["colls"]["first"], ctx["empties"]["first"]
    teak = ctx["mats"]["Teak"]
    steel = _trees.material(ctx, "Stair Steel", "#3E4744", 0.45)
    storey = c["STOREY"]
    rise = storey / (2 * N)
    run = (X_HI - X_LO) / N
    treads, metal = bmesh.new(), bmesh.new()
    flights = [(F1, X_LO, +1, 0.0), (F2, X_HI, -1, N * rise)]
    for (za, zb), x_start, sgn, base in flights:
        ya, yb = -zb, -za
        for i in range(N):
            x0 = x_start + sgn * i * run
            x1 = x0 + sgn * run
            top = base + (i + 1) * rise
            _box(treads, min(x0, x1), max(x0, x1), ya + 0.01, yb - 0.01, top - 0.02, top)
        a = (x_start, base)
        b = (x_start + sgn * N * run, base + N * rise)
        for y in (ya + 0.006, yb - 0.006):
            _plate(metal, a, b, y)
    # Landing at the east end, mid-height, both flights wide
    _box(treads, X_HI, X_WALL, -F1[1], -F2[0], N * rise - 0.02, N * rise)
    _box(metal, X_HI, X_WALL, -F1[1], -F2[0], N * rise - 0.09, N * rise - 0.02)
    # Rail on the open (north) side of flight two and the hall side of flight one
    rail = bmesh.new()
    for (za, zb), x_start, sgn, base in flights:
        y = -za + 0.0 if sgn > 0 else -za
        y = -za if sgn < 0 else -za      # north edge of each flight
        p0 = Vector((x_start, y, base + 0.36))
        p1 = Vector((x_start + sgn * N * run, y, base + N * rise + 0.36))
        _rod(rail, p0, p1, 0.01)
        for k in (1, 2, 3):
            dz = 0.36 * k / 4
            _rod(rail, p0 - Vector((0, 0, 0.36 - dz)), p1 - Vector((0, 0, 0.36 - dz)), 0.003)
        for i in range(0, N + 1, 2):
            x = x_start + sgn * i * run
            z = base + max(1, i) * rise
            _rod(rail, Vector((x, y, z)), Vector((x, y, z + 0.36)), 0.007)
    _mesh("first.SteelStair.treads", treads, coll, empty, teak)
    _mesh("first.SteelStair.stringers", metal, coll, empty, steel)
    _mesh("first.SteelStair.rail", rail, coll, empty, steel)
    return []


def finish(ctx):
    x0, z0, x1, z1 = WELL_SECOND
    ok = _cut.cut_box(ctx, "second.slab", x0, x1, -z1, -z0, -1.0, 1.0)
    ctx["helpers"]["info"]("steel_stair_to_second: stairwell opened in second.slab (%s)" % ok)
