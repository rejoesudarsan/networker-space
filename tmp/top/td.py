"""Straight-down orthographic render of one floor, to measure wall positions.
  /snap/bin/blender -b blender/space-house.blend --python blender/tools/topdown.py -- <floor> <cx>,<cz>,<half>
Centre (cx, cz) and half-width in that floor's Three.js units; writes /Users/rejoesudarsan/Dev/networker-space/tmp/top/basement 0,0,4.png.
Pixel to units: X = cx + (px - 450) * 2 * half / 900, Z = cz + (py - 450) * 2 * half / 900."""
import bpy, sys
from mathutils import Vector
args=sys.argv[sys.argv.index("--")+1:]
floor=args[0]; cx,cz,half=[float(v) for v in args[1].split(",")]
sc=bpy.context.scene; order=["basement","ground","first","second"]
for k in order[order.index(floor)+1:]:
    bpy.data.collections[k.capitalize()].hide_render=True
bpy.data.collections["Roof"].hide_render=True
for o in bpy.data.objects:
    if "fog" in o.name.lower(): o.hide_render=True
e=bpy.data.objects["Floor.%s"%floor]
p=e.matrix_world @ Vector((cx,-cz,0))
cam=bpy.data.objects.new("T",bpy.data.cameras.new("T")); sc.collection.objects.link(cam); sc.camera=cam
cam.data.type="ORTHO"; cam.data.ortho_scale=half*2*2.4384
cam.location=(p.x,p.y,p.z+30); cam.rotation_euler=(0,0,0)
sc.render.engine="BLENDER_WORKBENCH"; sh=sc.display.shading; sh.light="STUDIO"; sh.color_type="MATERIAL"; sh.show_cavity=True
sc.render.resolution_x=sc.render.resolution_y=900; sc.render.resolution_percentage=100
sc.render.filepath="/Users/rejoesudarsan/Dev/networker-space/tmp/top/basement 0,0,4.png"; bpy.ops.render.render(write_still=True)
