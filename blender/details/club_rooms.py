"""Club fit-out: every room that was still empty (user request, 6 Oct 2026),
following the members'-club plan.

Ground floor: the long meeting room and the back kitchen behind the café,
two washrooms, the work hall in the middle (a communal table on one side of
its partition, desks on the other), the maker space at the front with the maker's table and its
tool room. First floor: two private member rooms and a private meeting room
on the north-west side, a phone booth by Family 2. Second floor: a phone
booth and the nap / reading room between the terrace and the court.

Each room is found from a seed point inside it: rays at 2.6 m (above the
door heads, so doorways do not leak) find its four walls, and the layout is
fitted to that rectangle along its long side. Where the rays leak (open
gaps, a beam) the rectangle is given, measured from top-down renders. Everything stands on the floor
and stays under the short walls' 1 m where it sits against a wall, so the
baked dioramas read cleanly. Three.js units."""
import math

from . import _furniture as F
from . import _trees

E, W, N, S = math.pi / 2, -math.pi / 2, math.pi, 0.0      # facing
M = F.M

ROOMS = {
    # floor: [(name, seed x, seed z, kind[, rect x0, z0, x1, z1 where the rays leak]), ...]
    "ground": [
        ("meeting", -0.6, -3.0, "meeting", (-1.72, -3.67, 0.52, -2.23)),
        ("kitchen", 1.5, -3.0, "kitchen"),
        ("wc1", 0.92, -1.7, "washroom"),
        ("wc2", 1.88, -1.7, "washroom"),
        ("workhall", -1.0, 0.3, "hall", (-1.54, -0.68, -0.59, 1.28)),
        ("workroom", 0.0, 0.3, "cowork", (-0.47, -0.68, 0.52, 1.28)),
        ("maker", -1.0, 2.2, "maker"),
        ("tools", 0.16, 2.4, "tools"),
        ("reading", -2.45, -1.6, "library", (-2.98, -2.42, -1.90, -0.80)),
    ],
    "first": [
        ("member1", -2.25, -3.5, "member"),
        ("member2", -2.45, -2.3, "member"),
        ("privatemeet", -2.25, -0.8, "private_meeting"),
        ("booth1", 0.40, -2.35, "booth"),
    ],
    "second": [
        ("booth2", -0.42, 1.47, "booth", (-0.91, 1.19, 0.08, 1.75)),
        ("nap", -0.42, 2.45, "nap"),
    ],
}


def mats(ctx):
    for name, hx, r in (("Brushed Steel", "#B9BDC0", 0.35), ("Workbench Top", "#C9A27A", 0.7),
                        ("Cutting Mat", "#2F5D4A", 0.9), ("Tool Red", "#B8332E", 0.5),
                        ("Bin Blue", "#3F6FA8", 0.6), ("Bin Yellow", "#D9A82E", 0.6),
                        ("Rug Rust", "#9A5A3C", 0.95), ("Rug Sage", "#8A9A7A", 0.95),
                        ("Daybed Linen", "#E4DCCB", 0.95)):
        _trees.material(ctx, name, hx, r)


def room_rect(ctx, floor, x, z):
    w = lambda side: F.wall(ctx, floor, x, z, side, h=2.6)
    return w("west"), w("north"), w("east"), w("south")


# ---------------------------------------------------------------- pieces

def floor_lamp(k, x, z):
    k.at(x, z)
    k.cyl("Black Steel", 0, 0, 0, 0.03, 0.16, 0.16, 16)
    k.cyl("Black Steel", 0, 0, 0.03, 1.4, 0.012, 0.012, 6)
    k.cyl("Linen", 0, 0, 1.32, 1.58, 0.2, 0.15, 16)
    k.cyl("Lamp Glow", 0, 0, 1.34, 1.36, 0.1, 0.1, 10)


def counter(k, x, z, rot, length, depth=0.65, h=0.9, top="Brushed Steel"):
    k.at(x, z, rot)
    k.box("Brushed Steel", 0, 0, (h - 0.04) / 2, length, depth, h - 0.04)
    k.box(top, 0, 0, h - 0.02, length + 0.02, depth + 0.02, 0.04)


def wc(k, x, z, rot):
    k.at(x, z, rot)
    k.box("Ceramic White", 0, 0.05, 0.2, 0.36, 0.5, 0.4)
    k.box("Ceramic White", 0, 0.28, 0.6, 0.42, 0.16, 0.4)          # cistern, against the wall
    k.box("Ceramic White", 0, 0.0, 0.42, 0.38, 0.46, 0.03)


