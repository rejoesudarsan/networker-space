"""Club fit-out: Family 2 on the first floor becomes the PS5 room (user
request, 5 Oct 2026). The room (family2_sliding_teak_door.py): x 0.81..2.62,
z -2.83..-1.375, the big window on the north wall, the sliding teak panel
and bulkhead on the south wall, the floating teak shelf on a dark panel on
the west wall (z -2.3..-1.7, top 0.37 u), a narrow window at the south end
of the east wall, the ceiling fan.

Layout: a 65" TV on the west wall over the shelf, the PS5 and a soundbar on
the shelf (the PS5 lying flat), a glowing PLAY sign above; an olive sofa facing it with two
people playing, a low teak table with controllers and a headset, two bean
bags on an indigo rug; a retro arcade cabinet in the north-west corner; a
games shelf on the east wall. First frame, Three.js units."""
import math

from . import _entourage as _ent
from . import _furniture as F
from . import _trees

E, W, N, S = math.pi / 2, -math.pi / 2, math.pi, 0.0      # facing
M = F.M
SHELF_X1, SHELF_TOP = 0.81 + 0.13, 0.37    # floating shelf front edge and top (units)


def _glow(ctx, name, hex_colour, strength):
    m = _trees.material(ctx, name, hex_colour, 0.4)
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    for key in ("Emission Color", "Emission"):
        if key in bsdf.inputs:
            bsdf.inputs[key].default_value = bsdf.inputs["Base Color"].default_value
            break
    bsdf.inputs["Emission Strength"].default_value = strength
    return m


def build(ctx):
    info = ctx["helpers"]["info"]
    k = F.Kit(ctx, "first", "first.Family2PS5")
    wall = lambda x, z, side: F.wall(ctx, "first", x, z, side)
    west = wall(1.5, -2.0, "west")             # the dark panel behind the shelf
    north = wall(1.05, -2.2, "north")          # solid corner west of the window
    east = wall(2.0, -2.5, "east")
    for name, hx in (("Rug Indigo", "#3B4A6B"), ("Beanbag Teal", "#2E6E6A"), ("Beanbag Mustard", "#C99A2E"),
                     ("Arcade Red", "#B8332E"), ("PS5 White", "#F2F2F0")):
        _trees.material(ctx, name, hx, 0.85 if "Bean" in name or "Rug" in name else 0.45)
    _glow(ctx, "TV Screen", "#2B4C8C", 1.2)
    _glow(ctx, "TV Pitch", "#3E8A44", 1.2)
    _glow(ctx, "Arcade Screen", "#5AB8D8", 1.5)

    # TV on the west wall above the shelf, a simple game on screen.
    tz, ty = -2.0, 1.5
    k.at(west, tz, E)
    k.box("Black Steel", 0, -0.03, ty, 1.45, 0.045, 0.84)
    k.box("TV Screen", 0, -0.054, ty + 0.12, 1.40, 0.004, 0.55)
    k.box("TV Pitch", 0, -0.054, ty - 0.27, 1.40, 0.004, 0.24)
    F.lettering(k, west, tz, E, "PLAY", y0=2.05, px=0.035, mat="Lamp Glow")
    # PS5 lying flat at the north end of the shelf, soundbar under the TV.
    k.at((west + SHELF_X1) / 2, -2.14, 0.0, y=SHELF_TOP - k.base)
    k.box("PS5 White", 0, 0, 0.052, 0.26, 0.39, 0.104)
    k.box("Black Steel", 0, 0, 0.052, 0.265, 0.395, 0.05)
    k.at((west + SHELF_X1) / 2, tz, E, y=SHELF_TOP - k.base)
    k.box("Black Steel", 0, 0, 0.035, 0.95, 0.09, 0.07)

    # Sofa facing the TV, low table with controllers and a headset.
    F.rug(k, 1.08, -2.55, 2.3, -1.5, mat="Rug Indigo")
    sx = 2.12
    F.sofa(k, sx, tz, W, length=2.2, fabric="Olive Velvet")
    k.at(1.66, tz, W)
    k.box("Teak", 0, 0, 0.36, 1.1, 0.55, 0.04)
    for ex in (-1, 1):
        k.box("Teak", ex * 0.5, 0, 0.17, 0.05, 0.45, 0.34)
    for i, (cx, cy, a, mat) in enumerate(((-0.3, 0.05, 0.2, "PS5 White"), (0.25, -0.08, -0.4, "Ceramic Dark"))):
        k.box(mat, cx, cy, 0.4, 0.16, 0.1, 0.035, rz=a)
    k.cyl("Ceramic Dark", 0.05, 0.1, 0.38, 0.4, 0.09, 0.09, 16)                       # headset
    k.cyl("Ceramic White", -0.42, -0.15, 0.38, 0.47, 0.04, 0.045, 12)                 # mug
    # Bean bags nearer the screen.
    for bz, mat in ((-2.38, "Beanbag Teal"), (-1.68, "Beanbag Mustard")):
        k.at(1.28, bz)
        k.ball(mat, 0, 0, 0.24, 0.42, sz=0.6, sub=2)

    # Retro arcade cabinet in the north-west corner, facing south.
    ax = west + 0.32 * M
    k.at(ax, north + 0.36 * M, S)
    k.box("Arcade Red", 0, 0, 0.88, 0.62, 0.7, 1.76)
    k.box("Black Steel", 0, -0.36, 1.32, 0.52, 0.02, 0.42)
    k.box("Arcade Screen", 0, -0.372, 1.32, 0.46, 0.004, 0.36)
    k.box("Black Steel", 0, -0.43, 0.98, 0.62, 0.18, 0.06, rx=-0.25)
    for bx, mat in ((-0.15, "Ceramic Dark"), (0.0, "Team Blue"), (0.08, "Arcade Red"), (0.16, "Beanbag Mustard")):
        if mat == "Team Blue":
            _trees.material(ctx, "Team Blue", "#2F5FB8", 0.45)
        k.cyl(mat, bx, -0.44, 1.0, 1.03, 0.022, 0.022, 10)
    k.box("Lamp Glow", 0, -0.36, 1.66, 0.58, 0.02, 0.14)

    # Games shelf on the east wall (south of it the window), a plant.
    F.bookshelf(k, east - 0.16 * M, -2.62, W, w=0.8, h=1.6, seed=31)
    F.plant(k, east - 0.1, -1.78, h=1.0, pot_r=0.15, seed=32)

    objs = k.done()
    if _ent.enabled():
        _ent.place(ctx, "Person.ManSit", "first", sx - 0.04, tz - 0.17, 180, y=0.012, label="PS5.ManSit")
        _ent.place(ctx, "Person.WomanSit", "first", sx - 0.04, tz + 0.17, 180, y=0.012, label="PS5.WomanSit")
    info("family2_ps5: %d objects; walls w %.3f n %.3f e %.3f" % (len(objs), west, north, east))
    return []
