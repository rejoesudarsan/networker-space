"""Fast close-up preview of one detail module, before the full build.

  /snap/bin/blender -b blender/space-house.blend --python blender/tools/preview.py -- <module> [--dir sx,sy,sz] [--cut <floor>]

Loads the last saved scene, runs only blender/details/<module>.py, frames a
camera on the objects it created and renders two Workbench close-ups (a few
seconds each) to blender/renders/preview-<module>-1.png and -2.png. Nothing is
saved. --dir sets the first camera's viewing direction (default: from the
street, south-west, above)."""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.dirname(HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args:
    raise SystemExit("usage: preview.py -- <module> [--dir sx,sy,sz]")
module = args[0]
view_dir = Vector((-0.6, -1.0, 0.7))
if "--dir" in args:
    view_dir = Vector(float(v) for v in args[args.index("--dir") + 1].split(","))

# Load build_house's helpers and constants without running its main()
src = open(os.path.join(BLENDER_DIR, "build_house.py")).read()
src = src.replace("\nmain()\n", "\n")
ns = {"__file__": os.path.join(BLENDER_DIR, "build_house.py"), "__name__": "build_house_lib"}
exec(compile(src, "build_house.py", "exec"), ns)
sys.path.insert(0, BLENDER_DIR)

scene = bpy.context.scene
colls = {k: bpy.data.collections[ns["COLLECTION_FOR"][k]] for k in ns["FLOOR_ORDER"]}
ctx = dict(
    scene=scene,
    mats={m.name: m for m in bpy.data.materials},
    empties={k: bpy.data.objects["Floor.%s" % k] for k in ns["FLOOR_ORDER"]},
    colls=colls, site=bpy.data.collections["Site"], house=bpy.data.collections["House"],
    roof_coll=bpy.data.collections.get("Roof"),
    helpers={k: ns[k] for k in ("add_box", "add_slab", "get_collection", "set_parent",
                                "three_rect_to_blender", "new_material", "link_only", "info", "warn")},
    constants={k: ns[k] for k in ("UNIT_M", "SLAB_T", "STOREY", "WALL_H", "FLOORS", "PARAPET_H",
                                  "PARAPET_T", "TERRACE_X1", "SLAB_VOIDS")},
)
# The build script exposes mesh_islands etc. through __main__; mirror that here
import __main__
for k, v in ns.items():
    if callable(v) and not hasattr(__main__, k):
        setattr(__main__, k, v)

import importlib
before = set(bpy.data.objects)
mod = importlib.import_module("details." + module)
mod.build(ctx)
if hasattr(mod, "finish"):
    mod.finish(ctx)
bpy.context.view_layer.update()
new = [o for o in bpy.data.objects if o not in before and o.type in {"MESH", "CURVE"}]
print("[preview] %s: %d new objects" % (module, len(new)))
if not new:
    raise SystemExit("[preview] nothing was created")

# World-space bounds of what was added
pts = [o.matrix_world @ Vector(c) for o in new for c in o.bound_box]
lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
centre, size = (lo + hi) / 2, max((hi - lo).length, 1.0)
print("[preview] bounds (m): %s .. %s" % (tuple(round(v, 2) for v in lo), tuple(round(v, 2) for v in hi)))

# Cutaway: hide every floor above --cut, and the roof
if "--cut" in args:
    order = ns["FLOOR_ORDER"]
    keep = args[args.index("--cut") + 1]
    for k in order[order.index(keep) + 1:]:
        colls[k].hide_render = True
    roof = bpy.data.collections.get("Roof")
    if roof:
        roof.hide_render = True
    print("[preview] cutaway above %s" % keep)

# Hide haze so the close-up reads
for o in bpy.data.objects:
    if "fog" in o.name.lower() or "haze" in o.name.lower():
        o.hide_render = True

cam = bpy.data.objects.new("Camera.Preview", bpy.data.cameras.new("Camera.Preview"))
scene.collection.objects.link(cam)
cam.data.lens = 35
cam.data.clip_end = 1000
scene.camera = cam

scene.render.engine = "BLENDER_WORKBENCH"
sh = scene.display.shading
sh.light = "STUDIO"
sh.color_type = "MATERIAL"
sh.show_shadows = True
sh.show_cavity = True
sh.show_object_outline = True
scene.render.resolution_x, scene.render.resolution_y = 1200, 800
scene.render.resolution_percentage = 100
scene.render.film_transparent = False

# Highlight the new objects in the second view by selecting them is not rendered,
# so instead render one framed view and one wider context view.
out = os.path.join(BLENDER_DIR, "renders")
os.makedirs(out, exist_ok=True)
for i, (d, dist_k) in enumerate(((view_dir, 1.1), (Vector((0.5, -1.0, 0.5)), 2.2)), start=1):
    d = d.normalized()
    cam.location = centre + d * size * dist_k
    cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = os.path.join(out, "preview-%s-%d.png" % (module, i))
    bpy.ops.render.render(write_still=True)
    print("[preview] wrote %s" % scene.render.filepath)