def vanity(k, x, z, rot, length=0.9):
    k.at(x, z, rot)
    k.box("Teak", 0, 0, 0.4, length, 0.5, 0.8)
    k.cyl("Ceramic White", 0, -0.02, 0.8, 0.9, 0.2, 0.17, 20)
    k.cyl("Brass", 0, 0.18, 0.8, 0.95, 0.012, 0.012, 6)


def low_shelf(k, x, z, rot, length=1.4, h=0.85, seed=1, bins=False):
    """A low open teak shelf (under the short walls), books or tool bins."""
    import random
    k.at(x, z, rot)
    d = 0.35
    for y in (0.0, h / 2, h - 0.03):
        k.box("Teak", 0, 0, y + 0.015, length, d, 0.03)
    for sx in (-1, 1):
        k.box("Teak", sx * (length / 2 - 0.015), 0, h / 2, 0.03, d, h)
    rnd = random.Random(seed)
    for row in (0.03, h / 2 + 0.015):
        u = -length / 2 + 0.05
        while u < length / 2 - 0.1:
            if bins:
                w = 0.28
                k.box(rnd.choice(("Bin Blue", "Bin Yellow", "Tool Red")), u + w / 2, 0, row + 0.1, w - 0.02, d - 0.06, 0.2)
            else:
                w = rnd.uniform(0.02, 0.05)
                k.box("Book Spines", u + w / 2, 0, row + 0.13, w, d - 0.08, rnd.uniform(0.2, 0.3))
            u += w + 0.01


def daybed(k, x, z, rot, length=2.0):
    k.at(x, z, rot)
    k.box("Teak", 0, 0, 0.15, length, 0.95, 0.3)
    k.box("Daybed Linen", 0, 0, 0.38, length - 0.06, 0.9, 0.16)
    for u in (-0.5, 0.0, 0.5):
        k.box("Cushion", u, 0.32, 0.55, 0.45, 0.16, 0.36, rx=-0.2)


def maker_table(k, x, z, rot):
    """The maker's table: a big beech workbench, a cutting mat, tools."""
    k.at(x, z, rot)
    L, D, h = 2.6, 1.2, 0.92
    k.box("Workbench Top", 0, 0, h - 0.03, L, D, 0.06)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.box("Black Steel", sx * (L / 2 - 0.1), sy * (D / 2 - 0.1), (h - 0.06) / 2, 0.06, 0.06, h - 0.06)
    k.box("Teak", 0, 0, 0.18, L - 0.3, D - 0.25, 0.03)                  # lower shelf
    k.box("Cutting Mat", -0.6, 0.0, h + 0.002, 0.9, 0.6, 0.004)
    k.box("Tool Red", 0.55, 0.2, h + 0.05, 0.4, 0.2, 0.1)                # toolbox
    k.box("Brushed Steel", 0.9, -0.25, h + 0.1, 0.18, 0.18, 0.2)        # vice
    k.cyl("Brass", 0.1, -0.3, h, h + 0.02, 0.12, 0.12, 16)              # a reel of wire


def printer(k, x, z, rot):
    k.at(x, z, rot)
    k.box("Black Steel", 0, 0, 0.92 + 0.22, 0.42, 0.42, 0.04)
    for sx in (-1, 1):
        for sy in (-1, 1):
            k.box("Black Steel", sx * 0.19, sy * 0.19, 0.92 + 0.2, 0.03, 0.03, 0.4)
    k.box("Bin Yellow", 0, 0, 0.95, 0.12, 0.12, 0.06)


def laser(k, x, z, rot):
    k.at(x, z, rot)
    k.box("Ceramic White", 0, 0, 0.92 + 0.13, 0.9, 0.55, 0.26)
    k.box("Ceramic Dark", 0, 0, 0.92 + 0.27, 0.8, 0.45, 0.02)


# ---------------------------------------------------------------- rooms

def axes(r):
    """Centre, long length, short length (units) and the rotation that runs a
    piece's length along the room's long side."""
    x0, z0, x1, z1 = r
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    lx, lz = x1 - x0, z1 - z0
    return cx, cz, max(lx, lz), min(lx, lz), (0.0 if lx >= lz else E)


def along(r, t, s=0.0):
    """Point at fraction t (-0.5..0.5) along the long axis, offset s units across."""
    cx, cz, L, Sh, rot = axes(r)
    return (cx + t * L, cz + s) if rot == 0.0 else (cx + s, cz + t * L)


