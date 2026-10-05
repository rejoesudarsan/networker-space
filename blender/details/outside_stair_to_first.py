"""The outside stair from the entrance court up to the first-floor porch
(photos p6, p4), and the frangipani at its foot.

Rises EAST, from a landing by the west wall to the first floor's ENTRANCE
porch: the ground plan draws its lower flight with the up arrow pointing
east and the first-floor plan its upper part ending at the porch, and in p6
the court lies to the right of someone climbing. (The site has it rising
west.) Thirteen kota risers as in p6, z -0.7..-0.2 ground frame. The open side toward the court carries a charcoal steel rail of
thin rods running with the slope.
Frangipani: in the court beside the stair's foot, on the court side as in p6
(the site's spot at x -2.55, z 1.6 put its crown over the west boundary
wall), height 1.7, white and yellow flowers."""
import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _trees

X_FOOT, X_HEAD = -2.9, -1.3        # bottom (west wall) .. top (first-floor porch), Three.js x
Z_OPEN, Z_WALL = -0.2, -0.7        # court side, wall side (Three.js z)
RISERS = 13
RAIL_H = 0.37
RODS = 5


def _rod(bm, a, b, r):
    d = b - a
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=r, radius2=r, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((a + b) / 2) @ rot, verts=g["verts"])


def build(ctx):
    h, c = ctx["helpers"], ctx["constants"]
    coll, empty = ctx["colls"]["ground"], ctx["empties"]["ground"]
    kota = _trees.material(ctx, "Kota", "#B9A68A", 0.6)
    steel = ctx["mats"]["Charcoal Steel"]
    storey = c["STOREY"]
    run = (X_HEAD - X_FOOT) / RISERS          # signed: + when rising east
    rise = storey / RISERS
    y_open, y_wall = -Z_OPEN, -Z_WALL          # Blender y
    y0, y1 = min(y_open, y_wall), max(y_open, y_wall)
    for i in range(RISERS):
        xa, xb = X_FOOT + i * run, X_FOOT + (i + 1) * run
        h["add_box"]("ground.OutsideStair.%02d" % i, min(xa, xb), max(xa, xb), y0, y1, 0.0, (i + 1) * rise,
                     coll, empty, kota)
    # Rails
    bm = bmesh.new()
    yo = y_open - 0.02
    foot = Vector((X_FOOT, yo, rise))
    head = Vector((X_HEAD, yo, storey))
    for k in range(RODS + 1):
        dz = RAIL_H * (k + 1) / (RODS + 1)
        _rod(bm, foot + Vector((0, 0, dz)), head + Vector((0, 0, dz)), 0.012 if k == RODS else 0.004)
    for i in range(0, RISERS + 1, 3):
        x = X_FOOT + i * run
        z = max(rise, i * rise)
        _rod(bm, Vector((x, yo, z)), Vector((x, yo, z + RAIL_H + 0.01)), 0.01)
    # p6's wall-mounted handrail is left out: the model has no wall on that side
    me = bpy.data.meshes.new("ground.OutsideStairRail")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(steel)
    ob = bpy.data.objects.new(me.name, me)
    coll.objects.link(ob)
    ob.parent = empty
    ob.matrix_parent_inverse = Matrix.Identity(4)

    # Frangipani at the foot
    tcoll = h["get_collection"]("Trees", ctx["site"])
    _trees.tree(ctx, "ground.Frangipani", (-2.4, 0.02, 0.0), tcoll, empty,
                height=1.7, spread=0.6, flowers=40, flatten=0.7, seed=6,
                tone="#4E6B35", tone_light="#6E8C45", blossom=("#F4F1E6", "#F2D46B"),
                crown_scale=1.15, flower_size=0.8)
    return []
