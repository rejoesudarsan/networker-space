"""topdown.py after building one detail module: -- <module> <floor> <cx>,<cz>,<half>"""
import bpy, sys, importlib
BL="/home/bb/projects/networker-space/blender"
src=open(BL+"/build_house.py").read().replace("\nmain()\n","\n")
ns={"__file__":BL+"/build_house.py","__name__":"lib"}; exec(compile(src,"bh","exec"),ns)
sys.path.insert(0,BL)
import __main__
for k,v in ns.items():
    if callable(v) and not hasattr(__main__,k): setattr(__main__,k,v)
colls={k:bpy.data.collections[ns["COLLECTION_FOR"][k]] for k in ns["FLOOR_ORDER"]}
ctx=dict(scene=bpy.context.scene, mats={m.name:m for m in bpy.data.materials},
  empties={k:bpy.data.objects["Floor.%s"%k] for k in ns["FLOOR_ORDER"]}, colls=colls,
  site=bpy.data.collections["Site"], house=bpy.data.collections["House"], roof_coll=bpy.data.collections.get("Roof"),
  helpers={k:ns[k] for k in ("add_box","add_slab","get_collection","set_parent","three_rect_to_blender","new_material","link_only","info","warn")},
  constants={k:ns[k] for k in ("UNIT_M","SLAB_T","STOREY","WALL_H","FLOORS","PARAPET_H","PARAPET_T","TERRACE_X1","SLAB_VOIDS")})
a=sys.argv[sys.argv.index("--")+1:]
mod=importlib.import_module("details."+a[0]); mod.build(ctx)
if hasattr(mod,"finish"): mod.finish(ctx)
sys.argv=[sys.argv[0],"--"]+a[1:]
exec(open(BL+"/tools/topdown.py").read())
