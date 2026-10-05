"""Club fit-out: the second-floor quiet rooms (Regular tier), in Bedrooms 3
and 4. Focused-work desks with brass lamps face walls and windows; olive
velvet armchairs on teak frames with side tables (pin 10); bookshelves, a
linen rug, plants. Second frame, Three.js units, measured from section-cut
top-down renders (5 Oct 2026).

Bedroom 3 (x 0.19..2.0, z 1.13..3.14; door on the west wall at z 2.07..2.39,
windows onto the court on the north wall x 0.98..1.88 and onto the street on
the south wall x 0.20..1.21): a desk under each window and one on the east
wall, a reading corner of two armchairs in the south-east, a bookcase on the
west wall north of the door, a rug in the middle.

Bedroom 4 (x -0.55..0.92, z -3.45..-1.51; door at the south-west x
-0.55..-0.18, window onto the terrace on the west wall z -2.93..-2.04, a
small one on the north wall x 0.6..0.92; opening at z -2.74..-2.42 into the
dress x 1.0..2.0, which is the only way to the bath): a desk at the terrace
window, one on the north wall, a bookcase beside it, an armchair corner in
the south-east. The dress becomes a phone booth: a felt-lined call desk on
its north wall, the path to the bath door left clear."""
import math

from . import _furniture as F

E, W, N, S = math.pi / 2, -math.pi / 2, math.pi, 0.0      # facing
M = F.M
DESK_D = 0.35 * M          # half the desk depth, in units


def desk_with_chair(k, x, z, wall_side, length=1.3, seed=0):
    """A desk against the wall on `wall_side`, lamp at the wall, a teak chair
    pulled up facing the wall. (x, z) is the wall-face point at the desk's
    middle."""
    rot = {"north": S, "east": W, "south": N, "west": E}[wall_side]
    face = {"north": N, "east": E, "south": S, "west": W}[wall_side]
    dx, dz = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}[wall_side]
    cx, cz = x + dx * (DESK_D + 0.004), z + dz * (DESK_D + 0.004)
    F.desk(k, cx, cz, rot, length=length, depth=0.7)
    F.chair(k, cx + dx * 0.2, cz + dz * 0.2, face)
    # A closed notebook and a cup on the desk.
    k.at(cx, cz, rot)
    k.box("Linen", -0.15, 0.05, 0.765, 0.3, 0.22, 0.02, rz=0.08 + 0.05 * seed)
    k.cyl("Ceramic White", 0.25, -0.12, 0.75, 0.84, 0.04, 0.045, 12)


def reading_corner(k, x_wall, z_wall, sx, sz, side=0.18):
    """Two velvet armchairs in a corner with a teak side table between them.
    (x_wall, z_wall) are the two wall faces; sx, sz = +-1 point from the
    corner into the room."""
    back = 0.5 * M
    # Chair A with its back to the x-wall, facing along -sx (into the room).
    a_rot = E if sx > 0 else W
    F.armchair(k, x_wall + sx * back, z_wall + sz * 0.5, a_rot)
    # Chair B with its back to the z-wall.
    b_rot = S if sz > 0 else N
    F.armchair(k, x_wall + sx * 0.5, z_wall + sz * back, b_rot)
    tx, tz = x_wall + sx * 0.13, z_wall + sz * 0.13
    F.side_table(k, tx, tz, h=0.5, r=side)
    table_lamp(k, tx, tz, 0.5)


def table_lamp(k, x, z, y0):
    """Ceramic-based lamp with a linen drum shade, standing on a table top y0 (m)."""
    k.at(x, z)
    k.cyl("Ceramic Dark", 0, 0, y0, y0 + 0.2, 0.06, 0.045, 12)
    k.cyl("Brass", 0, 0, y0 + 0.2, y0 + 0.28, 0.008, 0.008, 6)
    k.cyl("Linen", 0, 0, y0 + 0.24, y0 + 0.4, 0.13, 0.1, 16)
    k.cyl("Lamp Glow", 0, 0, y0 + 0.25, y0 + 0.27, 0.07, 0.07, 10)


