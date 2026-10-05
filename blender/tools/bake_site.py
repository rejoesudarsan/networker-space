"""Bake the house's light into textures for the website, one atlas per floor.

  Blender -b blender/space-house.blend --python blender/tools/bake_site.py -- \
      [--floors ground,first] [--set day] [--res 2048] [--samples 128] [--exposure 0]

For each floor: every mesh the build put under Floor.<floor> (walls, slab,
finishes, every detail and fit-out module, modifiers applied) is joined in
world space into one object, given a second, non-overlapping UV map
("Lightmap", Smart UV Project) and baked in Cycles as Diffuse (direct +
indirect + colour), which holds the materials' colour and texture times the
light that falls on them, independent of the viewing angle. Glass and
emissive lamps are left out of the bake and exported with flat materials.

The bake is lit the way the site shows a floor: the floors above and the
roof are hidden (the site sees every room open-topped), the floors below and
the street stay for bounce light. --set picks the light: "day" (high warm
sun, the sky HDRI) or "night" (sun off, a low blue sky, the house's lamps
and glow materials on).

Writes site/public/models/baked/<floor>-<set>.gltf (+ .bin), its atlas
<floor>-<set>.jpg (the scene's view transform and --exposure applied, so the
site shows it as is, unlit), and <floor>-fixtures.gltf (glass + lamps).
Coordinates are the floor's local Three.js units, slab top at y = 0, as
export_site.py.
"""
import math
import os
import re
import sys
import time

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.dirname(HERE)
OUT = os.path.join(os.path.dirname(BLENDER_DIR), "site", "public", "models", "baked")
FLOORS = ["basement", "ground", "first", "second"]
EXTRA = ["roof", "site"]           # roof: second floor's frame; site: the street frame (Site.Units)
SKIP = ("details",)                 # CAD plan lines

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default):
    return args[args.index(name) + 1] if name in args else default


floors = opt("--floors", "" if "--rooms" in args else ",".join(FLOORS + EXTRA)).split(",")
light_set = opt("--set", "day")
RES = int(opt("--res", 2048))
SAMPLES = int(opt("--samples", 128))
EXPOSURE = float(opt("--exposure", -0.4))


def log(msg):
    print("[bake] %s" % msg, flush=True)


def under(o, root):
    p = o.parent
    while p is not None:
        if p == root:
            return True
        if p.name == "Floor.roof":
            return False
        p = p.parent
    return False


def under_name(o, name):
    p = o.parent
    while p is not None:
        if p.name == name:
            return True
        p = p.parent
    return False


def bsdf_of(m):
    if m is None or not m.node_tree:
        return None
    return next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)


def kind_of(m):
    """'glass', 'glow' or 'bake'."""
    if m is None:
        return "bake"
    b = bsdf_of(m)
    name = m.name.lower()
    if "glass" in name and "block" not in name:
        return "glass"
    if b is not None:
        tr = b.inputs.get("Transmission Weight") or b.inputs.get("Transmission")
        if tr is not None and not tr.is_linked and tr.default_value > 0.5:
            return "glass"
        es = b.inputs.get("Emission Strength")
        ec = b.inputs.get("Emission Color") or b.inputs.get("Emission")
        if es is not None and es.default_value > 0 and ec is not None and max(ec.default_value[:3]) > 0.01:
            return "glow"
    return "bake"


# ---------------------------------------------------------------- light sets

def set_light(kind):
    sc = bpy.context.scene
    sun = bpy.data.objects.get("Sun.Dawn")
    world = sc.world
    bgs = [n for n in world.node_tree.nodes if n.type == "BACKGROUND"] if world and world.node_tree else []
    if kind == "day":
        if sun:
            sun.hide_render = False
            # High, warm late-morning sun from the south-east.
            sun.rotation_euler = (math.radians(90 - 52), 0, math.radians(180 - 135))
            sun.data.energy = 3.2
            sun.data.color = (1.0, 0.93, 0.84)
        for n in bgs:
            n.inputs["Strength"].default_value = n.inputs["Strength"].default_value * 1.0
    else:
        if sun:
            sun.hide_render = True
        for n in bgs:
            n.inputs["Strength"].default_value *= 0.04
        for m in bpy.data.materials:
            b = bsdf_of(m)
            if b is None or kind_of(m) != "glow":
                continue
            b.inputs["Emission Strength"].default_value *= 6.0


