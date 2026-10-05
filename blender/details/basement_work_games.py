"""Club fit-out: the basement work room and games / meeting room (Regular
tier). Basement frame, Three.js units, measured from section-cut top-down
renders (5 Oct 2026).

Office (x -0.56..2.0, z -0.47..1.88; curved north-west corner, centre
(0.11, 0.14), r 0.67; door from Court 1 on the north wall x 0.35..0.99;
windows north x 1.02..1.88 onto the court tree, east z 0.80..1.41, west
z 1.10..1.43, south x 0.9..1.96 onto the open-to-sky court; a toilet in the
south-west notch x < 0.18, z > 1.54). office_den.py already holds the desk
ledge, task chair and whiteboard on the west wall, the cubby and AC at the
south window and the pinboard on the east wall. Added: a long shared teak
table under two pendants in the middle; three focused desks with lamps
(under the north window facing the tree, and two on the east wall, under the
pinboard and at the window); an olive velvet armchair corner by the west
window; a game table for four in the curved corner.

Lounge (user request, 5 Oct 2026): the desks and the long table gave way to
an RC car football table in the middle with four people playing round it,
an olive sofa on the east wall (someone watching) and a linen sofa under the
north window; the armchair corner and the corner game table stay, the desk
ledge is the snack ledge with two stools, the whiteboard the league table.

Studio / gallery (x 0.19..2.0, z -3.54..-2.13, opening onto Court 1 along
the south x 0.35..1.63, window east z -3.04..-2.67): the games and meeting
room, a long teak table for ten with a screen on the west wall and a
chalkboard games list beside the window. No table tennis: the room is only
3.4 m deep."""
import math

import bpy

from . import _entourage as _ent
from . import _furniture as F

E, W, N, S = math.pi / 2, -math.pi / 2, math.pi, 0.0      # facing
M = F.M
DESK_D = 0.35 * M


def jute(ctx):
    """A warm jute rug material, made once (Kit.done picks it up by name)."""
    if "Jute Rug" not in bpy.data.materials:
        mat, nt, bsdf = ctx["helpers"]["new_material"]("Jute Rug")
        lin = F._hex("#A88A62")
        bsdf.inputs["Base Color"].default_value = (*lin, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.95
        mat.diffuse_color = (*lin, 1.0)
    return "Jute Rug"


def desk_with_chair(k, x, z, wall_side, length=1.3, seed=0):
    """A desk against the wall on `wall_side` with (x, z) the wall-face point
    at its middle; lamp at the wall, a teak chair facing the wall."""
    rot = {"north": S, "east": W, "south": N, "west": E}[wall_side]
    face = {"north": N, "east": E, "south": S, "west": W}[wall_side]
    dx, dz = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}[wall_side]
    cx, cz = x + dx * (DESK_D + 0.004), z + dz * (DESK_D + 0.004)
    F.desk(k, cx, cz, rot, length=length, depth=0.7)
    F.chair(k, cx + dx * 0.2, cz + dz * 0.2, face)
    k.at(cx, cz, rot)
    k.box("Linen", -0.15, 0.05, 0.765, 0.3, 0.22, 0.02, rz=0.08 + 0.05 * seed)
    k.cyl("Ceramic White", 0.25, -0.12, 0.75, 0.84, 0.04, 0.045, 12)


def table_lamp(k, x, z, y0):
    k.at(x, z)
    k.cyl("Ceramic Dark", 0, 0, y0, y0 + 0.2, 0.06, 0.045, 12)
    k.cyl("Brass", 0, 0, y0 + 0.2, y0 + 0.28, 0.008, 0.008, 6)
    k.cyl("Linen", 0, 0, y0 + 0.24, y0 + 0.4, 0.13, 0.1, 16)
    k.cyl("Lamp Glow", 0, 0, y0 + 0.25, y0 + 0.27, 0.07, 0.07, 10)


