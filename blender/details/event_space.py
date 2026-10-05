"""Club fit-out: the event space (talks, demo nights, gigs) in first-floor
Living 2.

Living 2 (walls measured by raycast: x 0.813..2.625, z 1.76..4.07) opens on
its north side to the Double HT court, the foyer, across x 1.0..2.52, and
has a doorway from the hall in its west wall at z 1.76..2.17. The street
window (with the roman blinds) is the east half of the south wall, and a
small corner window ends the east wall at z 3.8. So the room faces west:
a low teak stage along the solid west wall with the projection screen above
it, tiered teak bleachers with gulmohar cushions (pin 21) backed onto the
east wall facing it, a front row of low floor poufs between them, two rattan
pendants down the middle and a ceiling projector. The band z 1.76..2.3 is
left clear so the court, the hall door and the room stay one circulation
space. First frame, Three.js units."""
import math

from . import _furniture as F

E, W, N, S = math.pi / 2, -math.pi / 2, math.pi, 0.0      # facing
M = F.M


def pouf(kit, x, z, r=0.24, h=0.36):
    """Low round floor cushion in gulmohar on a teak plinth."""
    kit.at(x, z)
    kit.cyl("Teak", 0, 0, 0, 0.05, r * 0.9, r * 0.9, 18)
    kit.cyl("Cushion", 0, 0, 0.05, h, r, r * 0.95, 18)


def projector(kit, x, z, ceiling, rot=0.0):
    """Ceiling-mounted projector on a black drop rod, lens toward -y."""
    kit.at(x, z, rot)
    kit.cyl("Black Steel", 0, 0, ceiling - 0.45, ceiling, 0.015, 0.015, 8)
    kit.box("Black Steel", 0, 0, ceiling - 0.52, 0.34, 0.28, 0.1)
    kit.cyl("Ceramic Dark", 0, 0, 0, 0, 0.035, 0.035, 12,
            a=(0.08, -0.13, ceiling - 0.52), b=(0.08, -0.17, ceiling - 0.52))


def build(ctx):
    wall_h_m = ctx["constants"]["WALL_H"] * ctx["constants"]["UNIT_M"]
    k = F.Kit(ctx, "first", "first.EventSpace")
    wall = lambda x, z, side, h=1.2: F.wall(ctx, "first", x, z, side, h=h)
    west = wall(1.5, 3.05, "west")          # 0.813
    east = wall(1.5, 3.05, "east")          # 2.625
    south = wall(1.2, 3.05, "south")        # 4.07 (solid part of the street wall)

    zc = 3.07                               # axis of stage, screen and seating
    # ---- Stage on the west wall, screen above it
    st_d, st_h = 1.15, 0.3
    F.stage(k, west + st_d / 2 * M, zc, E, w=3.3, d=st_d, h=st_h)
    F.screen(k, west, zc, E, w=2.6, h=1.46, y0=st_h + 0.95)
    F.plant(k, west + 0.12, south - 0.14, h=1.25, pot_r=0.19, seed=21)

    # ---- Tiered bleachers on the east wall, facing the stage (pin 21)
    steps, tread = 3, 0.6
    F.bleachers(k, east - steps * tread * M, zc - 0.04, W, width=3.2, steps=steps, rise=0.4, tread=tread)
    F.plant(k, east - 0.13, 3.88, h=1.0, pot_r=0.17, seed=22)

    # ---- Front row: low gulmohar poufs between stage and bleachers
    for z in (2.62, 2.92, 3.22, 3.52):
        pouf(k, 1.62, z)

    # ---- Light: two rattan pendants down the room, the projector
    for z in (2.55, 3.55):
        F.pendant(k, 1.62, z, wall_h_m, drop=1.0, r=0.24)
    projector(k, 2.05, zc, wall_h_m, W)

    objs = k.done()
    ctx["helpers"]["info"]("event_space: %d objects; walls w %.3f e %.3f s %.3f"
                           % (len(objs), west, east, south))
    return []
