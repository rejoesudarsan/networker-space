"""The second floor around the courtyard void (photos p30, p32; measured
top-down: void x 0.19..1.88, z -0.44..1.05, second frame).

p30: the passage runs north-south along the void's open west side. In place
of a railing, a long low white cabinet with glass-fronted doors, drawers and
a light-wood top stands on the void's edge (z -0.42..0.4), then a plain
plaster upstand to the south wall. p32: the study nook in the stair-top hall
north of the void: a light-wood desk along its south wall (the wall with the
window into the void), a white drawer unit under its east end, a pier with a
black pinboard at its west end. A steel guard rail of thin rods on the
stairwell's open edges at second-floor level. Second frame, Three.js units."""
import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _trees

VOID_W = 0.19
CAB = dict(z0=-0.42, z1=0.40, depth=0.16, h=0.4)
UPSTAND = (0.46, 1.03)
DESK = dict(x0=-0.25, x1=0.82, z_wall=-0.53, depth=0.22, h=0.31)
WELL = dict(x=0.83, z0=-1.43, z1=-0.53, z_mid=-0.98, x_end=1.88)


def _box(bm, x0, x1, y0, y1, z0, z1):
    g = bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.transform(bm, matrix=Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
                        @ Matrix.Diagonal((x1 - x0, y1 - y0, z1 - z0, 1)), verts=g["verts"])


def _rod(bm, a, b, r):
    d = b - a
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=g["verts"])


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
    coll, empty = ctx["colls"]["second"], ctx["empties"]["second"]
    white = _trees.material(ctx, "White Laminate", "#ECEBE6", 0.4)
    wood = _trees.material(ctx, "Light Wood", "#CDB896", 0.5)
    trim = _trees.material(ctx, "Teak Edge", "#A9773F", 0.5)
    glass = ctx["mats"].get("Glass") or bpy.data.materials.get("Glass") or _trees.material(ctx, "Clear Glass", "#DDE6E6", 0.05)
    black = _trees.material(ctx, "Black Pinboard", "#14171C", 0.9)
    plaster = ctx["mats"]["Lime White"]
    steel = ctx["mats"]["Charcoal Steel"]
    W, Wd, Tr, Gl, Bk, Pl, St = (bmesh.new() for _ in range(7))
    Y = lambda z: -z

    # Cabinet parapet on the void's west edge; fronts face the passage (-x)
    c = CAB
    xa, xb = VOID_W - c["depth"], VOID_W
    _box(W, xa, xb, Y(c["z1"]), Y(c["z0"]), 0.03, c["h"] - 0.03)
    _box(Wd, xa - 0.02, xb + 0.01, Y(c["z1"]) - 0.01, Y(c["z0"]) + 0.01, c["h"] - 0.03, c["h"])
    n = 8
    step = (c["z1"] - c["z0"]) / n
    for i in range(n):
        za, zb = c["z0"] + i * step, c["z0"] + (i + 1) * step
        _box(Tr, xa - 0.004, xa, Y(zb - 0.004), Y(za + 0.004), 0.04, c["h"] - 0.04)    # teak-edged door frame
        if i in (2, 3):                                                                 # drawers
            for zz in (0.14, 0.24):
                _box(W, xa - 0.006, xa - 0.004, Y(zb - 0.01), Y(za + 0.01), zz - 0.002, zz + 0.002)
        else:
            _box(Gl, xa - 0.006, xa - 0.004, Y(zb - 0.02), Y(za + 0.02), 0.07, c["h"] - 0.07)
    u0, u1 = UPSTAND
    _box(Pl, xa, xb, Y(u1), Y(u0), 0.0, c["h"])

    # Study nook desk along the void-side wall, drawer unit, pier + pinboard
    d = DESK
    yw = Y(d["z_wall"])                      # wall face; the nook is y > yw
    _box(Wd, d["x0"], d["x1"], yw, yw + d["depth"], d["h"] - 0.02, d["h"])
    _box(W, d["x1"] - 0.2, d["x1"], yw, yw + d["depth"] - 0.01, 0.02, d["h"] - 0.02)
    for zz in (0.09, 0.16, 0.23):
        _box(Tr, d["x1"] - 0.2, d["x1"], yw + d["depth"] - 0.012, yw + d["depth"] - 0.008, zz - 0.002, zz + 0.002)
    px = d["x0"] - 0.0
    _box(Pl, px - 0.12, px, yw, yw + d["depth"] + 0.04, 0.0, 1.3)
    _box(Bk, px - 0.11, px - 0.01, yw + d["depth"] + 0.04, yw + d["depth"] + 0.05, 0.4, 0.98)
    _box(Tr, d["x0"], d["x1"], yw, yw + 0.004, 0.0, 0.035)                              # skirting

    # Guard rail round the stairwell's open edges
    w = WELL
    h = 0.4
    for (a, b) in (((w["x"], w["z_mid"]), (w["x"], w["z1"])), ((w["x"], w["z_mid"]), (w["x_end"] - 0.25, w["z_mid"]))):
        A = Vector((a[0], Y(a[1]), 0.0))
        B = Vector((b[0], Y(b[1]), 0.0))
        _rod(St, A + Vector((0, 0, h)), B + Vector((0, 0, h)), 0.01)
        for k in (1, 2, 3, 4):
            _rod(St, A + Vector((0, 0, h * k / 5)), B + Vector((0, 0, h * k / 5)), 0.003)
        L = (B - A).length
        m = max(1, round(L / 0.3))
        for i in range(m + 1):
            P = A.lerp(B, i / m)
            _rod(St, P, P + Vector((0, 0, h)), 0.007)

    for bm, nm, m in ((W, "white", white), (Wd, "wood", wood), (Tr, "teakEdge", trim), (Gl, "glass", glass),
                      (Bk, "pinboard", black), (Pl, "plaster", plaster), (St, "guardRail", steel)):
        _mesh("second.Passage.%s" % nm, bm, coll, empty, m)
    return []
