"""The second-floor bath (photo p29; room measured top-down between the
Dress and the stair: x 1.0..2.0, z -2.36..-1.5, window in the north part of
the east wall). p29 looks east: the cream tub set into a turquoise
glass-block plinth with a dark slate deck along the south wall, the deck
running back to the window ledge; white square wall tiles above it; a glass
shower enclosure in the north-west corner with a steel handle; the WC
against the west wall; black slate floor. Second frame, Three.js units."""
import bmesh
import bpy
from mathutils import Matrix

from . import _trees

ROOM = (1.0, -2.36, 2.0, -1.535)   # z1 is the south wall's room face
PLINTH_H = 0.2


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
    coll, empty = ctx["colls"]["second"], ctx["empties"]["second"]
    slate = _trees.material(ctx, "Black Slate", "#2A2C2D", 0.7)
    glassblock = _trees.material(ctx, "Glass Block", "#2E9C91", 0.2)
    enamel = _trees.material(ctx, "Tub Enamel", "#E9E1C9", 0.25)
    tile = _trees.material(ctx, "White Tile", "#EEEEEA", 0.3)
    joint = _trees.material(ctx, "Tile Joint Grey", "#9A9B98", 0.6)
    glass = ctx["mats"].get("Glass") or bpy.data.materials.get("Glass") or _trees.material(ctx, "Clear Glass", "#DDE6E6", 0.05)
    steel = _trees.material(ctx, "Brushed Steel", "#9EA2A4", 0.3)
    x0, z0, x1, z1 = ROOM
    Y = lambda z: -z
    S, GB, E, T, J, GL, ST = (bmesh.new() for _ in range(7))
    _box(S, x0, x1, Y(z1), Y(z0), 0.0, 0.012)                                   # slate floor
    # Tub plinth along the south wall, deck back to the window
    tz0 = -1.82
    ta, tb, za, zb = 1.32, 1.95, -1.795, -1.565
    _box(GB, 1.25, x1, Y(z1), Y(tz0), 0.012, PLINTH_H - 0.1)                      # plinth below the basin
    for (a, b, c0, c1) in ((1.25, ta, tz0, z1), (tb, x1, tz0, z1), (ta, tb, tz0, za), (ta, tb, zb, z1)):
        _box(GB, a, b, Y(c1), Y(c0), PLINTH_H - 0.1, PLINTH_H)                     # and round it
    for (a, b, c0, c1) in ((1.23, ta, tz0 - 0.02, z1), (tb, x1, tz0 - 0.02, z1),
                           (ta, tb, tz0 - 0.02, za), (ta, tb, zb, z1)):
        _box(S, a, b, Y(c1), Y(c0), PLINTH_H, PLINTH_H + 0.02)                   # deck round the tub
    _box(GB, 1.78, x1, Y(tz0), Y(z0), 0.012, PLINTH_H)                          # ledge under the window
    _box(S, 1.76, x1, Y(tz0), Y(z0), PLINTH_H, PLINTH_H + 0.02)
    # Tub: an inset basin
    r = 0.03
    top = PLINTH_H + 0.035
    for (a, b, c0, c1) in ((ta, tb, za, za + r), (ta, tb, zb - r, zb), (ta, ta + r, za, zb), (tb - r, tb, za, zb)):
        _box(E, a, b, Y(c1), Y(c0), PLINTH_H - 0.1, top)                        # rim walls
    _box(E, ta + r, tb - r, Y(zb - r), Y(za + r), PLINTH_H - 0.1, PLINTH_H - 0.09)   # basin floor
    _box(ST, tb - 0.06, tb - 0.04, Y(zb), Y(zb - 0.02), top + 0.02, top + 0.05)       # spout
    # Tiles: south wall above the tub and the east wall, to 0.95
    yw = Y(z1) + 0.004                 # tile face just proud of the wall face
    _box(T, 1.25, x1, yw - 0.004, yw, PLINTH_H + 0.02, 0.95)
    z = PLINTH_H + 0.08
    while z < 0.95:
        _box(J, 1.25, x1, yw, yw + 0.002, z - 0.002, z + 0.002)
        z += 0.06
    x = 1.25 + 0.06
    while x < x1:
        _box(J, x - 0.002, x + 0.002, yw, yw + 0.002, PLINTH_H + 0.02, 0.95)
        x += 0.06
    # Shower enclosure, north-west corner
    sx, sz = 1.5, -2.08
    _box(GL, x0, sx, Y(sz) - 0.004, Y(sz) + 0.004, 0.012, 0.85)
    _box(GL, sx - 0.004, sx + 0.004, Y(sz), Y(z0), 0.012, 0.85)
    _box(ST, sx - 0.01, sx + 0.01, Y(sz) - 0.012, Y(sz) + 0.012, 0.012, 0.85)
    _box(ST, 1.42, 1.43, Y(sz) - 0.02, Y(sz) - 0.012, 0.3, 0.5)                # handle
    _box(ST, x0, x0 + 0.004, Y(sz + 0.02), Y(z0 + 0.02), 0.012, 0.86)          # (trim)
    # WC on the west wall, south of the shower
    wz = -1.93
    _box(T, x0, x0 + 0.08, Y(wz + 0.08), Y(wz - 0.08), 0.012, 0.32)            # cistern
    g = bmesh.ops.create_cone(T, cap_ends=True, segments=14, radius1=0.06, radius2=0.08, depth=0.16)
    bmesh.ops.translate(T, verts=g["verts"], vec=(x0 + 0.17, Y(wz), 0.09))
    for bm, nm, m in ((S, "slate", slate), (GB, "glassBlock", glassblock), (E, "tub", enamel), (T, "ceramic", tile),
                      (J, "joints", joint), (GL, "showerGlass", glass), (ST, "steel", steel)):
        _mesh("second.Bath.%s" % nm, bm, coll, empty, m)
    return []