def side_faces(rot):
    """Facings for chairs on the two long sides of a table run along rot."""
    return (S, N) if rot == 0.0 else (W, E)


def meeting(ctx, k, r, wall_h):
    cx, cz, L, Sh, rot = axes(r)
    length = min(L / M - 1.8, 3.6)
    F.long_table(k, cx, cz, rot, length=length, width=1.0)
    n = max(2, int(length / 0.65))
    fa, fb = side_faces(rot)
    for i in range(n):
        t = (-length / 2 + 0.35 + i * (length - 0.7) / max(1, n - 1)) * M / L
        F.chair(k, *along(r, t, -0.27), fb if rot == 0.0 else fa)
        F.chair(k, *along(r, t, 0.27), fa if rot == 0.0 else fb)
    for t in (-0.18, 0.18):
        F.pendant(k, *along(r, t), wall_h, drop=1.0, r=0.22)
    x0, z0, x1, z1 = r
    F.plant(k, x0 + 0.12, z0 + 0.12, h=1.2, seed=61)
    F.plant(k, x1 - 0.12, z1 - 0.12, h=1.0, seed=62)


def kitchen(ctx, k, r, wall_h):
    x0, z0, x1, z1 = r
    d = 0.65 * M
    counter(k, (x0 + x1) / 2, z0 + d / 2 + 0.004, S, (x1 - x0) / M - 0.05)          # along the north wall
    counter(k, x1 - d / 2 - 0.004, (z0 + z1) / 2 + d / 2, W, (z1 - z0) / M - 0.75)  # along the east wall
    k.at(x0 + 0.17, z1 - 0.17)
    k.box("Brushed Steel", 0, 0, 0.93, 0.75, 0.72, 1.86)                             # fridge
    cx, cz = (x0 + x1) / 2 - 0.05, (z0 + z1) / 2 + 0.08
    counter(k, cx, cz, 0.0, min(1.8, (x1 - x0) / M - 2.2), depth=0.9, top="Workbench Top")  # prep island
    k.at(cx, cz)
    k.cyl("Ceramic White", -0.3, 0, 0.9, 0.98, 0.14, 0.12, 16)
    k.box("Teak", 0.3, 0, 0.92, 0.45, 0.3, 0.03)


def washroom(ctx, k, r, wall_h):
    x0, z0, x1, z1 = r
    lx, lz = x1 - x0, z1 - z0
    # WC against the north wall at one end, the vanity at the other.
    wc(k, x0 + 0.25 * M + 0.03, z0 + 0.3 * M, S)
    vanity(k, x1 - 0.5 * M, z0 + 0.25 * M + 0.004, S, length=min(0.9, lx / M - 1.1))
    F.plant(k, x1 - 0.08, z1 - 0.08, h=0.6, pot_r=0.1, seed=63)


def hall(ctx, k, r, wall_h):
    cx, cz, L, Sh, rot = axes(r)
    fa, fb = side_faces(rot)
    length = min(L / M - 2.0, 3.2)
    for s in ((-0.38, 0.38) if Sh > 1.3 else (0.0,)):
        x, z = along(r, 0.0, s)
        F.long_table(k, x, z, rot, length=length, width=0.85)
        n = max(2, int(length / 0.6))
        for i in range(n):
            t = (-length / 2 + 0.3 + i * (length - 0.6) / max(1, n - 1)) * M / L
            F.stool(k, *along(r, t, s - 0.22), h=0.46)
            F.stool(k, *along(r, t, s + 0.22), h=0.46)
        for t in (-0.15, 0.15):
            F.pendant(k, *along(r, t, s), wall_h, drop=1.05, r=0.2)
    x0, z0, x1, z1 = r
    for i, (x, z) in enumerate(((x0 + 0.12, z0 + 0.12), (x1 - 0.12, z0 + 0.12), (x0 + 0.12, z1 - 0.12))):
        F.plant(k, x, z, h=1.2, seed=64 + i)


def cowork(ctx, k, r, wall_h):
    cx, cz, L, Sh, rot = axes(r)
    n = max(1, int((L / M - 0.6) / 1.5))
    for i in range(n):
        t = (i + 0.5) / n - 0.5
        x, z = along(r, t * 0.9)
        # two desks face to face across the room's short axis
        for s, f in ((-0.16, 1), (0.16, -1)):
            dx, dz = along(r, t * 0.9, s)
            F.desk(k, dx, dz, rot if f > 0 else rot + math.pi, length=1.3, depth=0.7)
            fa, fb = side_faces(rot)
            F.chair(k, *along(r, t * 0.9, s * 2.1), fb if f > 0 else fa)
    x0, z0, x1, z1 = r
    F.plant(k, x0 + 0.1, z0 + 0.1, h=1.1, seed=67)
    floor_lamp(k, x1 - 0.12, z1 - 0.12)


