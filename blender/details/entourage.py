"""Entourage from blender/entourage.blend (see ENTOURAGE.md): people at the
gate, in the entrance court, in the first-floor Double HT Court and on the
terrace; parked and passing cars, scooters, a motorbike and an auto on the
street. Linked collection instances, nothing appended. The garage car is
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
WALK_Z = 5.6         # pavement

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
    ("Person.WomanBags.Kurta",      -2.1, WALK_Z - 0.15, 180),   # heading for the gate
    ("Person.ManWalk.Kurta",        -2.72, 5.15, -90),         # in the gateway, facing the street
    ("Person.ManPhone",              2.3, WALK_Z, 0),
    ("Person.WomanWalk.Kurta",      -5.4, WALK_Z + 0.2, 0),
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
