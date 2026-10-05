"""The first-floor porch at the top of the outside stair (photo p4): the
ENTRANCE space of the first-floor plan, x -1.16..-0.30, z 0.18..1.64
(first frame). Washed-concrete floor in large panels, a perforated-mesh steel
rail along its west edge over the entrance court, the woven grass pendant
hanging by the door to Foyer 2, a coir mat at the door and potted plants in
the south-east corner. First-floor frame, Three.js units; slab top = 0."""
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _trees

PORCH = (-1.16, 0.18, -0.30, 1.64)    # x0, z0, x1, z1
TOP = 0.012
RAIL = dict(x=-1.16, z0=0.66, z1=1.64, h=0.4)
PENDANT = dict(x=-0.52, z=0.86, length=0.36, r_top=0.035, r_bottom=0.085)
MAT = dict(x=-0.40, z=0.98, dx=0.12, dz=0.24)
PLANTS = [(-0.42, 1.5), (-0.55, 1.55)]


def _obj(name, bm, coll, empty, mat):
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
    h, c = ctx["helpers"], ctx["constants"]
    coll, empty = ctx["colls"]["first"], ctx["empties"]["first"]
    concrete = _trees.material(ctx, "Washed Concrete", "#A49C8E", 0.9)
    joint = _trees.material(ctx, "Concrete Joint", "#8E897F", 0.9)
    steel = ctx["mats"]["Charcoal Steel"]
    mesh_m = _trees.material(ctx, "Steel Mesh", "#55595B", 0.6)
    grass = _trees.material(ctx, "Dry Grass", "#C9A96A", 0.9)
    coir = _trees.material(ctx, "Coir", "#7A5434", 0.95)
    terracotta = ctx["mats"]["Terracotta"]
    leaf = _trees.material(ctx, "Pot Plant", "#4F7A3A", 0.75)
    wall_h = c["WALL_H"]

    # Floor: large washed-concrete panels
    x0, z0, x1, z1 = PORCH
    h["add_box"]("first.Porch.floor", x0, x1, -z1, -z0, 0.0, TOP, coll, empty, concrete)
    z = z0 + 0.36
    while z < z1 - 0.05:
        h["add_box"]("first.Porch.joint", x0, x1, -z - 0.004, -z + 0.004, TOP, TOP + 0.002, coll, empty, joint)
        z += 0.36
    xm = (x0 + x1) / 2
    h["add_box"]("first.Porch.joint", xm - 0.004, xm + 0.004, -z1, -z0, TOP, TOP + 0.002, coll, empty, joint)

    # Mesh-panel rail along the west edge, over the court
    r = RAIL
    x = r["x"]
    ya, yb = -r["z1"], -r["z0"]
    h["add_box"]("first.PorchRail.top", x - 0.012, x + 0.012, ya, yb, r["h"] - 0.024, r["h"], coll, empty, steel)
    h["add_box"]("first.PorchRail.bottom", x - 0.01, x + 0.01, ya, yb, 0.03, 0.05, coll, empty, steel)
    for y in (ya, (ya + yb) / 2, yb):
        h["add_box"]("first.PorchRail.post", x - 0.012, x + 0.012, y - 0.012, y + 0.012, 0.0, r["h"],
                     coll, empty, steel)
    h["add_box"]("first.PorchRail.mesh", x - 0.003, x + 0.003, ya + 0.012, yb - 0.012, 0.05, r["h"] - 0.024,
                 coll, empty, mesh_m)

    # Woven grass pendant: a flaring fringe on a cord from the ceiling
    p = PENDANT
    cx, cy = p["x"], -p["z"]
    top = wall_h
    bm = bmesh.new()
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=p["r_bottom"], radius2=p["r_top"],
                              depth=p["length"])
    bmesh.ops.translate(bm, verts=g["verts"], vec=(cx, cy, top - 0.12 - p["length"] / 2))
    rnd = random.Random(4)
    for i in range(28):                      # loose strands at the hem
        a = i / 28 * 6.283
        rr = p["r_bottom"] * rnd.uniform(0.9, 1.05)
        z_hem = top - 0.12 - p["length"]
        g = bmesh.ops.create_cone(bm, cap_ends=False, segments=3, radius1=0.004, radius2=0.004,
                                  depth=rnd.uniform(0.04, 0.08))
        bmesh.ops.translate(bm, verts=g["verts"],
                            vec=(cx + rr * __import__("math").cos(a), cy + rr * __import__("math").sin(a), z_hem - 0.025))
    _obj("first.Porch.pendant", bm, coll, empty, grass)
    bm = bmesh.new()
    g = bmesh.ops.create_cone(bm, cap_ends=True, segments=4, radius1=0.003, radius2=0.003, depth=0.12)
    bmesh.ops.translate(bm, verts=g["verts"], vec=(cx, cy, top - 0.06))
    _obj("first.Porch.cord", bm, coll, empty, steel)

    # Coir mat at the door
    m = MAT
    h["add_box"]("first.Porch.mat", m["x"] - m["dx"] / 2, m["x"] + m["dx"] / 2,
                 -(m["z"] + m["dz"] / 2), -(m["z"] - m["dz"] / 2), TOP, TOP + 0.006, coll, empty, coir)

    # Potted plants, south-east corner
    pots, leaves = bmesh.new(), bmesh.new()
    for (px, pz) in PLANTS:
        g = bmesh.ops.create_cone(pots, cap_ends=True, segments=12, radius1=0.045, radius2=0.06, depth=0.12)
        bmesh.ops.translate(pots, verts=g["verts"], vec=(px, -pz, TOP + 0.06))
        for k in range(9):
            g = bmesh.ops.create_icosphere(leaves, subdivisions=1, radius=1.0)
            q = rnd.uniform(0.05, 0.08)
            mm = Matrix.Translation((px + rnd.uniform(-0.09, 0.09), -pz + rnd.uniform(-0.09, 0.09),
                                     TOP + 0.16 + rnd.uniform(0, 0.2))) @ Matrix.Diagonal((q, q, q * 0.8, 1))
            bmesh.ops.transform(leaves, matrix=mm, verts=g["verts"])
    _obj("first.Porch.pots", pots, coll, empty, terracotta)
    _obj("first.Porch.plants", leaves, coll, empty, leaf)
    return []


