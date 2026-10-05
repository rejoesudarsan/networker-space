"""The basement parking (photo p2; site details.js PLAN.parking, PLAN.car):
grey concrete floor in saw-cut squares over the two parking rectangles, the
grey concrete-block facing on the west wall's inner face with its coursing,
a plain grey SUV nose to the ramp, and the aluminium ladder leaning on the
east side as in p2. Basement frame, Three.js units; basement floor = 0."""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _trees

PARKING = [(-2.2, -3.54, 0.1, -0.52), (-2.2, -0.52, -0.61, 1.0)]
WEST_FACE = -2.2
BLOCK_Z = (-3.5, 0.75)          # along the west wall
CAR = dict(x=-1.55, z=-2.45, L=1.76, W=0.74)
LADDER = dict(x=0.06, z=-3.05, h=0.95, lean=0.2)


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


def _rod(bm, a, b, r, segs=6):
    d = b - a
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=g["verts"])


def build(ctx):
    coll, empty = ctx["colls"]["basement"], ctx["empties"]["basement"]
    concrete = _trees.material(ctx, "Garage Concrete", "#9C9890", 0.8)
    cjoint = _trees.material(ctx, "Concrete Joint", "#8E897F", 0.9)
    block = _trees.material(ctx, "Concrete Block", "#8F8D86", 0.95)
    bjoint = _trees.material(ctx, "Block Joint", "#6F6D67", 0.95)
    paint = _trees.material(ctx, "Car Grey", "#4E5256", 0.3)
    tint = _trees.material(ctx, "Car Glass", "#1E2328", 0.1)
    tyre = _trees.material(ctx, "Tyre", "#1A1A1A", 0.8)
    alu = _trees.material(ctx, "Aluminium", "#C9CCCE", 0.35)

    # Floor and saw cuts
    fl, fj = bmesh.new(), bmesh.new()
    for (x0, z0, x1, z1) in PARKING:
        _box(fl, x0, x1, -z1, -z0, 0.0, 0.006)
        x = x0 + 0.62
        while x < x1 - 0.05:
            _box(fj, x - 0.004, x + 0.004, -z1, -z0, 0.006, 0.0075)
            x += 0.62
        z = z0 + 0.62
        while z < z1 - 0.05:
            _box(fj, x0, x1, -z - 0.004, -z + 0.004, 0.006, 0.0075)
            z += 0.62
    _mesh("basement.Parking.floor", fl, coll, empty, concrete)
    _mesh("basement.Parking.cuts", fj, coll, empty, cjoint)

    # Block facing with coursing (stretcher bond)
    bw, bj = bmesh.new(), bmesh.new()
    za, zb = BLOCK_Z
    xf = WEST_FACE
    _box(bw, xf, xf + 0.008, -zb, -za, 0.0, 1.29)
    k = 0
    y = 0.1
    while y < 1.28:
        _box(bj, xf + 0.008, xf + 0.012, -zb, -za, y - 0.004, y + 0.004)
        z = za + (0.1 if k % 2 else 0.2)
        while z < zb - 0.02:
            _box(bj, xf + 0.008, xf + 0.012, -z - 0.004, -z + 0.004, y - 0.096, y - 0.004)
            z += 0.2
        y += 0.1
        k += 1
    _mesh("basement.Parking.blockWall", bw, coll, empty, block)
    _mesh("basement.Parking.blockJoints", bj, coll, empty, bjoint)

    # The car: body, cabin, glass band, wheels. Nose toward the ramp (+z, i.e. -y).
    c = CAR
    cx, cy = c["x"], -c["z"]
    L, W = c["L"], c["W"]
    body, glass, wheels = bmesh.new(), bmesh.new(), bmesh.new()
    _box(body, cx - W / 2, cx + W / 2, cy - L / 2, cy + L / 2, 0.08, 0.31)                       # lower body
    _box(body, cx - W / 2 + 0.04, cx + W / 2 - 0.04, cy - L / 2 + 0.38, cy + L / 2 - 0.12, 0.31, 0.58)   # cabin
    _box(glass, cx - W / 2 + 0.035, cx + W / 2 - 0.035, cy - L / 2 + 0.42, cy + L / 2 - 0.16, 0.34, 0.53)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g = bmesh.ops.create_cone(wheels, cap_ends=True, segments=14, radius1=0.135, radius2=0.135, depth=0.09)
            m = Matrix.Translation((cx + sx * (W / 2 - 0.03), cy + sy * (L / 2 - 0.3), 0.135)) @ Matrix.Rotation(math.pi / 2, 4, "Y")
            bmesh.ops.transform(wheels, matrix=m, verts=g["verts"])
    _mesh("basement.Car.body", body, coll, empty, paint)
    _mesh("basement.Car.glass", glass, coll, empty, tint)
    _mesh("basement.Car.wheels", wheels, coll, empty, tyre)

    # Ladder leaning on the east side
    lad = bmesh.new()
    l = LADDER
    ly = -l["z"]
    foot_x, top_x = l["x"] - l["lean"], l["x"]
    for dy in (-0.09, 0.09):
        _rod(lad, Vector((foot_x, ly + dy, 0.0)), Vector((top_x, ly + dy, l["h"])), 0.012)
    n = 9
    for i in range(1, n):
        t = i / n
        x = foot_x + (top_x - foot_x) * t
        _rod(lad, Vector((x, ly - 0.09, l["h"] * t)), Vector((x, ly + 0.09, l["h"] * t)), 0.008)
    _mesh("basement.Ladder", lad, coll, empty, alu)
    return []
