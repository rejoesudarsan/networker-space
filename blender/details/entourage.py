"""Entourage from blender/entourage.blend (see ENTOURAGE.md): people at the
gate, in the entrance court, in the first-floor Double HT Court and on the
terrace; a busy street: traffic both ways, cars and two-wheelers parked on
both verges, people on both pavements and crossing. Linked collection instances, nothing appended. The garage car is
placed by garage_fitout. Off with `-- --no-entourage` or SPACE_ENTOURAGE=0.

Positions are Three.js units in each frame (street = the ground frame at
street level). rot: 0 faces east, 90 north, -90 the street, 180 west.
Traffic keeps left: the lane nearer the house runs east, the far lane west.
The pavement in front of the gate (x -3.1..-2.4) and the ramp mouth
(x -1.85..-0.2) is kept clear."""
from . import _entourage as E

PARK_Z = 6.92        # parked cars, on the asphalt by the near verge
NEAR_Z = 7.65        # eastbound lane
FAR_Z = 8.55         # westbound lane
WALK_Z = 6.04        # pavement: outside the fence (z 5.79..5.91), inside the street trees (z 6.17..6.42)
FAR_PARK_Z = 9.3     # the far verge, across the street
FAR_WALK_Z = 9.45    # the far pavement

STREET = [
    # name, x, z, rot
    ("Car.SUV.Silver",              -6.9, PARK_Z, 0),
    ("Car.Hatch.White",              3.95, PARK_Z, 180),
    ("Car.Hatch.Red",               10.4, PARK_Z, 0),
    ("Bike.Scooter.White",           0.75, 6.32, -70),     # parked on the verge, nose to the road
    ("Bike.Vespa.Mint",              1.1, 6.30, -110),
    ("Bike.Motorbike.Red",          -3.75, 6.30, -80),
    ("Bike.Auto.Driven",            -1.4, NEAR_Z, 0),
    ("Bike.Scooter.Blue.Ridden",     2.6, NEAR_Z + 0.1, 0),
    ("Car.SUV.White",                6.8, NEAR_Z, 0),
    ("Car.Hatch.Silver",             8.6, FAR_Z, 180),
    ("Bike.Motorbike.Black.Ridden",  0.9, FAR_Z, 180),
    ("Bike.Scooter.Grey.Ridden",    -8.4, FAR_Z - 0.1, 180),
    # People on the pavement and at the gate
    ("Person.WomanBags.Kurta",      -2.1, WALK_Z, 180),          # heading for the gate
    ("Person.ManWalk.Kurta",        -2.72, 5.15, -90),         # in the gateway, facing the street
    ("Person.ManPhone",              2.3, WALK_Z, 0),
    ("Person.WomanWalk.Kurta",      -5.4, WALK_Z + 0.2, 0),
    # A busy street (user request, 6 Oct 2026): traffic both ways, both verges
    # parked up, people on both pavements and crossing.
    ("Car.Sedan.Grey",              -4.6, NEAR_Z, 0),
    ("Bike.Motorbike.Black.Ridden",  4.4, NEAR_Z + 0.15, 0),
    ("Bike.Scooter.Grey.Ridden",    -9.8, NEAR_Z + 0.1, 0),
    ("Bike.Auto.Driven",            11.5, FAR_Z, 180),
    ("Car.Hatch.White",             -3.4, FAR_Z, 180),
    ("Bike.Scooter.Blue.Ridden",     5.3, FAR_Z - 0.1, 180),
    ("Car.SUV.Silver",             -11.8, FAR_Z, 180),
    ("Car.Hatch.Silver",             7.2, PARK_Z, 0),
    ("Car.Sedan.Grey",             -10.0, PARK_Z, 180),
    ("Bike.Scooter.Grey",            1.45, 6.31, -100),
    ("Bike.Motorbike.Black",         2.0, 6.30, -75),
    ("Bike.Scooter.Blue",           -5.2, 6.30, -95),
    ("Car.Hatch.Red",               -7.5, FAR_PARK_Z, 180),
    ("Car.SUV.White",                2.5, FAR_PARK_Z, 180),
    ("Bike.Scooter.White",           5.9, FAR_PARK_Z - 0.05, 110),
    ("Bike.Vespa.Mint",             -1.0, FAR_PARK_Z - 0.05, 95),
    ("Person.ManWalk.Shirt",        -6.2, WALK_Z, 0),
    ("Person.WomanWalk.Green",       0.4, WALK_Z + 0.1, 180),
    ("Person.ManIdle.Shirt",         3.3, WALK_Z, 0),                # two chatting
    ("Person.WomanIdle.Churidar",    3.62, WALK_Z, 180),
    ("Person.ManPhone.Blue",         8.4, WALK_Z, 180),
    ("Person.WomanBags.Kurta",      -8.6, WALK_Z + 0.15, 0),
    ("Person.ManWalk.Kurta",        -5.6, 8.1, -90),                 # crossing
    ("Person.WomanWalk.Kurta",       6.0, 8.0, 90),
    ("Person.ManWalk.Shirt",        -2.2, FAR_WALK_Z, 180),
    ("Person.WomanWalk.Green",       3.8, FAR_WALK_Z - 0.05, 0),
    ("Person.ManIdle.Tee",           9.2, FAR_WALK_Z, 90),
    ("Person.WomanBags.Kurta",      -9.0, FAR_WALK_Z - 0.05, 180),
]

FLOORS = [
    # frame, name, x, z, rot, y (units above the floor)
    # Entrance court (p24): a man on the green bench, a woman by the plant shelf
    ("ground", "Person.ManSit",            -1.73, 0.72, 180, 0.012),
    ("ground", "Person.WomanIdle.Churidar", -2.05, 0.15, -60, 0.012),
    # Double HT Court (p11): one crossing toward the louvred doors, one by the olive
    ("first",  "Person.WomanWalk.Green",    1.30, 0.85, -40, 0.012),
    ("first",  "Person.ManIdle.Shirt",      1.80, 0.42, 160, 0.012),
    # Terrace (p33): a woman on the timber bench, a man at the parapet
    ("second", "Person.WomanSit",          -1.11, -2.4, 180, 0.012),
    ("second", "Person.ManIdle.Tee",       -2.08, 0.6, 180, 0.012),
]


def build(ctx):
    if not E.enabled():
        ctx["helpers"]["info"]("entourage: off (--no-entourage, SPACE_ENTOURAGE=0 or no entourage.blend)")
        return []
    for name, x, z, rot in STREET:
        E.place(ctx, name, "street", x, z, rot)
    for frame, name, x, z, rot, y in FLOORS:
        E.place(ctx, name, frame, x, z, rot, y=y)
    ctx["helpers"]["info"]("entourage: %d placed from %s" % (len(STREET) + len(FLOORS), E.LIB))
    return []
