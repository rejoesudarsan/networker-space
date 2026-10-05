"""Quick render of the saved scene from a named camera, or a close-up of
one object, for checking site-level details (trees, street, lamps).

  Blender -b blender/space-house.blend --python blender/tools/street_shot.py -- \
      [--cam Camera.Street] [--focus Site.Gulmohar.0] [--engine eevee|cycles] \
      [--samples 32] [--night] [--out name]

--focus frames a new camera on every object whose name starts with the given
prefix, from the street side and a little above. --night turns the sun off
and the sky down, as bake_site's night set does. Writes
blender/renders/street-<out>.png. Nothing is saved."""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.dirname(HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default):
    return args[args.index(name) + 1] if name in args else default


scene = bpy.context.scene
focus = opt("--focus", None)
if focus:
    objs = [o for o in bpy.data.objects if o.name.startswith(focus) and o.type == "MESH"]
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = (lo + hi) / 2
    span = max(hi.x - lo.x, hi.z - lo.z)
    cam = bpy.data.objects.new("Camera.Focus", bpy.data.cameras.new("Camera.Focus"))
    scene.collection.objects.link(cam)
    cam.data.lens = 50
    el = math.radians(float(opt("--el", 8)))
    d = Vector((0, -math.cos(el), math.sin(el)))
    cam.location = centre + d * span * float(opt("--dist", 2.3))
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
else:
    scene.camera = bpy.data.objects[opt("--cam", "Camera.Street")]

if "--night" in args:
    sun = bpy.data.objects.get("Sun.Dawn")
    if sun:
        sun.hide_render = True
    w = scene.world
    for n in (w.node_tree.nodes if w and w.node_tree else []):
        if n.type == "BACKGROUND":
            n.inputs["Strength"].default_value *= 0.04

engine = opt("--engine", "eevee")
scene.render.resolution_x, scene.render.resolution_y = 1280, 860
scene.render.resolution_percentage = 100
if engine == "cycles":
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
        print("[street] no GPU: %s" % e)
else:
    scene.render.engine = "BLENDER_EEVEE"
    try:
        scene.eevee.taa_render_samples = int(opt("--samples", 32))
    except Exception:
        pass

out = os.path.join(BLENDER_DIR, "renders", "street-%s.png" % opt("--out", "street"))
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("[street] wrote %s" % out)
