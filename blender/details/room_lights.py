"""Environment and light (Astra comps home-07, -10, -13, -16, -19): warm lamp
fixtures with real lights, so the Cycles bake paints lamp pools on the walls
and floors as the comps do.

Every fixture is a small piece of geometry with an emissive 'Lamp Glow' shade
(bake_site exports it as a flat glowing fixture) plus a real Blender light
(point or spot, ~2700 K, parented to the floor empty) that the bake picks up.
Each light object carries the custom property club_lamp = 1 (and
club_lamp_room); bake_site's day set scales club_lamp lights down, the night
set keeps them at full power. Lights are named Lamp.<room>.<n>.

- Café (ground, Living 1): brass wall sconces with glowing cup shades, two on
  the west wall either side of the guestbook faces wall, two on the east wall
  above the banquette.
- Court (first, Double HT court): sconces on the two plaster piers between
  the louvred shutter bays on the east wall, one on the north wall east of the
  doorway.
- Event space (first, Living 2): up/down wall washers, two on the west wall
  either side of the screen, two on the east wall above the bleachers.
- Basement office: up/down wall washers on the north, east and south walls.
- Terrace (second): a sconce on the house wall above the banquette, and a small point light in
  every bulb of the festoon that terrace_evening.py hangs ('Lamp Glow' balls in
  second.TerraceEvening.LampGlow).
Floor-local Three.js units for positions, metres for fixture sizes."""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

from . import _furniture as F

E, W, N, S = math.pi / 2, -math.pi / 2, math.pi, 0.0      # facing
M = F.M
KELVIN = 2700
# Linear-RGB colour of a 2700 K blackbody (used where the light has no temperature setting).
WARM = (1.0, 0.56, 0.25)
FACING = {"north": S, "south": N, "east": W, "west": E}     # facing away from the wall
OUT = {"north": (0, 1), "south": (0, -1), "east": (-1, 0), "west": (1, 0)}   # plan dx, dz into the room


def _light(ctx, floor, name, kind, x, z, y_m, power, radius=0.05, up=False, spot_deg=120.0, room=""):
    data = bpy.data.lights.new(name, type=kind)
    data.energy = power
    if hasattr(data, "temperature") and hasattr(data, "use_temperature"):
        data.use_temperature = True
        data.temperature = KELVIN
        data.color = (1.0, 1.0, 1.0)
    else:
        data.color = WARM
    data.shadow_soft_size = radius
    if kind == "SPOT":
        data.spot_size = math.radians(spot_deg)
        data.spot_blend = 0.75
        data.show_cone = False
    ob = bpy.data.objects.new(name, data)
    ctx["colls"][floor].objects.link(ob)
    ob.parent = ctx["empties"][floor]
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.location = (x, -z, 0.0085 + y_m * M)
    ob.scale = (M, M, M)               # undo the floor empty's units -> metres scale
    if up:
        ob.rotation_euler = (math.pi, 0, 0)
    ob["club_lamp"] = 1
    ob["club_lamp_room"] = room
    return ob


def sconce(ctx, kit, floor, room, n, x, z, side, y_m=2.0, power=35.0):
    """Brass wall sconce: backplate, short arm, an upturned glowing cup.
    (x, z) is the wall-face point; the light sits in the cup."""
    rot = FACING[side]
    kit.at(x, z, rot)
    kit.box("Brass", 0, -0.008, y_m, 0.07, 0.016, 0.16)
    kit.cyl("Brass", 0, 0, 0, 0, 0.008, 0.008, 6, a=(0, -0.016, y_m - 0.03), b=(0, -0.12, y_m - 0.01))
    kit.cyl("Brass", 0, 0, y_m - 0.03, y_m - 0.01, 0.022, 0.03, 10)
    # The cup: a glowing conical shade around the arm's end.
    kit.cyl("Lamp Glow", 0, -0.14, y_m - 0.01, y_m + 0.1, 0.04, 0.062, 12)
    dx, dz = OUT[side]
    off = 0.14 * M
    return _light(ctx, floor, "Lamp.%s.%d" % (room, n), "POINT", x + dx * off, z + dz * off, y_m + 0.18,
                  power, radius=0.05, room=room)


def washer(ctx, kit, floor, room, n, x, z, side, y_m=2.1, power=30.0):
    """Wall washer: a slim box on the wall with glowing slots top and bottom,
    throwing light up and down the wall (two spots)."""
    rot = FACING[side]
    kit.at(x, z, rot)
    kit.box("Black Steel", 0, -0.04, y_m, 0.12, 0.08, 0.16)
    kit.box("Lamp Glow", 0, -0.045, y_m + 0.081, 0.1, 0.06, 0.004)
    kit.box("Lamp Glow", 0, -0.045, y_m - 0.081, 0.1, 0.06, 0.004)
    dx, dz = OUT[side]
    off = 0.11 * M
    lx, lz = x + dx * off, z + dz * off
    up = _light(ctx, floor, "Lamp.%s.%d.up" % (room, n), "SPOT", lx, lz, y_m + 0.1, power,
                radius=0.03, up=True, spot_deg=110, room=room)
    dn = _light(ctx, floor, "Lamp.%s.%d.down" % (room, n), "SPOT", lx, lz, y_m - 0.1, power,
                radius=0.03, spot_deg=110, room=room)
    return [up, dn]


