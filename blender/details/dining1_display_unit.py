"""The teak display unit (photo p28), in the wide opening between Family 1
and Dining 1 where the ground plan draws it (x -0.12..0.5, z about -2.0):
a low sideboard of panelled teak doors with glass-fronted ends, a tall teak
panel at its east end carrying glass shelves into the opening, and a teak
frame round the opening. p28 is taken from Family 1 toward its north-west
corner (its double glazed doors to the west garden on the left), so the unit
faces south into Family 1. Ground frame, Three.js units; slab top = 0."""
import bmesh
import bpy
from mathutils import Matrix

from . import _trees

UNIT = dict(x0=-0.55, x1=0.25, z_back=-2.07, depth=0.17, h=0.31)
PANEL = dict(x0=0.25, x1=0.4)
OPENING = dict(x0=-0.62, x1=0.4, head=0.92)


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
    c = ctx["constants"]
    coll, empty = ctx["colls"]["ground"], ctx["empties"]["ground"]
    teak = ctx["mats"]["Teak"]
    dark = _trees.material(ctx, "Teak Seam", "#3A2214", 0.6)
    glass = ctx["mats"].get("Glass") or bpy.data.materials.get("Glass")
    shelf_glass = _trees.material(ctx, "Shelf Glass", "#CFE0DC", 0.1)
    wall_h = c["WALL_H"]
    u = UNIT
    yb = -u["z_back"]                  # back (north) face, Blender y
    yf = yb - u["depth"]               # front face, toward Family 1 (-y is south... z grows south)
    # Blender y = -z: Family 1 is south of the wall (larger z), i.e. smaller y
    body, seams, panes = bmesh.new(), bmesh.new(), bmesh.new()
    _box(body, u["x0"], u["x1"], yf, yb, 0.02, u["h"])             # carcass on a plinth
    _box(body, u["x0"] + 0.01, u["x1"] - 0.01, yf + 0.01, yb, 0.0, 0.02)
    _box(body, u["x0"] - 0.01, u["x1"] + 0.01, yf - 0.012, yb, u["h"], u["h"] + 0.018)   # top
    n = 6
    w = (u["x1"] - u["x0"]) / n
    for i in range(n):
        a, b = u["x0"] + i * w, u["x0"] + (i + 1) * w
        _box(seams, b - 0.002, b + 0.002, yf - 0.004, yf, 0.03, u["h"] - 0.01)      # door joints
        if i in (0, n - 1):                                                         # glass ends
            _box(panes, a + 0.018, b - 0.018, yf - 0.003, yf + 0.001, 0.05, u["h"] - 0.03)
        else:                                                                       # raised panels
            _box(body, a + 0.022, b - 0.022, yf - 0.008, yf, 0.06, u["h"] - 0.04)
        _box(seams, (a + b) / 2 + (0.03 if i % 2 else -0.03) - 0.002, (a + b) / 2 + (0.03 if i % 2 else -0.03) + 0.002,
             yf - 0.012, yf, u["h"] / 2 - 0.02, u["h"] / 2 + 0.02)                    # knobs
    # Tall panel at the east end, full height, and glass shelves into the opening
    p = PANEL
    _box(body, p["x0"], p["x1"], yf, yb, 0.0, wall_h)
    for zz in (0.5, 0.72, 0.94):
        _box(panes, p["x0"] - 0.3, p["x0"], yf + 0.02, yb - 0.02, zz, zz + 0.008)
    # Teak frame round the opening: head and west post
    o = OPENING
    _box(body, o["x0"], o["x1"], yf + 0.04, yb, o["head"], o["head"] + 0.05)
    _box(body, o["x0"], o["x0"] + 0.04, yf + 0.04, yb, 0.0, o["head"])
    # Plaster above the opening's head, up to the ceiling, as in p28 (the model has no wall there)
    ctx["helpers"]["add_box"]("ground.DisplayUnit.wallAbove", o["x0"], o["x1"], yb - 0.06, yb,
                              o["head"] + 0.05, wall_h, coll, empty, ctx["mats"]["Lime White"])
    _mesh("ground.DisplayUnit", body, coll, empty, teak)
    _mesh("ground.DisplayUnit.details", seams, coll, empty, dark)
    _mesh("ground.DisplayUnit.glass", panes, coll, empty, glass or shelf_glass)
    return []