def set_cycles():
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = False
    # Metal on the Mac, CUDA/OptiX/HIP on a GPU server, else the CPU (Hetzner).
    sc.cycles.device = "CPU"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = kind
            except TypeError:
                continue
            prefs.get_devices()
            gpus = [d for d in prefs.devices if d.type != "CPU"]
            if gpus:
                for d in prefs.devices:
                    d.use = True
                sc.cycles.device = "GPU"
                log("GPU (%s): %s" % (kind, ", ".join(d.name for d in gpus)))
                break
        else:
            log("CPU: no GPU device")
    except Exception as e:
        log("CPU (%s)" % e)
    sc.render.bake.margin = 8
    sc.render.bake.margin_type = "EXTEND"
    sc.render.bake.use_pass_direct = True
    sc.render.bake.use_pass_indirect = True
    sc.render.bake.use_pass_color = True


# ---------------------------------------------------------------- joining

def joined(objs, name):
    """World-space copies of the evaluated meshes, joined into one object."""
    dg = bpy.context.evaluated_depsgraph_get()
    import __main__
    box_uv = getattr(__main__, "box_uv", None)
    tmp = []
    coll = bpy.context.scene.collection
    for o in objs:
        ev = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev)
        if not me.polygons:
            bpy.data.meshes.remove(me)
            continue
        me.transform(o.matrix_world)
        if "BoxUV" not in me.uv_layers and box_uv is not None:
            box_uv(me, 1.0)
        # Keep only BoxUV so the join lines layers up by name.
        for uv in list(me.uv_layers):
            if uv.name != "BoxUV":
                me.uv_layers.remove(uv)
        if not me.materials:
            me.materials.append(bpy.data.materials.get("Lime White"))
        t = bpy.data.objects.new("tmp." + o.name, me)
        coll.objects.link(t)
        tmp.append(t)
    if not tmp:
        return None
    bpy.ops.object.select_all(action="DESELECT")
    for t in tmp:
        t.select_set(True)
    bpy.context.view_layer.objects.active = tmp[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = name
    ob.data.name = name
    for p in ob.data.polygons:
        p.use_smooth = False
    return ob


def split_by_kind(ob):
    """Separate glass and glow faces off into their own objects."""
    me = ob.data
    kinds = [kind_of(m) for m in me.materials]
    out = {}
    for k in ("glass", "glow"):
        idx = {i for i, kk in enumerate(kinds) if kk == k}
        if not idx:
            continue
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.mode_set(mode="OBJECT")
        n = 0
        for p in me.polygons:
            if p.material_index in idx:
                p.select = True
                n += 1
        if not n:
            continue
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.separate(type="SELECTED")
        bpy.ops.object.mode_set(mode="OBJECT")
        part = [o for o in bpy.context.selected_objects if o != ob][0]
        part.name = "%s.%s" % (ob.name, k)
        out[k] = part
    return out


def lightmap_uv(ob):
    me = ob.data
    uv = me.uv_layers.new(name="Lightmap")
    me.uv_layers.active = uv
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    t = time.time()
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    # Pack with a real margin in texels so the bake margin can't bleed across islands.
    try:
        bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=True, margin_method="FRACTION",
                                margin=4.0 / RES, shape_method="CONCAVE")
    except TypeError:
        bpy.ops.uv.pack_islands(rotate=True, margin=4.0 / RES)
    bpy.ops.object.mode_set(mode="OBJECT")
    log("lightmap UVs for %d faces in %.1f s" % (len(me.polygons), time.time() - t))


# ---------------------------------------------------------------- bake + export

def bake(ob, img):
    """Point every material on ob at img (as copies, so the house's own
    materials are untouched) and bake Diffuse into it."""
    me = ob.data
    for i, m in enumerate(me.materials):
        m = m or bpy.data.materials["Lime White"]
        c = m.copy()
        c.name = "bake.%s" % m.name
        nt = c.node_tree
        node = nt.nodes.new("ShaderNodeTexImage")
        node.image = img
        uvn = nt.nodes.new("ShaderNodeUVMap")
        uvn.uv_map = "Lightmap"
        nt.links.new(uvn.outputs["UV"], node.inputs["Vector"])
        for n in nt.nodes:
            n.select = False
        node.select = True
        nt.nodes.active = node
        me.materials[i] = c
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    t = time.time()
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"DIRECT", "INDIRECT", "COLOR"}, use_clear=True,
                        margin=8, target="IMAGE_TEXTURES")
    log("baked %s in %.0f s" % (ob.name, time.time() - t))


