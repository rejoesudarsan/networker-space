"""Three woven twig nest pendants in the Double HT Court (photos p11, p1):
spheres about 60 cm across, two hanging high and close together and one
lower, toward the court's north-west, on long cords from the roof slab over
the void (above the second floor). Rough twig surfaces: jittered spheres with
short twig spikes. First frame, Three.js units."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _trees

NESTS = [  # x, z, centre height above the first floor, radius
    (1.18, 0.52, 1.45, 0.11),
    (1.40, 0.42, 1.55, 0.10),
    (1.28, 0.78, 1.12, 0.125),
]


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
    c = ctx["constants"]
    coll, empty = ctx["colls"]["first"], ctx["empties"]["first"]
    twig = _trees.material(ctx, "Woven Twig", "#5C4632", 0.95)
    cord = _trees.material(ctx, "Cord", "#7A5E3E", 0.9)
    # Roof underside above the void, in the first frame
    ceiling = (c["FLOORS"]["second"]["level"] - c["FLOORS"]["first"]["level"]) + c["STOREY"] - c["SLAB_T"]
    rnd = random.Random(12)
    nb, cb = bmesh.new(), bmesh.new()
    for (x, z, hgt, r) in NESTS:
        centre = Vector((x, -z, hgt))
        g = bmesh.ops.create_icosphere(nb, subdivisions=3, radius=r)
        for v in g["verts"]:
            v.co = v.co * rnd.uniform(0.85, 1.1) + centre
        for k in range(70):                       # twig spikes poking out of the weave
            d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))).normalized()
            a = centre + d * r * 0.9
            b = centre + d * r * rnd.uniform(1.0, 1.12) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * r * 0.15
            seg = b - a
            t = bmesh.ops.create_cone(nb, cap_ends=False, segments=3, radius1=0.004, radius2=0.002, depth=seg.length)
            rot = Vector((0, 0, 1)).rotation_difference(seg.normalized()).to_matrix().to_4x4()
            bmesh.ops.transform(nb, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=t["verts"])
        top = centre + Vector((0, 0, r))
        t = bmesh.ops.create_cone(cb, cap_ends=True, segments=4, radius1=0.003, radius2=0.003, depth=ceiling - top.z)
        bmesh.ops.translate(cb, verts=t["verts"], vec=(x, -z, (ceiling + top.z) / 2))
    _mesh("first.Court2.nests", nb, coll, empty, twig)
    _mesh("first.Court2.nestCords", cb, coll, empty, cord)
    ctx["helpers"]["info"]("nest pendants: cords to %.2f units above the first floor" % ceiling)
    return []