# The open court over the ground-floor entrance court: the first-floor plan
# draws it open (leaf pattern, the outside stair inside it) and p24 / p6 show
# sky over the bench, but the model's first slab ran solid across it.
COURT_VOID = (-2.88, 0.12, -1.16, 1.64)   # first frame x0, z0, x1, z1


def finish(ctx):
    slab = bpy.data.objects.get("first.slab")
    if slab is None:
        ctx["helpers"]["warn"]("first_floor_porch: no first.slab to open")
        return
    x0, z0, x1, z1 = COURT_VOID
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new("_court_cutter")
    bm.to_mesh(me)
    bm.free()
    cutter = bpy.data.objects.new("_court_cutter", me)
    ctx["scene"].collection.objects.link(cutter)
    cutter.parent = slab.parent
    cutter.matrix_parent_inverse = Matrix.Identity(4)
    cutter.location = ((x0 + x1) / 2, -(z0 + z1) / 2, 0.0)
    cutter.scale = (x1 - x0, z1 - z0, 2.0)
    mod = slab.modifiers.new("court_void", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    try:
        mod.solver = "EXACT"
    except Exception:
        pass
    dg = ctx["scene"].view_layers[0].depsgraph if hasattr(ctx["scene"].view_layers[0], "depsgraph") else bpy.context.evaluated_depsgraph_get()
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(slab.evaluated_get(dg))
    slab.modifiers.remove(mod)
    old = slab.data
    slab.data = new_me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cutter, do_unlink=True)
    ctx["helpers"]["info"]("first_floor_porch: opened the court over the entrance court in first.slab")
