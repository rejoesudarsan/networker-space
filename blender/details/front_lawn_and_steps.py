"""The front lawn outside Living 1 (photo p21): the existing FrontLawn finish
(ground frame x -0.2..1.2, z 3.3..4.95) gets a grass material with patchy
variation, the low plaster wall along its east side topped by a planter bed of
pink hydrangea, and the rusted corten planter box along its west edge.

p36's garden steps (stone treads on brick risers between a plastered wall and
an ochre planter of pots) are not placed: their position on the plans is
unresolved, so they are a [?] item in DETAILS.md for the user."""
import random

import bmesh
import bpy
from mathutils import Matrix

from . import _trees

LAWN = (-0.2, 3.3, 1.2, 4.95)
EAST_WALL = dict(x=1.2, t=0.08, h=0.26, bed=0.16)     # wall on the east edge, bed on top of it
CORTEN = dict(x0=-0.2, x1=-0.08, z0=3.4, z1=4.3, h=0.16)


def build(ctx):
    h = ctx["helpers"]
    coll, empty = ctx["colls"]["ground"], ctx["empties"]["ground"]
    plaster = ctx["mats"]["Lime White"]
    soil = _trees.material(ctx, "Soil", "#4A3426", 0.95)
    leaf = _trees.material(ctx, "Shrub", "#3F6B2F", 0.8)
    pink = _trees.material(ctx, "Hydrangea", "#D99AC5", 0.6)
    corten = _trees.material(ctx, "Corten", "#9A4E22", 0.85)
    x0, z0, x1, z1 = LAWN
    rnd = random.Random(21)

    # East wall with a planter bed on top, as in p21's right side
    w = EAST_WALL
    h["add_box"]("ground.LawnWall.E", w["x"], w["x"] + w["t"], -z1, -z0, 0.0, w["h"], coll, empty, plaster)
    h["add_box"]("ground.LawnBed.E", w["x"] + w["t"], w["x"] + w["t"] + w["bed"], -z1, -z0, 0.0, w["h"] - 0.03,
                 coll, empty, plaster)
    h["add_box"]("ground.LawnBed.E.soil", w["x"] + w["t"], w["x"] + w["t"] + w["bed"], -z1, -z0,
                 w["h"] - 0.03, w["h"] - 0.02, coll, empty, soil)
    shrubs, flowers = bmesh.new(), bmesh.new()
    z = z0 + 0.08
    while z < z1 - 0.05:
        cx = w["x"] + w["t"] + w["bed"] / 2
        q = rnd.uniform(0.08, 0.12)
        g = bmesh.ops.create_icosphere(shrubs, subdivisions=1, radius=1.0)
        bmesh.ops.transform(shrubs, matrix=Matrix.Translation((cx, -z, w["h"] + q * 0.6))
                            @ Matrix.Diagonal((q, q * 1.2, q * 0.8, 1)), verts=g["verts"])
        for k in range(rnd.randint(1, 3)):
            f = rnd.uniform(0.025, 0.035)
            g = bmesh.ops.create_icosphere(flowers, subdivisions=1, radius=f)
            bmesh.ops.translate(flowers, verts=g["verts"],
                                vec=(cx + rnd.uniform(-q, q) * 0.7, -z + rnd.uniform(-q, q) * 0.7, w["h"] + q * 1.2))
        z += rnd.uniform(0.12, 0.18)

    # Corten planter box along the west edge with low planting
    cbox = CORTEN
    h["add_box"]("ground.CortenPlanter", cbox["x0"], cbox["x1"], -cbox["z1"], -cbox["z0"], 0.0, cbox["h"],
                 coll, empty, corten)
    z = cbox["z0"] + 0.06
    while z < cbox["z1"] - 0.04:
        q = rnd.uniform(0.04, 0.06)
        g = bmesh.ops.create_icosphere(shrubs, subdivisions=1, radius=1.0)
        bmesh.ops.transform(shrubs, matrix=Matrix.Translation(((cbox["x0"] + cbox["x1"]) / 2, -z, cbox["h"] + q * 0.5))
                            @ Matrix.Diagonal((q, q, q * 0.9, 1)), verts=g["verts"])
        z += rnd.uniform(0.08, 0.12)

    for bm, nm, mat in ((shrubs, "ground.LawnShrubs", leaf), (flowers, "ground.LawnFlowers", pink)):
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mat)
        ob = bpy.data.objects.new(nm, me)
        coll.objects.link(ob)
        ob.parent = empty
        ob.matrix_parent_inverse = Matrix.Identity(4)
    return []


def _grass(h):
    grass = bpy.data.materials.get("Lawn")
    if grass is not None:
        return grass
    grass, nt, bsdf = h["new_material"]("Lawn")
    bsdf.inputs["Roughness"].default_value = 0.95
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 6.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[1].position = 0.35, 0.7
    cr.elements[0].color = (0.10, 0.20, 0.035, 1)     # deep green
    cr.elements[1].color = (0.24, 0.36, 0.07, 1)      # sunlit, slightly yellow
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    grass.diffuse_color = (0.16, 0.28, 0.05, 1)
    return grass


def finish(ctx):
    """The FrontLawn finish is made after the detail modules run, so the grass
    material goes on here."""
    lawn = bpy.data.objects.get("ground.FrontLawn")
    if lawn is None:
        ctx["helpers"]["warn"]("front_lawn: no ground.FrontLawn finish to re-grass")
        return
    lawn.data.materials.clear()
    lawn.data.materials.append(_grass(ctx["helpers"]))
