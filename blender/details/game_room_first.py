"""Club fit-out: the first-floor game room (Regular tier), in Bedroom 3.

The room (first frame, measured from section-cut top-down renders, 5 Oct
2026): main floor x -1.59..-0.02, z 2.23..3.76, with windows on the west wall
(z 3.16..3.73) and the street wall (x -0.86..0.0); an alcove to the west
x -2.07..-1.59, z 2.23..3.13 with a doorway at its north end; a vestibule to
the east x -0.02..0.73, z 2.23..2.70 entered from the north (x 0.07..0.47);
the toilet door on the east wall at z 2.73..3.05.

Layout: the "GAME TIME" chalkboard wall (pin 24) on the north wall; the
carrom table on a linen rug in the middle under a rattan pendant, four teak
stools round it; a board-game table for four by the street window under a
second pendant; a low linen sofa in the west alcove with a side table and a
plant; a games shelf in the vestibule. Three.js units."""
import math

from . import _furniture as F

E, W, N, S = math.pi / 2, -math.pi / 2, math.pi, 0.0      # facing
M = F.M


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
    k = F.Kit(ctx, "first", "first.GameRoomFirst")
    wall = lambda x, z, side: F.wall(ctx, "first", x, z, side)
    north = wall(-0.85, 2.9, "north")          # main room north wall
    east = wall(-0.5, 3.4, "east")             # main room east wall, below the toilet door
    south = wall(-1.2, 3.0, "south")           # solid part of the street wall
    alc_w = wall(-1.8, 2.8, "west")            # alcove west wall
    alc_s = wall(-1.85, 2.8, "south")          # alcove south wall
    vest_s = wall(0.35, 2.4, "south")          # vestibule partition (toilet side)

    # Chalkboard game wall on the north wall.
    F.chalk_wall(k, -0.83, north, S, w=2.1, h=1.45, y0=0.75)

    # Carrom in the middle, on a rug, four stools.
    cx, cz = -1.1, 2.98
    F.rug(k, cx - 0.4, cz - 0.38, cx + 0.4, cz + 0.38, mat=jute(ctx))
    F.carrom(k, cx, cz, 0.0)
    for dx, dz in ((-0.29, 0), (0.29, 0), (0, -0.29), (0, 0.29)):
        F.stool(k, cx + dx, cz + dz, h=0.5)
    F.pendant(k, cx, cz, wall_h_m, drop=1.0, r=0.24)

    # Board-game table for four by the street window.
    gx, gz = -0.38, south - 0.42
    F.game_table(k, gx, gz, 0.0, seed=11)
    F.chair(k, gx - 0.23, gz, E)
    F.chair(k, gx + 0.23, gz, W)
    F.chair(k, gx, gz - 0.23, S)
    F.chair(k, gx, gz + 0.23, N)
    F.pendant(k, gx, gz, wall_h_m, drop=1.05, r=0.2)

    # Low sofa in the west alcove, clear of its north doorway.
    sz = alc_s - 0.16 - 0.65 * M                   # side table at the south end, sofa north of it
    F.sofa(k, alc_w + 0.43 * M, sz, E, length=1.3, fabric="Linen")
    for dz in (-0.12, 0.12):
        k.at(alc_w + 0.27 * M, sz + dz, E)
        k.box("Cushion", 0, 0.2, 0.55, 0.42, 0.14, 0.36, rx=-0.18)
    F.side_table(k, alc_w + 0.1, alc_s - 0.085, h=0.45, r=0.18)
    F.plant(k, -1.5, south - 0.1, h=1.15, pot_r=0.18, seed=21)

    # Games shelf in the vestibule, against the partition, facing north.
    F.bookshelf(k, 0.33, vest_s - 0.16 * M, N, w=1.1, h=1.1, seed=8)
    F.plant(k, 0.64, vest_s - 0.09, h=0.7, pot_r=0.14, seed=22)

    objs = k.done()
    ctx["helpers"]["info"]("game_room_first: %d objects; walls n %.3f e %.3f s %.3f alcove w %.3f s %.3f vest s %.3f"
                           % (len(objs), north, east, south, alc_w, alc_s, vest_s))
    return []
