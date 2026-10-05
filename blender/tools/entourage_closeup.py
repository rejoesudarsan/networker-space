"""Close-up of some entourage.blend collections, side by side.

  /snap/bin/blender -b blender/entourage.blend --python blender/tools/entourage_closeup.py -- <name> [<name> ...] [--dir sx,sy,sz] [--out file.png]

Each name is a collection (exact, or a prefix such as Bike.Scooter). Renders
a Workbench view to blender/renders/entourage-closeup.png."""
import math
import os
import sys

import bpy
from mathutils import Vector

BL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
view = Vector((0.0, 1.0, -0.15))      # camera looks along this; default from the -Y side, +X to the right
out = os.path.join(BL, "renders", "entourage-closeup.png")
names = []
i = 0
while i < len(args):
    if args[i] == "--dir":
        view = Vector(float(v) for v in args[i + 1].split(","))
        i += 2
    elif args[i] == "--out":
        out = args[i + 1]
        i += 2
    else:
        names.append(args[i])
        i += 1

scene = bpy.context.scene
for lc in bpy.context.view_layer.layer_collection.children:
    lc.exclude = True
colls = [c for c in bpy.data.collections if any(c.name == n or c.name.startswith(n + ".") for n in names)
         and c.objects]
x = 0.0
lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
for c in colls:
    ob = bpy.data.objects.new("I." + c.name, None)
    ob.instance_type = "COLLECTION"
    ob.instance_collection = c
    scene.collection.objects.link(ob)
    pts = [o.matrix_world @ Vector(b) for o in c.objects for b in o.bound_box]
    w = max(p.x for p in pts) - min(p.x for p in pts)
    ob.location = (x, 0, 0)
    for p in pts:
        q = p + Vector((x, 0, 0))
        lo = Vector(map(min, lo, q))
        hi = Vector(map(max, hi, q))
    x += w + 0.4
    print("[closeup]", c.name, [round(max(p[k] for p in pts) - min(p[k] for p in pts), 2) for k in range(3)])
centre = (lo + hi) / 2
r = (hi - lo).length
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
scene.collection.objects.link(cam)
d = view.normalized()
cam.location = centre - d * r * 2
cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
cam.data.type = "ORTHO"
cam.data.ortho_scale = max(hi.x - lo.x, hi.z - lo.z) + 0.4
scene.camera = cam
scene.render.engine = "BLENDER_WORKBENCH"
scene.display.shading.light = "STUDIO"
scene.display.shading.color_type = "MATERIAL"
scene.display.shading.show_shadows = True
scene.render.resolution_x = 1400
scene.render.resolution_y = max(400, int(1400 * (hi.z - lo.z + 0.4) / (hi.x - lo.x + 0.4)))
scene.render.filepath = out
bpy.ops.render.render(write_still=True)
print("[closeup] wrote", out)
