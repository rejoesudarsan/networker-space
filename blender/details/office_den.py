"""The basement office (photos p31, p10; basement plan OFFICE, label at
x 0.79, z 0.61, with the curved west wall and the glazing onto the
open-to-sky court on its south side). From p31: a desk ledge on the west wall
with a whiteboard above (the task chair went when the office became the
lounge, 5 Oct 2026), a low cubby shelf under
the south window, a split AC over it. From p10: a green pinboard in a teak
frame on the east wall, teak skirting. Basement frame, Three.js units."""
import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _trees

ROOM = (-0.57, -0.47, 2.0, 1.88)    # x0, z0, x1, z1, measured from a straight-down render of the walls


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
    teak = ctx["mats"]["Teak"]
    black = _trees.material(ctx, "Chair Black", "#1C1C1E", 0.6)
    white = _trees.material(ctx, "Whiteboard", "#F2F2EE", 0.2)
    cork = _trees.material(ctx, "Pinboard Green", "#7E8A2E", 0.9)
    ac = _trees.material(ctx, "AC White", "#ECECE8", 0.4)
    x0, z0, x1, z1 = ROOM
    wood, dark, light, green, acm = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()

    # Desk ledge on the west wall and whiteboard above it
    _box(wood, x0, x0 + 0.24, -0.95, -0.2, 0.29, 0.31)
    _box(wood, x0, x0 + 0.24, -0.95, -0.92, 0.0, 0.29)
    _box(light, x0, x0 + 0.008, -0.85, -0.3, 0.5, 0.78)
    _box(dark, x0, x0 + 0.01, -0.86, -0.29, 0.49, 0.5)
    # Cubby shelf under the south window
    sy = -(z1 - 0.12)
    _box(wood, 1.1, 1.95, sy, -z1 + 0.0, 0.0, 0.2)
    for i in range(1, 5):
        xx = 1.1 + i * 0.17
        _box(wood, xx - 0.006, xx + 0.006, sy - 0.11, sy, 0.0, 0.2)
    # Split AC above the window
    _box(acm, 1.3, 1.75, -(z1 - 0.06), -(z1 - 0.0), 1.05, 1.15)
    # Pinboard on the east wall
    _box(wood, x1 - 0.012, x1, -0.55, 0.15, 0.5, 0.82)
    _box(green, x1 - 0.016, x1 - 0.012, -0.53, 0.13, 0.52, 0.8)
    # Teak skirting round the room
    for (a, b, ya, yb) in ((0.2, x1, -z0 - 0.006, -z0), (x1 - 0.006, x1, -z1, -z0)):
        _box(wood, a, b, ya, yb, 0.0, 0.035)
    _mesh("basement.Office.teak", wood, coll, empty, teak)
    _mesh("basement.Office.black", dark, coll, empty, black)
    _mesh("basement.Office.whiteboard", light, coll, empty, white)
    _mesh("basement.Office.pinboard", green, coll, empty, cork)
    _mesh("basement.Office.ac", acm, coll, empty, ac)
    return []