def jute(ctx):
    """A warm jute rug material, made once (Kit.done picks it up by name)."""
    import bpy
    if "Jute Rug" not in bpy.data.materials:
        mat, nt, bsdf = ctx["helpers"]["new_material"]("Jute Rug")
        lin = F._hex("#A88A62")
        bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.95
        mat.diffuse_color = (*lin, 1.0)
    return "Jute Rug"


def build(ctx):
    wall_h_m = ctx["constants"]["WALL_H"] * ctx["constants"]["UNIT_M"]
    k = F.Kit(ctx, "second", "second.QuietRoomsSecond")
    wall = lambda x, z, side: F.wall(ctx, "second", x, z, side)
    info = ctx["helpers"]["info"]

    # ---- Bedroom 3
    n3 = wall(0.5, 2.0, "north")
    s3 = wall(1.6, 2.0, "south")
    e3 = wall(1.0, 1.6, "east")
    w3 = wall(1.0, 2.7, "west")           # the west wall is open at z 1.38..1.83 and 2.07..2.39
    desk_with_chair(k, 0.72, s3, "south", length=1.4, seed=1)        # street window
    desk_with_chair(k, 1.43, n3, "north", length=1.3, seed=2)        # court window
    desk_with_chair(k, e3, 2.12, "east", length=1.3, seed=3)
    reading_corner(k, e3, s3, -1, -1)
    F.bookshelf(k, w3 + 0.16 * M, 2.76, E, w=1.4, h=2.0, seed=31)    # south of the door
    F.rug(k, 0.62, 1.78, 1.42, 2.55, mat=jute(ctx))
    F.plant(k, w3 + 0.1, n3 + 0.1, h=1.1, pot_r=0.16, seed=33)
    F.pendant(k, 1.02, 2.16, wall_h_m, drop=0.9, r=0.26)

    # ---- Bedroom 4
    n4 = wall(-0.2, -2.5, "north")
    w4 = wall(-0.2, -3.2, "west")
    s4 = wall(0.3, -2.5, "south")
    e4 = wall(0.3, -2.0, "east")          # the bath's wall, south of the dress opening
    e4n = wall(0.3, -3.1, "east")         # the pier north of the opening
    desk_with_chair(k, w4, -2.48, "west", length=1.3, seed=4)        # terrace window
    desk_with_chair(k, 0.48, n4, "north", length=1.2, seed=5)
    F.bookshelf(k, -0.22, n4 + 0.16 * M, S, w=1.2, h=2.0, seed=41)
    reading_corner(k, e4, s4, -1, -1)
    F.rug(k, -0.1, -2.95, 0.58, -2.05, mat=jute(ctx))
    F.plant(k, e4n - 0.09, -2.9, h=0.9, pot_r=0.15, seed=42)
    F.pendant(k, 0.22, -2.5, wall_h_m, drop=0.9, r=0.24)

    # ---- The dress as a phone booth: felt-lined call desk on its north wall.
    nd = wall(1.5, -2.9, "north")
    ed = wall(1.5, -3.2, "east")
    F.wall_panel(k, 1.5, nd + 0.004, S, 2.1, 1.6, 0.6, "Felt Green", t=0.03)
    desk_with_chair(k, 1.5, nd + 0.012, "north", length=1.0, seed=6)
    F.plant(k, ed - 0.08, nd + 0.08, h=0.8, pot_r=0.13, seed=43)

    objs = k.done()
    info("quiet_rooms_second: %d objects; br3 n %.3f s %.3f e %.3f w %.3f; br4 n %.3f w %.3f s %.3f e %.3f e-pier %.3f; dress n %.3f e %.3f"
         % (len(objs), n3, s3, e3, w3, n4, w4, s4, e4, e4n, nd, ed))
    return []
