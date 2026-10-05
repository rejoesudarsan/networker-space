"""Grey cladding strip: the full-height band of charcoal textured plaster on
the street facade, right of centre (photos p03, p19). Ground-frame x 0.3..1.4,
from the ground slab up to the roof parapet, on the first and second floors.
Built as one box per floor so it travels with the cutaway."""
import bpy

STRIP_X0, STRIP_X1 = 0.3, 1.4      # ground frame, Three.js x (east)
PROUD = 0.02                       # how far the band stands off the wall, units
MAT_NAME = "Charcoal Plaster"


def _material(ctx):
    h = ctx["helpers"]
    if MAT_NAME in bpy.data.materials:
        return bpy.data.materials[MAT_NAME]
    mat, nt, bsdf = h["new_material"](MAT_NAME)
    base = (0.18, 0.185, 0.18, 1.0)   # charcoal grey, linear
    bsdf.inputs["Base Color"].default_value = base
    bsdf.inputs["Roughness"].default_value = 0.95
    try:
        mat.diffuse_color = base
    except Exception:
        pass
    # Coarse textured plaster
    try:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.location = (-450, -250)
        noise.inputs["Scale"].default_value = 60.0
        noise.inputs["Detail"].default_value = 6.0
        bump = nt.nodes.new("ShaderNodeBump")
        bump.location = (-150, -250)
        bump.inputs["Strength"].default_value = 0.25
        bump.inputs["Distance"].default_value = 0.03
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    except Exception as e:
        h["warn"]("cladding bump: %s" % e)
    return mat


def build(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    floors, storey, slab_t = c["FLOORS"], c["STOREY"], c["SLAB_T"]
    mat = _material(ctx)
    ground = floors["ground"]
    # Street face (Three.js z) of each floor, in the ground frame
    for key, z0, z1 in (
        # first: from the ground slab top (one storey below) up to the second slab top
        ("first", -storey, storey),
        # second: up through the roof slab to the parapet top
        ("second", 0.0, storey + c["PARAPET_H"]),
    ):
        f = floors[key]
        ox, oz = f["offset"]
        x0, x1 = STRIP_X0 - ox, STRIP_X1 - ox
        face_z = f["depth"] / 2                       # floor-local Three.js z of the street face
        rect = h["three_rect_to_blender"]((x0, face_z, x1, face_z + PROUD))
        h["add_box"]("%s.CladdingStrip" % key, rect[0], rect[1], rect[2], rect[3],
                     z0, z1, ctx["colls"][key], ctx["empties"][key], mat)
    return []