def festoon_lights(ctx, power=8.0, every=1):
    """Point lights in the festoon bulbs: one per `every` bulbs, at the bulb
    centres (islands of the LampGlow mesh terrace_evening.py made)."""
    ob = bpy.data.objects.get("second.TerraceEvening.LampGlow")
    if ob is None:
        ctx["helpers"]["warn"]("room_lights: no festoon mesh second.TerraceEvening.LampGlow")
        return []
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    seen, centres = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        stack, pts = [v], []
        seen.add(v)
        while stack:
            a = stack.pop()
            pts.append(a.co.copy())
            for e in a.link_edges:
                b = e.other_vert(a)
                if b not in seen:
                    seen.add(b)
                    stack.append(b)
        centres.append(sum(pts, Vector()) / len(pts))
    bm.free()
    # Sort along the terrace (floor-local blender y = -z) so "every second" is spatial.
    centres.sort(key=lambda c: (c.y, c.x))
    lights = []
    for i, c in enumerate(centres[::every]):
        lo = ob.matrix_basis @ c          # mesh is in the empty's frame (identity basis)
        data = bpy.data.lights.new("Lamp.terrace.%d" % i, type="POINT")
        data.energy = power
        if hasattr(data, "temperature") and hasattr(data, "use_temperature"):
            data.use_temperature = True
            data.temperature = KELVIN
        else:
            data.color = WARM
        data.shadow_soft_size = 0.03
        lo_ob = bpy.data.objects.new(data.name, data)
        ctx["colls"]["second"].objects.link(lo_ob)
        lo_ob.parent = ctx["empties"]["second"]
        lo_ob.matrix_parent_inverse = Matrix.Identity(4)
        lo_ob.location = lo - Vector((0, 0, 0.06 * M))   # just under the bulb
        lo_ob.scale = (M, M, M)
        lo_ob["club_lamp"] = 1
        lo_ob["club_lamp_room"] = "terrace"
        lights.append(lo_ob)
    ctx["helpers"]["info"]("room_lights: festoon %d bulbs, %d lights" % (len(centres), len(lights)))
    return lights


def build(ctx):
    info = ctx["helpers"]["info"]
    lights = []

    # ---- Café, Living 1 (ground)
    k = F.Kit(ctx, "ground", "ground.RoomLights")
    wall = lambda x, z, side, h=2.0: F.wall(ctx, "ground", x, z, side, h=h)
    lw = wall(1.2, 1.55, "west")
    lights.append(sconce(ctx, k, "ground", "cafe", 0, lw, 1.55, "west", y_m=2.0))
    lw2 = wall(1.2, 3.0, "west")
    lights.append(sconce(ctx, k, "ground", "cafe", 1, lw2, 3.0, "west", y_m=2.0))
    le = wall(1.8, 2.35, "east")
    for i, z in enumerate((2.35, 2.7)):
        lights.append(sconce(ctx, k, "ground", "cafe", 2 + i, le, z, "east", y_m=1.75))
    k.done()

    # ---- Court and event space (first)
    k = F.Kit(ctx, "first", "first.RoomLights")
    wall = lambda x, z, side, h=2.0: F.wall(ctx, "first", x, z, side, h=h)
    for i, z in enumerate((0.75, 1.25)):          # piers between the louvred bays
        ce = wall(1.9, z, "east", h=2.0)
        lights.append(sconce(ctx, k, "first", "court", i, ce, z, "east", y_m=2.05))
    cn = wall(2.35, 0.9, "north", h=1.0)           # east of the olive; ray under its crown
    lights.append(sconce(ctx, k, "first", "court", 2, 2.35, cn, "north", y_m=2.05))
    ew = wall(1.5, 3.05, "west")
    ee = wall(1.5, 3.05, "east")
    for i, z in enumerate((2.3, 3.85)):
        lights += washer(ctx, k, "first", "event", i, ew, z, "west", y_m=2.15)
    for i, z in enumerate((2.45, 3.65)):
        lights += washer(ctx, k, "first", "event", 2 + i, ee, z, "east", y_m=2.3)
    k.done()

    # ---- Basement office
    k = F.Kit(ctx, "basement", "basement.RoomLights")
    wall = lambda x, z, side, h=2.0: F.wall(ctx, "basement", x, z, side, h=h)
    on = wall(0.25, 0.4, "north")
    lights += washer(ctx, k, "basement", "office", 0, 0.25, on, "north", y_m=2.0)
    oe = wall(1.0, 0.65, "east")
    lights += washer(ctx, k, "basement", "office", 1, oe, 0.65, "east", y_m=2.0)
    os_ = wall(0.55, 1.2, "south")
    lights += washer(ctx, k, "basement", "office", 2, 0.55, os_, "south", y_m=2.0)
    k.done()

    # ---- Terrace (second): sconces on the house wall, the festoon
    k = F.Kit(ctx, "second", "second.RoomLights")
    for i, z in enumerate((1.3,)):           # z -0.6 is the recessed doorway
        te = F.wall(ctx, "second", -1.6, z, "east", h=2.0)
        if te < -0.9:                       # solid house wall, not an opening
            lights.append(sconce(ctx, k, "second", "terrace", 10 + i, te, z, "east", y_m=2.0))
        else:
            ctx["helpers"]["warn"]("room_lights: terrace wall at z %.2f is open (%.3f); no sconce" % (z, te))
    k.done()
    lights += festoon_lights(ctx)

    info("room_lights: %d lights; cafe w %.3f/%.3f e %.3f, court n %.3f, event w %.3f e %.3f, office n %.3f e %.3f s %.3f"
         % (len(lights), lw, lw2, le, cn, ew, ee, on, oe, os_))
    return []