def maker(ctx, k, r, wall_h):
    x0, z0, x1, z1 = r
    cx, cz, L, Sh, rot = axes(r)
    maker_table(k, cx, cz + 0.05, rot)
    fa, fb = side_faces(rot)
    for t in (-0.25, -0.08, 0.08, 0.25):
        F.stool(k, *along(r, t, -0.36), h=0.66)
        F.stool(k, *along(r, t, 0.36), h=0.66)
    F.pendant(k, *along(r, -0.15), wall_h, drop=0.95, r=0.24)
    F.pendant(k, *along(r, 0.15), wall_h, drop=0.95, r=0.24)
    # Machine bench along the north wall: two 3D printers and a laser cutter.
    bx, bz = (x0 + x1) / 2, z0 + 0.35 * M + 0.004
    counter(k, bx, bz, S, min(3.0, (x1 - x0) / M - 0.6), depth=0.7, top="Workbench Top")
    for u in (-1.0, -0.45):
        printer(k, bx + u * M, bz, S)
    laser(k, bx + 0.6 * M, bz, S)
    # Material shelves along the west wall, the tool trolley by the door side.
    low_shelf(k, x0 + 0.18 * M + 0.004, (z0 + z1) / 2 + 0.15, E, length=1.6, seed=71, bins=True)
    k.at(x1 - 0.2, z1 - 0.25)
    k.box("Tool Red", 0, 0, 0.45, 0.6, 0.45, 0.8)
    F.plant(k, x1 - 0.1, z0 + 0.45, h=1.0, seed=72)


def tools(ctx, k, r, wall_h):
    x0, z0, x1, z1 = r
    low_shelf(k, x0 + 0.18 * M + 0.004, (z0 + z1) / 2, E, length=min(2.2, (z1 - z0) / M - 0.4), seed=73, bins=True)
    low_shelf(k, x1 - 0.18 * M - 0.004, (z0 + z1) / 2, W, length=min(2.2, (z1 - z0) / M - 0.4), seed=74, bins=True)


def member(ctx, k, r, wall_h):
    x0, z0, x1, z1 = r
    cx, cz, L, Sh, rot = axes(r)
    F.rug(k, cx - 0.32, cz - 0.28, cx + 0.32, cz + 0.28, mat="Rug Rust")
    # desk against the north wall, chair facing it
    F.desk(k, x0 + 0.3, z0 + 0.35 * M + 0.004, S, length=1.2, depth=0.7)
    F.chair(k, x0 + 0.3, z0 + 0.35 * M + 0.2, N)
    F.armchair(k, x1 - 0.22, z1 - 0.25, N + 0.6)
    F.side_table(k, x1 - 0.1, z1 - 0.48, h=0.5, r=0.18)
    floor_lamp(k, x0 + 0.1, z1 - 0.1)
    F.plant(k, x1 - 0.1, z0 + 0.1, h=1.1, seed=75)


def private_meeting(ctx, k, r, wall_h):
    cx, cz, L, Sh, rot = axes(r)
    F.rug(k, cx - 0.4, cz - 0.4, cx + 0.4, cz + 0.4, mat="Rug Sage")
    F.bistro(k, cx, cz, r=0.55, h=0.74, top="Teak", things=False)
    for i in range(5):
        a = i * math.tau / 5
        F.chair(k, cx - math.sin(a) * 0.3, cz - math.cos(a) * 0.3, a)
    F.pendant(k, cx, cz, wall_h, drop=1.0, r=0.26)
    x0, z0, x1, z1 = r
    low_shelf(k, (x0 + x1) / 2, z0 + 0.18 * M + 0.004, S, length=min(1.8, (x1 - x0) / M - 0.6), seed=76)
    F.plant(k, x1 - 0.1, z1 - 0.1, h=1.2, seed=77)


def booth(ctx, k, r, wall_h):
    x0, z0, x1, z1 = r
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    F.armchair(k, cx, cz - 0.05, S)
    F.side_table(k, cx + 0.22, cz + 0.12, h=0.55, r=0.15)
    floor_lamp(k, cx - 0.22, cz - 0.15)


