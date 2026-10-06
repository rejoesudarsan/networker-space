"""Bake the house's light into textures for the website, one atlas per floor.

  Blender -b blender/space-house.blend --python blender/tools/bake_site.py -- \
      [--floors ground,first] [--rooms cafe,court] [--set day] [--res 2048] [--samples 128] [--exposure -0.4] [--wall-cut 1.0]

--rooms bakes the homepage's room dioramas from site/src/space/rooms.json
instead: each room alone (nothing else in the scene), cut to its rectangle
and wall height, lit identically, written as room-<id>-<set>.gltf. Given
alone, --rooms skips the floors.

For each floor: every mesh the build put under Floor.<floor> (walls, slab,
finishes, every detail and fit-out module, modifiers applied) is joined in
world space into one object, given a second, non-overlapping UV map
("Lightmap", Smart UV Project) and baked in Cycles as Diffuse (direct +
indirect + colour), which holds the materials' colour and texture times the
light that falls on them, independent of the viewing angle. Glass and
emissive lamps are left out of the bake and exported with flat materials.
The linked entourage (people, the garage car) is made real and baked in.
Walls are cut short (--wall-cut, metres, default 1.0; user request) so the
rooms read from above, and faces buried under other surfaces are dropped
(they bake black and flicker on the site).

The bake is lit the way the site shows a floor: the floors above and the
roof are hidden (the site sees every room open-topped), the floors below and
the street stay for bounce light. --set picks the light: "day" (high warm
sun, the sky HDRI, the club_lamp lights at a quarter power) or "night" (sun
off, a low blue sky, the house's lamps at full power and glow materials on).

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
# Day saves a touch under (-0.4); night at 0, as checked against Cycles
# shots of the café and the court (night-light-check, 6 Oct 2026).
WALL_CUT = float(opt("--wall-cut", 1.0))   # metres; walls stop here, 0 keeps them whole
EXPOSURE = float(opt("--exposure", -0.4 if light_set == "day" else 0.0))


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
    """'glass', 'glow', 'flat' or 'bake'. Flat goes to the fixtures file in
    plain colour instead of the atlas: the street gulmohars' foliage (~100k
    faces in thousands of tiny islands, which shrink the whole atlas to
    nothing) and the people (too small in the atlas: the denoiser mottles
    their clothes)."""
    if m is None:
        return "bake"
    b = bsdf_of(m)
    name = m.name.lower()
    if name.startswith("gulmohar") and ("leaf" in name or "blossom" in name):
        return "flat"
    if name.startswith("person "):
        return "flat"
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
        # The club's lamps (details/room_lights.py, club_lamp = 1) stay on by
        # day at a quarter of their power: soft pools, not night glare.
        for o in bpy.data.objects:
            if o.type == "LIGHT" and o.get("club_lamp"):
                o.data.energy *= 0.25
    else:
        # Night (night-light-check, 6 Oct 2026, against Cycles shots of the
        # café and the court): sun off, sky at 4% (a blue night, the wall
        # tops still read), glow materials at 6x, the club lamps at full
        # power for warm pools, saved at exposure 0 (EXPOSURE above).
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

def person_mat(m):
    if m is None:
        return None
    c = bpy.data.materials.get("Person " + m.name)
    if c is None:
        c = m.copy()
        c.name = "Person " + m.name
    return c


def realized(pick):
    """World-space mesh copies of the linked entourage (people, cars:
    collection-instance empties) that `pick` keeps, so they are baked into
    the shell with their shadows instead of leaving shadows of nothing.
    Returns (temporary mesh objects, the instancing empties)."""
    dg = bpy.context.evaluated_depsgraph_get()
    empties = [o for o in bpy.data.objects if o.type == "EMPTY" and o.instance_type == "COLLECTION"
               and o.instance_collection and not o.hide_render and pick(o)]
    names = {e.name for e in empties}
    out = []
    for inst in dg.object_instances:
        par = inst.parent.original if inst.is_instance and inst.parent else None
        if par is None or par.name not in names or inst.object.type not in {"MESH", "CURVE"}:
            continue
        me = bpy.data.meshes.new_from_object(inst.object)
        if not me.polygons:
            bpy.data.meshes.remove(me)
            continue
        me.transform(inst.matrix_world)
        # The assets keep their materials on object slots: carry them over
        # (people's as "Person ..." copies, which go out in flat colour).
        slots = [sl.material for sl in inst.object.material_slots]
        if par.instance_collection.name.startswith("Person"):
            slots = [person_mat(m) for m in slots]
        for i, m in enumerate(slots):           # assign in place: clear() would reset the face indices
            if i < len(me.materials):
                me.materials[i] = m
            else:
                me.materials.append(m)
        # Their textures use the asset's own UV map: keep it, under the name the join keeps.
        uvs = [uv for uv in me.uv_layers if uv.active_render] or list(me.uv_layers)[:1]
        if uvs:
            for uv in list(me.uv_layers):
                if uv != uvs[0] and uv.name == "BoxUV":
                    me.uv_layers.remove(uv)
            uvs[0].name = "BoxUV"
        t = bpy.data.objects.new("inst.%s.%s" % (par.name, inst.object.name), me)
        bpy.context.scene.collection.objects.link(t)
        out.append(t)
    log("entourage: %d meshes from %d instances" % (len(out), len(empties)))
    return out, empties


SHELL_PARTS = {"walls", "columns", "doorHeads", "gapHeads", "windowHeads", "windowFrames", "windowGlass",
               "windowBoxes", "WindowBox", "sills", "sliverFill", "blockWall", "louvres", "louvreBars",
               "louvreFrames", "blind", "blinds", "bulkhead", "coveGlow", "slidingDoor", "doorSeams",
               "trackAndPanel", "doorFrames", "doorGlass", "wallAbove", "windowGrille", "glassBlock", "showerGlass",
               "fan"}       # ceiling fans: with no ceiling they would float


def is_shell(name):
    """Walls and what is built into them (openings, frames, glass, blinds,
    bulkheads, sliding panels), by the build's object names."""
    parts = re.sub(r"\.\d+$", "", name).split(".")
    return bool(SHELL_PARTS.intersection(parts[2:] if parts[0] == "tmp" else parts[1:])) or "Passage.glass" in name