def export(objs, path, root):
    """Export copies of objs in root's local frame (Three.js floor units)."""
    sc = bpy.data.scenes.new("export")
    inv = root.matrix_world.inverted()
    for o in objs:
        me = o.data.copy()
        me.transform(inv)
        c = bpy.data.objects.new(o.name, me)
        sc.collection.objects.link(c)
    win = bpy.context.window
    prev = bpy.context.window.scene if win else None
    if win:
        win.scene = sc
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE", use_active_scene=True,
                              export_apply=False, export_yup=True, export_cameras=False, export_lights=False,
                              export_extras=True, export_texture_dir="", export_image_format="JPEG",
                              export_jpeg_quality=88, export_keep_originals=True)
    if win:
        win.scene = prev
    log("wrote %s (%.0f KB)" % (path, os.path.getsize(path) / 1024))


def denoise(img):
    """Run the baked image through the compositor's Denoise node (OIDN) in a
    throwaway Workbench scene; returns the denoised render result path."""
    sc = bpy.data.scenes.new("denoise")
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = img.size
    sc.render.resolution_percentage = 100
    sc.render.use_compositing = True
    sc.view_settings.view_transform = "Standard"
    try:
        tree = bpy.data.node_groups.new("denoise", "CompositorNodeTree")
        sc.compositing_node_group = tree
        tree.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        out = tree.nodes.new("NodeGroupOutput")
    except AttributeError:
        sc.use_nodes = True
        tree = sc.node_tree
        tree.nodes.clear()
        out = tree.nodes.new("CompositorNodeComposite")
    src = tree.nodes.new("CompositorNodeImage")
    src.image = img
    dn = tree.nodes.new("CompositorNodeDenoise")
    try:
        dn.prefilter = "ACCURATE"
    except Exception:
        pass
    tree.links.new(src.outputs["Image"], dn.inputs["Image"])
    tree.links.new(dn.outputs["Image"], out.inputs[0])
    bpy.ops.render.render(scene=sc.name)
    res = bpy.data.images["Render Result"]
    path = os.path.join(bpy.app.tempdir, "denoised.exr")
    sc.render.image_settings.file_format = "OPEN_EXR"
    sc.render.image_settings.color_depth = "32"
    res.save_render(path, scene=sc)
    bpy.data.scenes.remove(sc)
    clean = bpy.data.images.load(path)
    clean.colorspace_settings.name = img.colorspace_settings.name
    log("denoised %s" % img.name)
    return clean


def baked_material(name, img_path):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = bsdf_of(m)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(img_path)
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "Lightmap"
    nt.links.new(uvn.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 1.0
    m["baked"] = 1
    return m


def flat_copy(m, kind):
    """Plain glTF material for glass and lamps: colour, alpha, emission."""
    b = bsdf_of(m)
    c = bpy.data.materials.new("fix.%s" % m.name)
    c.use_nodes = True
    cb = bsdf_of(c)
    col = b.inputs["Base Color"].default_value if b is not None and not b.inputs["Base Color"].is_linked else m.diffuse_color
    cb.inputs["Base Color"].default_value = col
    cb.inputs["Roughness"].default_value = 0.1 if kind == "glass" else 0.5
    if kind == "glass":
        cb.inputs["Alpha"].default_value = 0.3
        c["glass"] = 1
        try:
            c.surface_render_method = "BLENDED"
        except Exception:
            c.blend_method = "BLEND"
    else:
        ec = b.inputs.get("Emission Color") or b.inputs.get("Emission")
        for key in ("Emission Color", "Emission"):
            if key in cb.inputs:
                cb.inputs[key].default_value = ec.default_value
        cb.inputs["Emission Strength"].default_value = 1.0
        c["glow"] = 1
    return c


def main():
    # build_house's helpers (box_uv) without running its main()
    src = open(os.path.join(BLENDER_DIR, "build_house.py")).read().replace("\nmain()\n", "\n")
    ns = {"__file__": os.path.join(BLENDER_DIR, "build_house.py"), "__name__": "build_house_lib"}
    exec(compile(src, "build_house.py", "exec"), ns)
    import __main__
    for k, v in ns.items():
        if callable(v) and not hasattr(__main__, k):
            setattr(__main__, k, v)

    os.makedirs(OUT, exist_ok=True)
    sc = bpy.context.scene
    set_cycles()
    set_light(light_set)
    sc.render.use_compositing = False
    order = FLOORS
    for floor in floors:
        if not floor:
            continue
        if floor == "roof":
            root = bpy.data.objects["Floor.second"]
            pick = lambda o: under_name(o, "Floor.roof")
        elif floor == "site":
            root = bpy.data.objects["Site.Units"]
            # The street disc and the neighbours stay out: the site's fog
            # stands in for them, and the disc alone would eat the atlas.
            pick = lambda o, r=None: under_name(o, "Site.Units") and not o.name.startswith(("Site.Street", "Site.Neighbour"))
        else:
            root = bpy.data.objects["Floor.%s" % floor]
            pick = lambda o, r=root: under(o, r)

        # Open-topped: everything above a floor goes, as on the site. The
        # roof and the street are baked with the whole house standing.
        def hide(o, floor=floor):
            if "fog" in o.name.lower() or "haze" in o.name.lower():
                return True
            if floor in order:
                if any(under(o, bpy.data.objects["Floor.%s" % k]) for k in order[order.index(floor) + 1:]):
                    return True
                return under_name(o, "Floor.roof")
            return False
        bake_part(floor, root, pick, hide)

    # Room dioramas (site/src/space/rooms.json): each room alone, cut to its
    # rectangle and wall height, lit the same way, so every space matches.
    for rid in [r for r in opt("--rooms", "").split(",") if r]:
        cfg = ROOMS[rid]
        root = bpy.data.objects["Floor.%s" % cfg["floor"]]
        pick = lambda o, r=root: under(o, r)

        def hide(o, r=root):
            if o.type == "LIGHT":
                return o.name != "Sun.Dawn" and not under(o, r)
            return not under(o, r)
        bake_part("room-" + rid, root, pick, hide, cut=(cfg["rect"], cfg["top"]))


ROOMS = {}
try:
    import json
    ROOMS = {k: v for k, v in json.load(open(os.path.join(os.path.dirname(BLENDER_DIR), "site", "src", "space", "rooms.json"))).items() if k != "_"}
except Exception as e:
    log("no rooms.json (%s)" % e)


def cut_to(ob, root, rect, top):
    """Keep only what lies inside the room's rectangle and below `top`
    (floor plan units), like the site's diorama."""
    import bmesh
    x0, z0, x1, z1 = rect
    mw = root.matrix_world
    planes = [((x0, 0, 0), (-1, 0, 0)), ((x1, 0, 0), (1, 0, 0)),
              ((0, -z0, 0), (0, 1, 0)), ((0, -z1, 0), (0, -1, 0)), ((0, 0, top), (0, 0, 1))]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for co, no in planes:
        wco = mw @ Vector(co)
        wno = (mw.to_3x3() @ Vector(no)).normalized()
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=wco, plane_no=wno,
                               clear_outer=True)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    log("cut %s to %s, top %.2f: %d faces" % (ob.name, rect, top, len(ob.data.polygons)))