def nap(ctx, k, r, wall_h):
    x0, z0, x1, z1 = r
    cx, cz, L, Sh, rot = axes(r)
    F.rug(k, x0 + 0.08, z0 + 0.1, x1 - 0.08, z1 - 0.1, mat="Rug Sage")
    if rot == 0.0:
        daybed(k, cx, z0 + 0.48 * M, S, length=min(2.0, (x1 - x0) / M - 0.3))
    else:
        daybed(k, x0 + 0.48 * M, cz - 0.15, E, length=min(2.0, (z1 - z0) / M - 0.8))
    low_shelf(k, x1 - 0.18 * M - 0.004, cz + 0.2, W, length=1.2, seed=78)
    F.armchair(k, cx + 0.05, z1 - 0.3, N)
    floor_lamp(k, x1 - 0.12, z1 - 0.12)
    F.plant(k, x0 + 0.1, z1 - 0.1, h=1.0, seed=79)


def library(ctx, k, r, wall_h):
    """The reading room: low shelves round the walls, a reading table for
    four, two armchair pairs on a rug, floor lamps."""
    x0, z0, x1, z1 = r
    cx, cz, L, Sh, rot = axes(r)
    low_shelf(k, x0 + 0.18 * M + 0.004, (z0 + z1) / 2, E, length=min(2.4, (z1 - z0) / M - 0.6), seed=81)
    low_shelf(k, x1 - 0.18 * M - 0.004, (z0 + z1) / 2 - 0.3, W, length=1.4, seed=82)
    low_shelf(k, (x0 + x1) / 2, z0 + 0.18 * M + 0.004, S, length=min(1.8, (x1 - x0) / M - 0.8), seed=83)
    # reading table in the north half
    tx, tz = cx + 0.04, z0 + (z1 - z0) * 0.32
    F.long_table(k, tx, tz, rot, length=1.5, width=0.85)
    fa, fb = side_faces(rot)
    for d in (-0.15, 0.15):
        F.chair(k, *((tx + d, tz - 0.25) if rot == 0.0 else (tx - 0.25, tz + d)), fb if rot == 0.0 else fa)
        F.chair(k, *((tx + d, tz + 0.25) if rot == 0.0 else (tx + 0.25, tz + d)), fa if rot == 0.0 else fb)
    F.pendant(k, tx, tz, wall_h, drop=1.0, r=0.22)
    # armchairs on a rug in the south half
    ax, az = cx + 0.04, z0 + (z1 - z0) * 0.74
    F.rug(k, ax - 0.33, az - 0.3, ax + 0.33, az + 0.3, mat="Rug Rust")
    F.armchair(k, ax - 0.2, az - 0.12, E + 0.3)
    F.armchair(k, ax + 0.2, az - 0.12, W - 0.3)
    F.armchair(k, ax - 0.2, az + 0.18, E - 0.3)
    F.side_table(k, ax, az + 0.02, h=0.5, r=0.18)
    floor_lamp(k, x0 + 0.12, z1 - 0.12)
    floor_lamp(k, x1 - 0.12, z0 + 0.12)
    F.plant(k, x1 - 0.1, z1 - 0.1, h=1.2, seed=84)


LAYOUT = dict(meeting=meeting, kitchen=kitchen, washroom=washroom, hall=hall, cowork=cowork, maker=maker,
              tools=tools, library=library, member=member, private_meeting=private_meeting, booth=booth, nap=nap)


def build(ctx):
    info, warn = ctx["helpers"]["info"], ctx["helpers"]["warn"]
    wall_h = ctx["constants"]["WALL_H"] * ctx["constants"]["UNIT_M"]
    mats(ctx)
    n = 0
    for floor, rooms in ROOMS.items():
        k = F.Kit(ctx, floor, "%s.ClubRooms" % floor)
        for name, x, z, kind, *fixed in rooms:
            r = fixed[0] if fixed else room_rect(ctx, floor, x, z)
            if r[2] - r[0] < 0.15 or r[3] - r[1] < 0.15:
                warn("club_rooms: %s %s too small %s" % (floor, name, r))
                continue
            LAYOUT[kind](ctx, k, r, wall_h)
            info("club_rooms: %s %s (%s) x %.2f..%.2f z %.2f..%.2f" % (floor, name, kind, r[0], r[2], r[1], r[3]))
        n += len(k.done())
    info("club_rooms: %d objects" % n)
    return []
