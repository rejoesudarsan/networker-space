"""Kitchen 1, the long galley (photo p13; ground plan 9'4" x 18'8").
p13 looks north: the west run on the exterior wall with the hob under a
concrete hood and the window, an L in the north-east corner with wall
cabinets above, the door to the back store in the north wall. The plan also
draws a return along the south wall (behind the camera in p13), the sink at
the north end of the west run and the hob mid-run. Black granite tops,
mauve laminate fronts, black floor tiles. Ground frame, Three.js units."""
import bmesh
import bpy
from mathutils import Matrix

from . import _trees

ROOM = (-2.93, -4.55, -1.82, -2.62)       # x0, z0, x1, z1
D = 0.24                                   # counter depth (58 cm)
H = 0.355                                  # counter top (86 cm)
TOP_T = 0.016
RUNS = [  # x0, x1, z0, z1, which side the fronts face: "e" (+x), "w" (-x), "s" (+z), "n" (-z)
    (-2.93, -2.93 + D, -4.55, -2.85, "e"),           # west run
    (-2.93 + D, -1.82, -2.85 - 0.0, -2.62, "n"),     # south return (plan)
    (-1.82 - D, -1.82, -4.55 + D, -3.67, "w"),       # east run, north end
    (-2.35, -1.82, -4.55, -4.55 + D, "s"),           # north run, east part
]
HOB_Z, SINK_Z = -3.25, -4.05
WALL_CAB = [(-1.82 - 0.18, -1.82, -4.55 + 0.18, -3.67), (-2.35, -1.82, -4.55, -4.55 + 0.18)]


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


def _front_joints(bm, x0, x1, y0, y1, face, z0, z1, step=0.25):
    """Vertical door joints and a handle rail on the run's front face."""
    if face in ("e", "w"):
        xf = x1 if face == "e" else x0
        o = 0.003 if face == "e" else -0.003
        a, b = min(y0, y1), max(y0, y1)
        y = a + step
        while y < b - 0.05:
            _box(bm, min(xf, xf + o), max(xf, xf + o), y - 0.002, y + 0.002, z0, z1)
            y += step
        _box(bm, min(xf, xf + 2 * o), max(xf, xf + 2 * o), a + 0.02, b - 0.02, z1 - 0.03, z1 - 0.022)
    else:
        yf = y0 if face == "s" else y1
        o = -0.003 if face == "s" else 0.003
        x = x0 + step
        while x < x1 - 0.05:
            _box(bm, x - 0.002, x + 0.002, min(yf, yf + o), max(yf, yf + o), z0, z1)
            x += step
        _box(bm, x0 + 0.02, x1 - 0.02, min(yf, yf + 2 * o), max(yf, yf + 2 * o), z1 - 0.03, z1 - 0.022)


def build(ctx):
    c = ctx["constants"]
    coll, empty = ctx["colls"]["ground"], ctx["empties"]["ground"]
    granite = _trees.material(ctx, "Black Granite", "#141414", 0.15)
    mauve = _trees.material(ctx, "Mauve Laminate", "#B9A3AC", 0.45)
    joint = _trees.material(ctx, "Cabinet Joint", "#6E5F66", 0.6)
    tile = _trees.material(ctx, "Black Floor Tile", "#232425", 0.35)
    tjoint = _trees.material(ctx, "Tile Joint", "#3A3B3C", 0.8)
    concrete = _trees.material(ctx, "Concrete", "#A8A297", 0.85)
    steel = ctx["mats"]["Charcoal Steel"]
    wall_h = c["WALL_H"]

    # Floor tiles
    x0, z0, x1, z1 = ROOM
    fl, fj = bmesh.new(), bmesh.new()
    _box(fl, x0, x1, -z1, -z0, 0.0, 0.012)
    x = x0 + 0.25
    while x < x1:
        _box(fj, x - 0.002, x + 0.002, -z1, -z0, 0.012, 0.0135)
        x += 0.25
    z = z0 + 0.25
    while z < z1:
        _box(fj, x0, x1, -z - 0.002, -z + 0.002, 0.012, 0.0135)
        z += 0.25
    _mesh("ground.Kitchen1.floor", fl, coll, empty, tile)
    _mesh("ground.Kitchen1.floorJoints", fj, coll, empty, tjoint)

    body, tops, joints, metal = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    for (a, b, za, zb, face) in RUNS:
        ya, yb = -zb, -za
        _box(body, a, b, ya, yb, 0.03, H - TOP_T)                      # cabinets above a kick
        _box(joints, a + 0.02, b - 0.02, ya + 0.02, yb - 0.02, 0.012, 0.03)
        ox = {"e": 0.015, "w": -0.015}.get(face, 0.0)
        oy = {"s": -0.015, "n": 0.015}.get(face, 0.0)
        _box(tops, min(a, a + ox), max(b, b + ox), min(ya, ya + oy), max(yb, yb + oy), H - TOP_T, H)
        _front_joints(joints, a, b, ya, yb, face, 0.04, H - TOP_T - 0.01)
    # Hob (two burner pairs) and sink on the west run
    xa, xb = RUNS[0][0], RUNS[0][1]
    for dz in (-0.07, 0.07):
        for dx in (-0.04, 0.04):
            g = bmesh.ops.create_cone(metal, cap_ends=True, segments=10, radius1=0.022, radius2=0.018, depth=0.01)
            bmesh.ops.translate(metal, verts=g["verts"], vec=((xa + xb) / 2 + dx, -(HOB_Z + dz), H + 0.005))
    _box(metal, xa + 0.04, xb - 0.04, -(SINK_Z + 0.12), -(SINK_Z - 0.12), H - 0.04, H + 0.002)
    # Concrete hood over the hob, up to the ceiling
    _box(body, xa, xa + 0.2, -(HOB_Z + 0.16), -(HOB_Z - 0.16), 0.74, wall_h)
    # Wall cabinets on the north-east L
    for (a, b, za, zb) in WALL_CAB:
        _box(body, a, b, -zb, -za, 0.62, 0.95)
    _mesh("ground.Kitchen1.cabinets", body, coll, empty, mauve)
    _mesh("ground.Kitchen1.granite", tops, coll, empty, granite)
    _mesh("ground.Kitchen1.joints", joints, coll, empty, joint)
    _mesh("ground.Kitchen1.hobSink", metal, coll, empty, steel)
    hood = bpy.data.objects.get("ground.Kitchen1.cabinets")
    # Give the hood its own concrete look: split it out
    bm = bmesh.new()
    _box(bm, xa - 0.001, xa + 0.201, -(HOB_Z + 0.161), -(HOB_Z - 0.161), 0.74, wall_h)
    _mesh("ground.Kitchen1.hood", bm, coll, empty, concrete)
    return []