def bake_part(name, root, pick, hide, cut=None):
    sc = bpy.context.scene
    t0 = time.time()
    hidden = []
    for o in bpy.data.objects:
        if not o.hide_render and hide(o):
            o.hide_render = True
            hidden.append(o)
    srcs = [o for o in bpy.data.objects if o.type in {"MESH", "CURVE", "FONT"} and pick(o)
            and not o.hide_render and re.sub(r"\.\d+$", "", o.name).split(".")[-1] not in SKIP]
    ob = joined(srcs, "%s.baked" % name)
    for o in srcs:
        o.hide_render = True
    if cut:
        cut_to(ob, root, *cut)
    parts = split_by_kind(ob)
    lightmap_uv(ob)
    img = bpy.data.images.new("%s-%s" % (name, light_set), RES, RES, float_buffer=True)
    bake(ob, img)
    if "--no-denoise" not in args:
        try:
            img = denoise(img)
        except Exception as e:
            log("denoise failed (%s); keeping the raw bake" % e)
    # Bake pixels are linear scene light; save through the scene's view
    # transform so the site can show them unlit and untouched.
    sc.view_settings.exposure = EXPOSURE
    jpg = os.path.join(OUT, "%s-%s.jpg" % (name, light_set))
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 90
    img.save_render(jpg, scene=sc)
    log("atlas %s" % jpg)
    # Export: the baked shell, then the fixtures.
    me = ob.data
    me.materials.clear()
    me.materials.append(baked_material("baked.%s-%s" % (name, light_set), jpg))
    for uv in list(me.uv_layers):
        if uv.name != "Lightmap":
            me.uv_layers.remove(uv)
    export([ob], os.path.join(OUT, "%s-%s.gltf" % (name, light_set)), root)
    fixtures = []
    for k, part in parts.items():
        pm = part.data
        for i, m in enumerate(pm.materials):
            if m is not None:
                pm.materials[i] = flat_copy(m, k)
        for uv in list(pm.uv_layers):
            pm.uv_layers.remove(uv)
        fixtures.append(part)
    if fixtures and light_set == "day":
        export(fixtures, os.path.join(OUT, "%s-fixtures.gltf" % name), root)
    # Put the scene back for the next part.
    for o in srcs + hidden:
        o.hide_render = False
    for o in [ob] + fixtures:
        bpy.data.objects.remove(o)
    log("%s done in %.0f s" % (name, time.time() - t0))

main()
