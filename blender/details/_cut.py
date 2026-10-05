"""Boolean box cuts on existing meshes, applied in place (no bpy.ops)."""
import bmesh
import bpy
from mathutils import Matrix


def cut_box(ctx, obj_name, x0, x1, y0, y1, z0, z1):
    """Cut an axis-aligned box out of obj_name. Coordinates are in the object's
    parent space (the floor Empty's units), Blender axes. Returns True if cut."""
    ob = bpy.data.objects.get(obj_name)
    if ob is None or ob.type != "MESH":
        ctx["helpers"]["warn"]("cut_box: no mesh %s" % obj_name)
        return False
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    me = bpy.data.meshes.new("_cutter")
    bm.to_mesh(me)
    bm.free()
    cutter = bpy.data.objects.new("_cutter", me)
    ctx["scene"].collection.objects.link(cutter)
    cutter.parent = ob.parent
    cutter.matrix_parent_inverse = Matrix.Identity(4)
    cutter.location = ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
    cutter.scale = (x1 - x0, y1 - y0, z1 - z0)
    mod = ob.modifiers.new("_cut", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    try:
        mod.solver = "EXACT"
    except Exception:
        pass
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    new_me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.remove(mod)
    old = ob.data
    ob.data = new_me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    bpy.data.objects.remove(cutter, do_unlink=True)
    bpy.data.meshes.remove(me)
    return True