def shorten(objs, z, near=0.3):
    """Short, indicative walls (user request, 6 Oct 2026): cut the shell at
    world height z. Fit-out pieces that hang flat on a wall (every vertex
    within `near` metres of it: screens, boards, sconces, letters, the TV)
    are cut at z too, so nothing floats above the short walls; free-standing
    furniture, people and plants stay whole."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    shell = [o for o in objs if is_shell(o.name)]
    if not shell:
        return
    verts, polys = [], []
    for o in shell:
        b = len(verts)
        verts += [v.co.copy() for v in o.data.vertices]
        polys += [[b + i for i in p.vertices] for p in o.data.polygons]
    bvh = BVHTree.FromPolygons(verts, polys)
    plane = dict(plane_co=(0, 0, z), plane_no=(0, 0, 1), clear_outer=True)
    hung = 0
    for o in objs:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        if o in shell:
            bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], **plane)
        elif o.data.vertices and max(v.co.z for v in o.data.vertices) > z:
            islands, seen = [], set()
            for f in bm.faces:
                if f in seen:
                    continue
                isl, stack = [], [f]
                seen.add(f)
                while stack:
                    g = stack.pop()
                    isl.append(g)
                    for e in g.edges:
                        for h in e.link_faces:
                            if h not in seen:
                                seen.add(h)
                                stack.append(h)
                islands.append(isl)
            cut = []
            for isl in islands:
                vs = {v for g in isl for v in g.verts}
                if max(v.co.z for v in vs) > z and all(bvh.find_nearest(v.co, near)[0] is not None for v in vs):
                    cut.append((vs, {e for g in isl for e in g.edges}, isl))
            for vs, es, isl in cut:
                bmesh.ops.bisect_plane(bm, geom=list(vs) + list(es) + isl, **plane)
            hung += len(cut)
        bm.to_mesh(o.data)
        bm.free()
    log("short walls at %.2f m: %d shell objects cut, %d wall-hung pieces trimmed" % (z, len(shell), hung))


def joined(objs, name, wall_z=None):
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
    if wall_z is not None:
        shorten(tmp, wall_z)
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
    """Separate glass, glow and flat faces off into their own objects."""
    me = ob.data
    kinds = [kind_of(m) for m in me.materials]
    out = {}
    for k in ("glass", "glow", "flat"):
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
    # People and cars (materials "Ent ...") are small and curved: scaled up
    # 5x before packing they get ~25x the texels; at 3x their clothes mottled.
    bpy.ops.object.mode_set(mode="OBJECT")
    ent = {i for i, m in enumerate(me.materials) if m is not None and m.name.startswith("Ent ")}
    if ent:
        uvd = uv.data
        for p in me.polygons:
            if p.material_index in ent:
                for li in p.loop_indices:
                    uvd[li].uv *= 5.0
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
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
    """Plain glTF material for glass, lamps and flat parts: colour, alpha, emission."""
    b = bsdf_of(m)
    c = bpy.data.materials.new("fix.%s" % m.name)
    c.use_nodes = True
    cb = bsdf_of(c)
    col = b.inputs["Base Color"].default_value if b is not None and not b.inputs["Base Color"].is_linked else m.diffuse_color
    cb.inputs["Base Color"].default_value = col
    cb.inputs["Roughness"].default_value = 0.1 if kind == "glass" else 0.5
    if kind == "flat":
        # Shown unlit by the site: a little darker than the paint, as if in light shade.
        cb.inputs["Base Color"].default_value = [v * 0.8 for v in col[:3]] + [1.0]
        cb.inputs["Roughness"].default_value = 0.8
    elif kind == "glass":
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


def drop_buried(ob, reach=0.015, push=0.01):
    """Remove the faces nothing can see: a face whose front is covered within
    `reach` (metres) by other geometry at every sample point (a slab
    top under its floor finish, a base plane under planks) bakes black and
    z-fights on the site, where it shows as flicker. A large face that is
    mostly covered (60% of its samples: a layer under another) is split off
    and pushed back up to `push` metres, never past what lies behind it, so
    the depth buffer keeps the layers apart."""
    import bmesh
    from mathutils.bvhtree import BVHTree
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.ensure_lookup_table()
    bvh = BVHTree.FromBMesh(bm)
    dead, part = [], []
    for f in bm.faces:
        n = f.normal
        if n.length < 0.5 or f.calc_area() < 1e-8:
            continue
        c = f.calc_center_median()
        vs = [v.co for v in f.verts]
        pts = [c] + [v.lerp(c, 0.12) for v in vs] + [((a + b) / 2).lerp(c, 0.12) for a, b in zip(vs, vs[1:] + vs[:1])]
        hits = 0
        for pt in pts:
            loc, _, idx, _ = bvh.ray_cast(pt + n * 1e-5, n, reach)
            if loc is not None and idx != f.index:
                hits += 1
        if hits == len(pts):
            dead.append(f)
        elif hits >= 0.6 * len(pts) and f.calc_area() > 0.02:
            # Mostly covered: a layer under another. Never push it past what lies behind it.
            loc, _, idx, dist = bvh.ray_cast(c - n * 1e-5, -n, 0.1)
            part.append((f, push if loc is None else min(push, 0.45 * dist)))
    bmesh.ops.split_edges(bm, edges=list({e for f, _ in part for e in f.edges}))
    for f, d in part:
        for v in f.verts:
            v.co -= f.normal * d
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()
    log("buried faces: %d removed, %d pushed back" % (len(dead), len(part)))


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
    inst, empties = realized(pick)
    wall_z = None
    if WALL_CUT > 0 and (name in FLOORS or name.startswith("room-")):
        wall_z = (root.matrix_world @ Vector((0, 0, 0))).z + WALL_CUT
    ob = joined(srcs + inst, "%s.baked" % name, wall_z)
    for o in inst:
        bpy.data.objects.remove(o)
    for o in srcs + empties:
        o.hide_render = True
    if cut:
        cut_to(ob, root, *cut)
    drop_buried(ob)
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
    if light_set == "day":
        fx = os.path.join(OUT, "%s-fixtures.gltf" % name)
        if fixtures:
            export(fixtures, fx, root)
        else:                       # nothing left (short walls took the lamps): drop the old file
            for f in (fx, fx[:-5] + ".bin"):
                if os.path.exists(f):
                    os.remove(f)
    # Put the scene back for the next part.
    for o in srcs + empties + hidden:
        o.hide_render = False
    for o in [ob] + fixtures:
        bpy.data.objects.remove(o)
    log("%s done in %.0f s" % (name, time.time() - t0))

main()
