"""Close-up of one room with everything above it removed, for checking a
fit-out the way the site shows it (an open-topped diorama).

  Blender -b blender/space-house.blend --python blender/tools/room_shot.py -- \
      <floor> <x0>,<z0>,<x1>,<z1> [--module cafe] [--az 20] [--el 38] [--engine eevee|cycles|workbench] \
      [--samples 32] [--out name]

The rectangle is in that floor's Three.js plan units. --module rebuilds a
detail module first (as preview.py does) so unsaved edits show. The camera
looks at the rectangle from the street side (azimuth in degrees, 0 = from
the street, positive = from the east) at elevation --el, framed to fit.
Writes blender/renders/room-<out or floor>.png."""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.dirname(HERE)
args = sys.argv[sys.argv.index("--") + 1:]
floor = args[0]
x0, z0, x1, z1 = [float(v) for v in args[1].split(",")]


def opt(name, default):
    return args[args.index(name) + 1] if name in args else default


src = open(os.path.join(BLENDER_DIR, "build_house.py")).read().replace("\nmain()\n", "\n")
ns = {"__file__": os.path.join(BLENDER_DIR, "build_house.py"), "__name__": "build_house_lib"}
exec(compile(src, "build_house.py", "exec"), ns)
sys.path.insert(0, BLENDER_DIR)
import __main__
for k, v in ns.items():
    if callable(v) and not hasattr(__main__, k):
        setattr(__main__, k, v)

scene = bpy.context.scene
order = ns["FLOOR_ORDER"]
colls = {k: bpy.data.collections[ns["COLLECTION_FOR"][k]] for k in order}

for mod_name in [a for i, a in enumerate(args) if i and args[i - 1] == "--module"]:
    import importlib
    # Drop what a previous build of this module left in the saved scene.
    for o in list(bpy.data.objects):
        if o.name.startswith("%s.%s" % (floor, mod_name.title().replace("_", ""))):
            bpy.data.objects.remove(o)
    ctx = dict(
        scene=scene, mats={m.name: m for m in bpy.data.materials},
        empties={k: bpy.data.objects["Floor.%s" % k] for k in order}, colls=colls,
        site=bpy.data.collections["Site"], house=bpy.data.collections["House"],
        roof_coll=bpy.data.collections.get("Roof"),
        helpers={k: ns[k] for k in ("add_box", "add_slab", "get_collection", "set_parent",
                                    "three_rect_to_blender", "new_material", "link_only", "info", "warn")},
        constants={k: ns[k] for k in ("UNIT_M", "SLAB_T", "STOREY", "WALL_H", "FLOORS", "PARAPET_H",
                                      "PARAPET_T", "TERRACE_X1", "SLAB_VOIDS")},
    )
    before = set(bpy.data.objects)
    mod = importlib.import_module("details." + mod_name)
    mod.build(ctx)
    bpy.context.view_layer.update()
    for o in set(bpy.data.objects) - before:
        if o.type == "MESH" and "BoxUV" not in o.data.uv_layers:
            ns["box_uv"](o.data, o.matrix_world.to_scale()[0])

# Everything above this floor goes, as in the site's diorama.
for k in order[order.index(floor) + 1:]:
    colls[k].hide_render = True
if bpy.data.collections.get("Roof") is not None:
    bpy.data.collections["Roof"].hide_render = True
for o in bpy.data.objects:
    n = o.name.lower()
    if "fog" in n or "haze" in n:
        o.hide_render = True

empty = bpy.data.objects["Floor.%s" % floor]
U = ns["UNIT_M"]
c_local = Vector(((x0 + x1) / 2, -(z0 + z1) / 2, ns["WALL_H"] * 0.35))
centre = empty.matrix_world @ c_local
span = max(x1 - x0, z1 - z0) * U
az = math.radians(float(opt("--az", 20)))
el = math.radians(float(opt("--el", 38)))
lens = float(opt("--lens", 35))
d = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
fov = 2 * math.atan(18 / lens)
dist = span * 0.62 / math.tan(fov / 2) + span * 0.15

cam = bpy.data.objects.new("Camera.Room", bpy.data.cameras.new("Camera.Room"))
scene.collection.objects.link(cam)
cam.data.lens = lens
cam.data.clip_end = 2000
cam.location = centre + d * dist
cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
scene.camera = cam
if "--top" in args:
    # Straight down, orthographic, the rectangle filling the frame: for
    # measuring. Pixel -> plan: x = x0 + px / W * (x1 - x0), z = z0 + py / H * (z1 - z0).
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = max(x1 - x0, (z1 - z0) * 1280 / 860) * U
    cam.location = empty.matrix_world @ Vector(((x0 + x1) / 2, -(z0 + z1) / 2, 6.0))
    cam.rotation_euler = (0, 0, 0)

engine = opt("--engine", "eevee")
scene.render.resolution_x, scene.render.resolution_y = 1280, 860
scene.render.resolution_percentage = 100
if engine == "workbench":
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light, sh.color_type, sh.show_shadows, sh.show_cavity = "STUDIO", "MATERIAL", True, True
elif engine == "cycles":
    scene.render.engine = "CYCLES"
    scene.cycles.samples = int(opt("--samples", 64))
    scene.cycles.use_denoising = True
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = True
        scene.cycles.device = "GPU"
    except Exception as e:
        print("[room] no GPU: %s" % e)
else:
    scene.render.engine = "BLENDER_EEVEE"
    try:
        scene.eevee.taa_render_samples = int(opt("--samples", 32))
        scene.eevee.use_raytracing = True
    except Exception:
        pass
# The compositor fog would grey out a close-up.
scene.render.use_compositing = False

out = os.path.join(BLENDER_DIR, "renders", "room-%s.png" % opt("--out", floor))
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("[room] wrote %s" % out)
