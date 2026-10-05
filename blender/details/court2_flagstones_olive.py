"""The first-floor Double HT Court (photos p11, p14, p1): sandstone
flagstones in random sizes and mixed tones over the court (walls measured
top-down: x 0.81..2.51, z 0.18..1.69, first frame), a few small coloured
tiles set among them (p11), and the olive tree in a round concrete planter
toward the back, before the east wall's louvred doors. First frame, units."""
import random

import bmesh
import bpy
from mathutils import Matrix

from . import _trees

COURT = (0.81, 0.18, 2.51, 1.69)
OLIVE = (2.05, 0.55)
TOP = 0.012


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
    tones = [_trees.material(ctx, "Sandstone %d" % i, hx, 0.85)
             for i, hx in enumerate(("#B9A27E", "#A8916E", "#C4AE8A", "#8F877A"))]
    joint = _trees.material(ctx, "Flagstone Joint", "#A39478", 0.9)
    accent = _trees.material(ctx, "Accent Tile", "#B5532F", 0.5)
    concrete = _trees.material(ctx, "Concrete", "#A8A297", 0.85)
    soil = _trees.material(ctx, "Soil", "#4A3426", 0.95)
    x0, z0, x1, z1 = COURT
    rnd = random.Random(11)
    bms = [bmesh.new() for _ in tones]
    jb, ab = bmesh.new(), bmesh.new()
    _box(jb, x0, x1, -z1, -z0, 0.0, TOP - 0.002)            # grout bed
    # Rows of random-length stones with 1 cm gaps
    z = z0
    while z < z1 - 0.02:
        zh = min(rnd.choice((0.18, 0.24, 0.3)), z1 - z)
        x = x0
        while x < x1 - 0.02:
            w = min(rnd.uniform(0.18, 0.42), x1 - x)
            _box(bms[rnd.randrange(len(bms))], x + 0.005, x + w - 0.005, -(z + zh) + 0.005, -z - 0.005, TOP - 0.004, TOP)
            if rnd.random() < 0.05:
                c = (x + w / 2, -(z + zh / 2))
                _box(ab, c[0] - 0.035, c[0] + 0.035, c[1] - 0.035, c[1] + 0.035, TOP, TOP + 0.001)
            x += w
        z += zh
    for i, (b, m) in enumerate(zip(bms, tones)):
        _mesh("first.Court2.stones%d" % i, b, coll, empty, m)
    _mesh("first.Court2.grout", jb, coll, empty, joint)
    _mesh("first.Court2.accents", ab, coll, empty, accent)

    # Round concrete planter and the olive
    ox, oz = OLIVE
    pl = bmesh.new()
    g = bmesh.ops.create_cone(pl, cap_ends=True, segments=24, radius1=0.15, radius2=0.16, depth=0.1)
    bmesh.ops.translate(pl, verts=g["verts"], vec=(ox, -oz, TOP + 0.05))
    _mesh("first.Court2.planter", pl, coll, empty, concrete)
    sb = bmesh.new()
    g = bmesh.ops.create_cone(sb, cap_ends=True, segments=24, radius1=0.14, radius2=0.14, depth=0.01)
    bmesh.ops.translate(sb, verts=g["verts"], vec=(ox, -oz, TOP + 0.096))
    _mesh("first.Court2.planterSoil", sb, coll, empty, soil)
    _trees.tree(ctx, "first.Olive", (ox, -oz, TOP + 0.1), coll, empty,
                height=1.3, spread=0.3, flowers=0, flatten=1.1, seed=8,
                tone="#7A8A62", tone_light="#9AA680", crown_scale=0.9)
    return []