def rc_football_table(ctx, k, x, z):
    """RC car football: a turf pitch on a teak table (2.4 x 1.4 m, top at
    0.77 m) with a low rim, chalk lines, a netted goal at each end, two
    teams of two little RC cars and the ball, long axis east-west."""
    from . import _trees
    _trees.material(ctx, "Turf", "#3F7A3A", 0.95)
    _trees.material(ctx, "Team Orange", "#E0702E", 0.45)
    _trees.material(ctx, "Team Blue", "#2F5FB8", 0.45)
    L, Wd, top = 2.4, 1.4, 0.77
    k.at(x, z)
    k.box("Teak", 0, 0, top - 0.045, L, Wd, 0.07)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.box("Black Steel", sx * (L / 2 - 0.1), sy * (Wd / 2 - 0.1), (top - 0.08) / 2, 0.05, 0.05, top - 0.08)
        k.box("Teak", sx * (L / 2 + 0.07), 0, top - 0.045, 0.14, 0.56, 0.07)    # goal ledges
    k.box("Turf", 0, 0, top - 0.005, L - 0.06, Wd - 0.06, 0.012)
    # Rim, open at the goal mouths.
    gw = 0.46
    for sy in (-1, 1):
        k.box("Teak", 0, sy * (Wd / 2 - 0.02), top + 0.035, L, 0.04, 0.07)
    for sx in (-1, 1):
        for sy in (-1, 1):
            seg = (Wd - gw) / 2
            k.box("Teak", sx * (L / 2 - 0.02), sy * (gw / 2 + seg / 2), top + 0.035, 0.04, seg, 0.07)
    # Chalk lines.
    ly = top + 0.0015
    k.box("Chalk", 0, 0, ly, 0.02, Wd - 0.14, 0.003)
    for sy in (-1, 1):
        k.box("Chalk", 0, sy * (Wd / 2 - 0.07), ly, L - 0.14, 0.02, 0.003)
    for sx in (-1, 1):
        k.box("Chalk", sx * (L / 2 - 0.07), 0, ly, 0.02, Wd - 0.14, 0.003)
        k.box("Chalk", sx * (L / 2 - 0.37), 0, ly, 0.02, 0.72, 0.003)                 # penalty box
        for sy in (-1, 1):
            k.box("Chalk", sx * (L / 2 - 0.22), sy * 0.35, ly, 0.3, 0.02, 0.003)
        k.cyl("Chalk", sx * (L / 2 - 0.5), 0, top, top + 0.003, 0.02, 0.02, 8)        # spot
    k.arc_box("Chalk", 0, 0, 0.17, 0.19, 0, 2 * math.pi, top, top + 0.003, seg=32)
    # Goals: white posts and bar, a net behind.
    for sx in (-1, 1):
        gx = sx * L / 2
        for sy in (-1, 1):
            k.cyl("Ceramic White", 0, 0, 0, 0, 0.012, 0.012, 8,
                  a=(gx, sy * gw / 2, top), b=(gx, sy * gw / 2, top + 0.16))
        k.cyl("Ceramic White", 0, 0, 0, 0, 0.012, 0.012, 8, a=(gx, -gw / 2, top + 0.16), b=(gx, gw / 2, top + 0.16))
        k.box("Linen", gx + sx * 0.12, 0, top + 0.08, 0.01, gw, 0.16)
        k.box("Linen", gx + sx * 0.06, 0, top + 0.16, 0.12, gw, 0.01)
        for sy in (-1, 1):
            k.box("Linen", gx + sx * 0.06, sy * gw / 2, top + 0.08, 0.12, 0.01, 0.16)
    # The cars: orange attack from the west, blue defend; ball near the blue box.
    cars = (("Team Orange", -0.25, 0.18, 0.3), ("Team Orange", 0.3, -0.28, -0.5),
            ("Team Blue", 0.62, 0.05, 2.9), ("Team Blue", 0.85, -0.3, 2.4))
    for mat, cx, cy, a in cars:
        ca, sa = math.cos(a), math.sin(a)
        rot = lambda u, v: (cx + u * ca - v * sa, cy + u * sa + v * ca)
        k.box(mat, cx, cy, top + 0.045, 0.22, 0.13, 0.04, rz=a)
        k.box("Ceramic Dark", *rot(-0.02, 0), top + 0.078, 0.1, 0.1, 0.03, rz=a)
        k.box(mat, *rot(-0.1, 0), top + 0.1, 0.03, 0.14, 0.01, rz=a)                  # spoiler
        for u in (-0.07, 0.07):
            for v in (-0.075, 0.075):
                px, py = rot(u, v)
                k.cyl("Ceramic Dark", 0, 0, 0, 0, 0.03, 0.03, 10,
                      a=(px + 0.012 * sa, py - 0.012 * ca, top + 0.03), b=(px - 0.012 * sa, py + 0.012 * ca, top + 0.03))
    k.ball("Ceramic White", 0.48, -0.1, top + 0.055, 0.055, sub=2)


