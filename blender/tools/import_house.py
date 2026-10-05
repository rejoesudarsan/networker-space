import bpy, json, math
# clear
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
for c in list(bpy.data.collections): bpy.data.collections.remove(c)
M="/home/bb/projects/networker-space/site/public/models/"
house=json.load(open(M+"house.json"))
LEVEL={"basement":-0.72,"ground":0.73,"first":2.18,"second":3.63}
for fid,y in LEVEL.items():
    col=bpy.data.collections.new(fid); bpy.context.scene.collection.children.link(col)
    before=set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=M+fid+".glb")
    new=[o for o in bpy.data.objects if o not in before]
    ox,oz=house["floors"][fid]["offset"]
    root=bpy.data.objects.new(fid+"_root",None); col.objects.link(root)
    root.location=(ox,-oz,y)
    for o in new:
        for c in o.users_collection: c.objects.unlink(o)
        col.objects.link(o)
        if o.parent is None: o.parent=root
    print(fid, [(o.name,o.type, tuple(round(v,2) for v in o.dimensions)) for o in new][:8])
# camera + light
cam=bpy.data.objects.new("Cam",bpy.data.cameras.new("Cam")); bpy.context.scene.collection.objects.link(cam)
cam.location=(14,-16,11); cam.rotation_euler=(math.radians(62),0,math.radians(40)); cam.data.lens=35
bpy.context.scene.camera=cam
sun=bpy.data.objects.new("Sun",bpy.data.lights.new("Sun",'SUN')); bpy.context.scene.collection.objects.link(sun)
sun.rotation_euler=(math.radians(50),math.radians(10),math.radians(30)); sun.data.energy=3
# frame viewport
for a in bpy.context.screen.areas:
    if a.type=='VIEW_3D':
        r3=a.spaces.active.region_3d
        r3.view_location=(0,0,2); r3.view_distance=22; r3.view_rotation=cam.rotation_euler.to_quaternion()
        a.spaces.active.shading.type='SOLID'
print("objects:", len(bpy.data.objects))
