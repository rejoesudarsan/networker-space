"""The skylight over the Double HT Court (photos p1, p11): the roof slab is
opened over the second-floor courtyard void (second frame x 0.18..1.88,
z -0.49..1.06), with a plastered kerb round the opening and a steel-framed
glass light on it, gently pitched, with glazing bars. The roof and its Empty
are made after the detail modules run, so everything happens in finish().
Roof frame (Floor.roof: second frame, raised to the roof underside); units."""
import bmesh
import bpy
from mathutils import Matrix

from . import _cut, _trees

VOID = (0.18, -0.49, 1.88, 1.06)     # second frame x0, z0, x1, z1
KERB_H, KERB_T = 0.1, 0.05
BAR_STEP = 0.28


def build(ctx):
    return []


def _box(bm, x0, x1, y0, y1, z0, z1):
    g = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
                        @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)), verts=g["verts"])


def _mesh(name, bm, coll, parent, mat):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.parent = parent
    ob.matrix_parent_inverse = Matrix.Identity(4)
    return ob


def finish(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    roof = bpy.data.objects.get("Floor.roof")
    coll = ctx.get("roof_coll") or bpy.data.collections.get("Roof")
    if roof is None or coll is None:
        h["warn"]("skylight: no Floor.roof")
        return
    x0, z0, x1, z1 = VOID
    y0, y1 = -z1, -z0
    slab_t = c["SLAB_T"]
    ok = _cut.cut_box(ctx, "roof.slab", x0, x1, y0, y1, -1.0, 1.0)
    plaster = ctx["mats"]["Lime White"]
    steel = ctx["mats"]["Charcoal Steel"]
    glass = ctx["mats"].get("Glass") or bpy.data.materials.get("Glass") or _trees.material(ctx, "Sky Glass", "#DFE8EA", 0.05)
    kerb, bars, panes = bmesh.new(), bmesh.new(), bmesh.new()
    zt = slab_t + KERB_H
    t = KERB_T
    _box(kerb, x0 - t, x1 + t, y0 - t, y0, slab_t, zt)
    _box(kerb, x0 - t, x1 + t, y1, y1 + t, slab_t, zt)
    _box(kerb, x0 - t, x0, y0, y1, slab_t, zt)
    _box(kerb, x1, x1 + t, y0, y1, slab_t, zt)
    # Glass pitched along y (falls toward the street, -y): rise 0.06 over the span
    rise = 0.06
    span = y1 - y0
    zg = lambda y: zt + 0.02 + rise * (y - y0) / span
    n = max(2, round(span / BAR_STEP))
    for i in range(n):
        ya, yb = y0 + i * span / n, y0 + (i + 1) * span / n
        g = bmesh.ops.create_cube(panes, size=1.0)
        za, zb = zg(ya), zg(yb)
        # A thin pane following the pitch: shear the cube's top/bottom by y
        for v in g["verts"]:
            v.co.x = x0 + (v.co.x + 0.5) * (x1 - x0)
            yy = ya + (v.co.y + 0.5) * (yb - ya)
            v.co.y = yy
            v.co.z = zg(yy) + (v.co.z + 0.5) * 0.008
        for yy in (ya, yb):                                 # bars across
            _box(bars, x0 - t, x1 + t, yy - 0.012, yy + 0.012, zg(yy) - 0.01, zg(yy) + 0.022)
    m = max(2, round((x1 - x0) / BAR_STEP))
    for j in range(m + 1):                                   # bars along the pitch
        xx = x0 + j * (x1 - x0) / m
        g = bmesh.ops.create_cube(bars, size=1.0)
        for v in g["verts"]:
            v.co.x = xx + v.co.x * 0.024
            yy = y0 + (v.co.y + 0.5) * span
            v.co.y = yy
            v.co.z = zg(yy) - 0.01 + (v.co.z + 0.5) * 0.032
    _mesh("roof.SkylightKerb", kerb, coll, roof, plaster)
    _mesh("roof.SkylightBars", bars, coll, roof, steel)
    _mesh("roof.SkylightGlass", panes, coll, roof, glass)
    h["info"]("skylight: roof slab opened (%s), %d panes" % (ok, n))
