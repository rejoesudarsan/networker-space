"""Kitchen 2 (photo p26; walls measured top-down: x -1.66..-0.01,
z -2.82..-1.39, door in the west wall at z -2.58..-2.26). p26 looks south:
the east run with the hob, dark lower fronts, light-wood wall cabinets with
frosted-glass doors and a steel chimney hood; on the south wall a light-wood
base unit with drawers under a glass display cabinet, then tall pantry units
to the west; along the west wall south of the door, the black granite run
with the double steel sink. Black floor tiles. First frame, Three.js units."""
import bmesh
import bpy
from mathutils import Matrix

from . import _trees

ROOM = (-1.66, -2.82, -0.01, -1.39)
D, H, TOP_T = 0.24, 0.355, 0.016


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
    light = _trees.material(ctx, "Light Wood", "#CDB896", 0.5)
    darkw = _trees.material(ctx, "Wenge", "#3B2E28", 0.5)
    granite = _trees.material(ctx, "Black Granite", "#141414", 0.15)
    frost = _trees.material(ctx, "Frosted Glass", "#C9D2CF", 0.3)
    steel = _trees.material(ctx, "Brushed Steel", "#9EA2A4", 0.3)
    joint = _trees.material(ctx, "Cabinet Joint", "#6E5F66", 0.6)
    tile = _trees.material(ctx, "Black Floor Tile", "#232425", 0.35)
    x0, z0, x1, z1 = ROOM
    Y = lambda z: -z
    L, Dk, G, Fr, St, J, Fl = (bmesh.new() for _ in range(7))
    _box(Fl, x0, x1, Y(z1), Y(z0), 0.0, 0.012)

    # East run along x1: z -2.76..-1.39+D (meets the south run)
    ea, eb = -2.76, z1 - D
    _box(Dk, x1 - D, x1, Y(eb), Y(ea), 0.03, H - TOP_T)
    _box(G, x1 - D - 0.015, x1, Y(z1), Y(ea), H - TOP_T, H)
    for zz in (-2.5, -2.2, -1.9):
        _box(J, x1 - D - 0.003, x1 - D, Y(zz + 0.002), Y(zz - 0.002), 0.04, H - 0.03)
    # Hob and hood
    hz = -2.45
    for dz in (-0.06, 0.06):
        for dx in (-0.05, 0.05):
            g = bmesh.ops.create_cone(St, cap_ends=True, segments=10, radius1=0.022, radius2=0.018, depth=0.01)
            bmesh.ops.translate(St, verts=g["verts"], vec=(x1 - D / 2 + dx, Y(hz + dz), H + 0.005))
    _box(St, x1 - 0.22, x1, Y(hz + 0.16), Y(hz - 0.16), 0.74, 0.79)
    _box(St, x1 - 0.1, x1, Y(hz + 0.05), Y(hz - 0.05), 0.79, 1.15)
    # Wall cabinets, east, beside the hood, with frosted doors
    for (za, zb) in ((-2.25, -1.75),):
        _box(L, x1 - 0.15, x1, Y(zb), Y(za), 0.62, 0.92)
        _box(Fr, x1 - 0.152, x1 - 0.148, Y(zb - 0.03), Y(za + 0.03), 0.65, 0.89)

    # South run: base with drawers + display cabinet (east part), tall units (west part)
    ya, yb = Y(z1), Y(z1) + D                     # room side of the south wall is y > -z1
    _box(L, -0.6, x1 - D, ya, yb, 0.03, H - TOP_T)
    _box(G, -0.6, x1, ya, yb + 0.015, H - TOP_T, H)
    for zz in (0.12, 0.2, 0.28):
        _box(J, -0.6, x1 - D, yb, yb + 0.003, zz - 0.002, zz + 0.002)
    _box(Dk, -0.6, -0.28, ya, ya + 0.15, 0.55, 0.92)
    _box(Fr, -0.58, -0.3, ya + 0.15, ya + 0.153, 0.58, 0.89)
    _box(L, -1.42, -0.62, ya, yb + 0.03, 0.0, 0.95)                # tall pantry units
    for xx in (-1.22, -1.02, -0.82):
        _box(J, xx - 0.002, xx + 0.002, yb + 0.03, yb + 0.033, 0.02, 0.93)

    # West run: granite counter with the double sink, south of the door
    wa, wb = -2.2, z1
    _box(L, x0, x0 + D, Y(wb), Y(wa), 0.03, H - TOP_T)
    _box(G, x0, x0 + D + 0.015, Y(wb), Y(wa), H - TOP_T, H)
    for zc in (-1.98, -1.8):
        _box(St, x0 + 0.04, x0 + D - 0.04, Y(zc + 0.08), Y(zc - 0.08), H - 0.05, H + 0.002)

    for bm, nm, m in ((L, "lightWood", light), (Dk, "wenge", darkw), (G, "granite", granite),
                      (Fr, "frosted", frost), (St, "steel", steel), (J, "joints", joint), (Fl, "floor", tile)):
        _mesh("first.Kitchen2.%s" % nm, bm, coll, empty, m)
    return []
