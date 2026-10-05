"""Shared low-poly tree builder for detail modules (gulmohar, frangipani,
olive, the Court 1 tree). Mirrors tree() in site/src/world/world.js: a trunk,
four branches, a crown of flattened blobs and optional blossoms. Geometry is
in model units (1 unit = 8 ft); parent the result to a frame scaled by UNIT_M.

Each tree is three mesh objects: <name>.wood, <name>.crown, <name>.blossom."""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector


def material(ctx, name, hex_colour, rough=0.8):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    mat, nt, bsdf = ctx["helpers"]["new_material"](name)
    h = hex_colour.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    try:
        mat.diffuse_color = (*lin, 1.0)
    except Exception:
        pass
    return mat


def _obj(name, bm, coll, parent, mat, loc):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    ob.parent = parent
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.location = loc
    me.materials.append(mat)
    return ob


def _cyl(bm, start, end, r0, r1, segs=7):
    d = end - start
    length = d.length
    geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r0, radius2=r1, depth=length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    m = Matrix.Translation((start + end) / 2) @ rot
    bmesh.ops.transform(bm, matrix=m, verts=geom["verts"])


def _blob(bm, centre, sx, sy, sz, subdiv=1):
    geom = bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    m = Matrix.Translation(centre) @ Matrix.Diagonal((sx, sy, sz, 1.0))
    bmesh.ops.transform(bm, matrix=m, verts=geom["verts"])


def tree(ctx, name, loc, coll, parent, height=2.4, spread=1.0, flowers=0,
         flatten=0.75, tone="#59634D", tone_light="#6F7D5A", blossom=("#E0531F", "#F08A3C"),
         seed=1, crown_scale=1.0, flower_size=1.0):
    """loc: Blender-space location (x, y, z) in the parent's units."""
    rnd = random.Random(seed)
    wood_m = material(ctx, "Bark", "#5A4636", 0.9)
    leaf_m = material(ctx, "Foliage " + tone, tone, 0.8)
    leaf2_m = material(ctx, "Foliage " + tone_light, tone_light, 0.8)

    # Trunk and branches
    bm = bmesh.new()
    _cyl(bm, Vector((0, 0, 0)), Vector((0, 0, height * 0.6)), 0.09 * spread, 0.05 * spread)
    for i in range(4):
        a = i * math.pi / 2 + 0.3
        s = Vector((0, 0, height * (0.36 + i * 0.035)))
        e = Vector((math.cos(a) * spread * crown_scale * 0.5, math.sin(a) * spread * crown_scale * 0.5, height * 0.72))
        _cyl(bm, s, e, 0.035 * spread, 0.02 * spread, 5)
    _obj(name + ".wood", bm, coll, parent, wood_m, loc)

    # Crown: two meshes so the light tone reads
    crown_z = height * 0.62
    cs = spread * crown_scale
    blobs = 5 + round(cs * 4)
    bm, bm2 = bmesh.new(), bmesh.new()
    for i in range(blobs):
        s = rnd.uniform(0.35, 0.6) * cs
        a = i / blobs * math.pi * 2 + rnd.uniform(-0.2, 0.2)
        r = 0 if i == 0 else rnd.uniform(0.25, 0.65) * cs
        c = Vector((math.cos(a) * r, math.sin(a) * r, crown_z + rnd.uniform(0, 0.45) * cs * flatten))
        _blob(bm if i % 3 else bm2, c, s, s, s * flatten)
    _obj(name + ".crown", bm, coll, parent, leaf_m, loc)
    if len(bm2.verts):
        _obj(name + ".crown2", bm2, coll, parent, leaf2_m, loc)
    else:
        bm2.free()

    # Blossoms sit on the crown's outer shell so they show
    if flowers:
        mats = [material(ctx, "Blossom " + h, h, 0.6) for h in blossom]
        groups = [bmesh.new() for _ in mats]
        for i in range(flowers):
            a = rnd.uniform(0, math.pi * 2)
            # Keep blossoms on the crown's shell: lower towards the rim
            u = rnd.uniform(0.3, 0.9)
            r = u * cs
            top = (0.85 - 0.6 * u) * cs * flatten
            c = Vector((math.cos(a) * r, math.sin(a) * r,
                        crown_z + rnd.uniform(0.15, 1.0) * top))
            k = rnd.uniform(0.05, 0.09) * spread * flower_size
            _blob(groups[0 if i % 4 else 1], c, k, k, k * 0.8, subdiv=0)
        for j, (g, m) in enumerate(zip(groups, mats)):
            _obj("%s.blossom%d" % (name, j), g, coll, parent, m, loc)