def build(ctx):
    wall_h_m = ctx["constants"]["WALL_H"] * ctx["constants"]["UNIT_M"]
    k = F.Kit(ctx, "basement", "basement.BasementWorkGames")
    wall = lambda x, z, side: F.wall(ctx, "basement", x, z, side)
    info = ctx["helpers"]["info"]

    # ---------------- Office -> lounge (user request, 5 Oct 2026)
    on = wall(1.45, 0.4, "north")          # behind the north-window sofa
    on_solid = wall(0.2, 0.4, "north")
    oe = wall(1.0, 0.25, "east")           # under the pinboard
    ow = wall(0.5, 0.7, "west")            # the desk-ledge wall
    os_ = wall(-0.2, 1.2, "south")         # the toilet's north wall
    # RC car football table in the middle, two pendants over it.
    tx, tz = 0.86, 0.72
    rc_football_table(ctx, k, tx, tz)
    for dx in (-0.22, 0.22):
        F.pendant(k, tx + dx, tz, wall_h_m, drop=1.0, r=0.22)
    # Lounge sofas: one along the east wall facing the game, one under the
    # north window facing south, a side table in the corner between them.
    F.rug(k, oe - 0.62, 0.02, oe - 0.02, 1.12, mat=jute(ctx))
    F.sofa(k, oe - 0.42 * M, 0.57, W, length=2.2, fabric="Olive Velvet")
    F.sofa(k, 1.32, on + 0.42 * M, S, length=1.9, fabric="Linen")
    F.side_table(k, oe - 0.1, on + 0.1, h=0.5, r=0.2)
    table_lamp(k, oe - 0.1, on + 0.1, 0.5)
    # Armchair corner by the west window, south of the snack ledge.
    F.rug(k, -0.53, 1.0, 0.14, 1.52, mat=jute(ctx))
    F.armchair(k, ow + 0.5 * M, 1.22, E)
    F.armchair(k, -0.04, os_ - 0.5 * M, N)
    F.side_table(k, ow + 0.1, os_ - 0.08, h=0.5, r=0.18)
    table_lamp(k, ow + 0.1, os_ - 0.08, 0.5)
    # Two stools at the old desk ledge, now the snack ledge.
    for dz in (-0.12, 0.12):
        F.stool(k, ow + 0.15, 0.58 + dz, h=0.62)
    # Game table in the curved corner.
    gx, gz = 0.0, -0.04
    F.game_table(k, gx, gz, 0.3, seed=9)
    for i in range(4):
        a = 0.3 + i * math.pi / 2
        # chair i sits 0.23 u out along direction a (blender x/y -> plan x, -z), facing the table
        px, pz = gx - math.sin(a) * 0.23, gz - math.cos(a) * 0.23
        F.chair(k, px, pz, a)
    F.pendant(k, gx, gz, wall_h_m, drop=1.0, r=0.2)
    F.plant(k, 1.9, on_solid + 0.09, h=1.2, pot_r=0.17, seed=51)
    F.plant(k, oe - 0.09, 1.3, h=1.0, pot_r=0.16, seed=52)
    # Four players round the table, one watching from the sofa.
    if _ent.enabled():
        for name, x, z, rot in (("Person.ManPhone", tx - 0.2, tz - 0.42, -90),
                                ("Person.WomanIdle.Churidar", tx + 0.25, tz - 0.42, -90),
                                ("Person.ManPhone.Blue", tx + 0.05, tz + 0.43, 90),
                                ("Person.ManIdle.Tee", tx - 0.62, tz + 0.1, 0)):
            _ent.place(ctx, name, "basement", x, z, rot, y=0.012, label="Lounge." + name)
        _ent.place(ctx, "Person.WomanSit", "basement", oe - 0.5 * M, 0.45, 180, y=0.012, label="Lounge.WomanSit")

    # ---------------- Studio / gallery: games and meeting room
    sn = wall(1.1, -2.8, "north")
    sw = wall(1.1, -2.8, "west")
    se = wall(1.1, -3.35, "east")          # solid part north of the window
    mx, mz = 1.12, -2.8
    F.long_table(k, mx, mz, 0.0, length=2.4, width=0.95)
    for dx in (-0.32, 0.0, 0.32):
        F.chair(k, mx + dx, mz - 0.28, S, mat="Teak")
        F.chair(k, mx + dx, mz + 0.28, N)
    F.chair(k, mx + 0.6, mz, W)
    for dx in (-0.25, 0.25):
        F.pendant(k, mx + dx, mz, wall_h_m, drop=1.0, r=0.24)
    F.screen(k, sw, mz, E, w=1.6, h=0.95, y0=1.0)
    F.bookshelf(k, mx, sn + 0.16 * M, S, w=1.6, h=0.9, seed=55)     # the games cupboard
    F.lettering(k, mx, sn, S, "GAMES", y0=1.25, px=0.03)
    F.plant(k, se - 0.1, -2.25, h=1.3, pot_r=0.18, seed=53)
    F.plant(k, sw + 0.1, sn + 0.1, h=1.1, pot_r=0.16, seed=54)

    objs = k.done()
    info("basement_work_games: %d objects; office n %.3f (solid %.3f) e %.3f w %.3f s %.3f; studio n %.3f w %.3f e %.3f"
         % (len(objs), on, on_solid, oe, ow, os_, sn, sw, se))
    return []
