"""Club fit-out: the walk-in café (08:00-18:00) on the ground floor.

Living 1 (x 0.62..2.40, z 1.34..3.20, teak floor, brass lanterns) is the
front room: a cushioned lime-plaster banquette on the east wall with three
two-tops, two round tables for four in the middle on a linen rug, the
guestbook "faces" wall on the west wall (Pinterest pin 3), and in the north-
east corner the gulmohar light cone with one empty teak chair (pins 2, 17,
23): the chair the site ends on.

Family 1 (x -1.80..0.54, z -2.17..-0.74) is the bar: a teak-slatted lime
counter with a brass espresso machine along the west wall (it used to stand
across the room and hid it from the street view), open shelves behind it and stools at it, two café tables, a communal teak table for six in
the east half, and the AM / PM
sandstone panel (pin 12) on the east wall. Ground frame, Three.js units.
Measured from top-down renders of the built model (5 Oct 2026)."""
import math

from . import _furniture as F

E, W, N, S = math.pi / 2, -math.pi / 2, math.pi, 0.0      # facing


def build(ctx):
    wall_h_m = ctx["constants"]["WALL_H"] * ctx["constants"]["UNIT_M"]
    k = F.Kit(ctx, "ground", "ground.Cafe")
    wall = lambda x, z, side: F.wall(ctx, "ground", x, z, side)
    living_e = wall(1.8, 2.5, "east")
    living_w = wall(1.2, 2.3, "west")
    living_n = wall(2.0, 1.8, "north")
    family_n = wall(-1.15, -1.5, "north")
    family_e = wall(0.1, -1.33, "east")

    # ---- Living 1: the front room
    F.banquette(k, living_e - 0.226, 1.98, living_e, 3.08, back="east")
    for z in (2.17, 2.52, 2.87):
        F.bistro(k, 1.98, z, r=0.27, seed=int(z * 10))
        F.chair(k, 1.74, z, E)
    F.rug(k, 0.84, 1.72, 1.52, 3.0)
    for i, z in enumerate((1.98, 2.74)):
        x = 1.18
        F.bistro(k, x, z, r=0.36, seed=10 + i)
        F.chair(k, x - 0.19, z, E)
        F.chair(k, x + 0.19, z, W)
        F.chair(k, x, z - 0.19, S)
        F.chair(k, x, z + 0.19, N)
    F.faces_wall(k, living_w, 2.3, E, 1.9, 1.15, y0=0.95)
    F.spotlight_cone(k, 2.0, living_n, S, top_y=2.35, width=0.95, floor_depth=0.75)
    F.chair(k, 2.0, 1.52, S)
    F.plant(k, 2.25, 3.0, h=1.2, seed=3)
    F.plant(k, 0.72, 1.45, h=0.9, pot_r=0.16, seed=4)

    # ---- Family 1: the coffee bar and the communal table
    # The counter runs along the west wall, customers on its east side, so
    # it no longer stands across the room in the view (user, 6 Oct 2026).
    family_w = -1.78                       # the room is open to the west here: no wall for a ray
    F.back_shelf(k, family_w + 0.055, -1.45, E, length=2.4)
    F.coffee_counter(k, family_w + 0.62, -1.45, E, length=2.2, ret=True)
    F.plant(k, -0.35, family_n + 0.1, h=1.3, seed=5)
    # Stools at the counter and two café tables between it and the long table.
    for dz in (-0.27, -0.09, 0.09, 0.27):
        F.stool(k, family_w + 0.83, -1.45 + dz, h=0.72)
    for z in (-1.82, -1.1):
        F.bistro(k, -0.6, z, r=0.3, seed=int(-z * 10) + 20)
        F.chair(k, -0.79, z, E)
        F.chair(k, -0.41, z, W)
    F.long_table(k, 0.12, -1.33, E, length=2.1, width=0.85)
    for z in (-1.72, -1.33, -0.94):
        F.chair(k, -0.08, z, E)
        F.chair(k, 0.32, z, W)
    F.am_pm_panel(k, family_e - 0.01, -1.33, W, w=1.5, h=1.05, y0=1.05)
    F.pendant(k, 0.12, -1.65, wall_h_m, drop=1.15, r=0.2)
    F.pendant(k, 0.12, -1.0, wall_h_m, drop=1.15, r=0.2)

    objs = k.done()
    ctx["helpers"]["info"]("cafe: %d objects; walls living e %.3f w %.3f n %.3f, family n %.3f e %.3f w %.3f"
                           % (len(objs), living_e, living_w, living_n, family_n, family_e, family_w))
    return []
