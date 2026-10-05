"""Export the Blender house for the website, one glTF per floor, with its textures.

  /snap/bin/blender -b blender/space-house.blend --python blender/tools/export_site.py

Writes site/public/models/blender/<floor>.gltf (+ .bin) and a shared
textures/ folder. Each file holds what the Blender build adds to a floor
(slab with its openings, finishes, site works and every detail module) plus
the house's own walls and columns, in that floor's local Three.js units with
the slab top at y = 0, so the site can add it to its floor group as is.

Meshes are merged per material, in groups per floor: '<mat>', '<mat>_high'
and '<mat>_wall'. High parts are those that start more than 0.45 units above
the floor (lanterns, fans, wall cabinets, pinboards): the site hides them
while its walls are lowered for the cutaway. Wall parts (the CAD walls and
columns, cladding, window boxes, sliver fills) are scaled down by the site in
the cutaway.

Materials keep their image textures (colour, roughness, normal) on the BoxUV
map, downscaled to 1k for the web; the per-material tint and roughness
scaling that build_house.py applies in its node trees are written to the
material extras ('tint', 'rough') and applied by the site. Procedural
materials become flat colours. Emission and glass alpha are kept.

Also writes site.gltf (everything under Site.Units: gulmohars, neighbour
houses, compound wall and gates, in the street frame) and roof.gltf
(everything under Floor.roof, in the second floor's frame).
"""
import os
import re

import bpy
from mathutils import Matrix

FLOORS = ["basement", "ground", "first", "second"]
# What the site still draws itself: the CAD sills and plan lines, and its own
# windows (which lower with the cutaway).
SKIP = ("sills", "details", "windowFrames", "windowGlass")
WALLISH = ("walls", "columns", "sliverFill", "CladdingStrip", "WindowBox", "doorHeads", "gapHeads")
HIGH_Z = 0.45
WEB_TEX = 1024
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(HERE), "site", "public", "models", "blender")


def base(name):
    return re.sub(r"\.\d+$", "", name).split(".")[-1]


def under_roof(o, _root):
    p = o.parent
    while p is not None:
        if p.name == "Floor.roof":
            return True
        p = p.parent
    return False


def under(o, root):
    p = o.parent
    while p is not None:
        if p == root:
            return True
        if p.name == "Floor.roof":
            return False
        p = p.parent
    return False


def find_tex(nt, socket):
    """Walk back from a BSDF socket to the first Image Texture node; return
    (image, multiplier rgb or None, scalar factor or None)."""
    if not socket.is_linked:
        return None, None, None
    mult = None
    factor = None
    node = socket.links[0].from_node
    for _ in range(8):
        if node.type == "TEX_IMAGE":
            return node.image, mult, factor
        if node.type in ("MIX", "MIX_RGB"):
            # build_house: tex * (palette / mean), then a mix toward the flat palette
            a = node.inputs[6] if node.type == "MIX" else node.inputs[1]
            b = node.inputs[7] if node.type == "MIX" else node.inputs[2]
            blend = node.blend_type
            fac = node.inputs[0].default_value
            if blend == "MULTIPLY" and not b.is_linked:
                mult = tuple(b.default_value)[:3]
            elif blend == "MIX" and not b.is_linked:
                # pull toward the flat colour: fold into the multiplier as a lerp toward 1
                t = tuple(b.default_value)[:3]
                if mult is None:
                    mult = (1.0, 1.0, 1.0)
                mult = tuple(mult[i] * (1 - fac) + t[i] * fac for i in range(3))
            node = a.links[0].from_node if a.is_linked else None
        elif node.type == "MATH" and node.operation == "MULTIPLY":
            factor = node.inputs[1].default_value
            node = node.inputs[0].links[0].from_node if node.inputs[0].is_linked else None
        elif node.type == "NORMAL_MAP":
            node = node.inputs["Color"].links[0].from_node if node.inputs["Color"].is_linked else None
        else:
            return None, mult, factor
        if node is None:
            return None, mult, factor
    return None, mult, factor


_web_images = {}


def web_image(img):
    """A 1k copy of the image for the web, saved once per source."""
    if img.name in _web_images:
        return _web_images[img.name]
    w, h = img.size
    copy = img.copy()
    copy.name = "web_" + img.name
    if max(w, h) > WEB_TEX:
        s = WEB_TEX / float(max(w, h))
        copy.scale(max(1, int(w * s)), max(1, int(h * s)))
    tex_dir = os.path.join(OUT, "textures")
    os.makedirs(tex_dir, exist_ok=True)
    src = bpy.path.abspath(img.filepath_raw) if img.filepath_raw else img.name
    stem = os.path.basename(os.path.dirname(src)) + "_" + os.path.splitext(os.path.basename(src))[0]
    path = os.path.join(tex_dir, stem + ".jpg")
    copy.filepath_raw = path
    copy.file_format = "JPEG"
    scene = bpy.context.scene
    try:
        q = scene.render.image_settings.quality
        scene.render.image_settings.quality = 85
    except Exception:
        q = None
    copy.save()
    if q is not None:
        scene.render.image_settings.quality = q
    copy.colorspace_settings.name = img.colorspace_settings.name
    _web_images[img.name] = copy
    return copy


def web_material(m, cache):
    """An export copy of a material: textures linked straight into the BSDF,
    tint and roughness scale in extras."""
    if m is None:
        m = bpy.data.materials.get("Lime White")
    if m.name in cache:
        return cache[m.name]
    fm = bpy.data.materials.new("web." + m.name)
    fm.use_nodes = True
    nt = fm.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    src = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m.node_tree else None
    col = tuple(m.diffuse_color)
    rough, metal, emit, strength = 0.8, 0.0, None, 0.0
    tint = None
    rough_k = None
    size_m = 1.0
    if src is not None:
        # texture scale: the Mapping node on the BoxUV chain
        mp = next((n for n in m.node_tree.nodes if n.type == "MAPPING"), None)
        if mp is not None:
            size_m = 1.0 / max(mp.inputs["Scale"].default_value[0], 1e-6)
        bc = src.inputs["Base Color"]
        img, mult, _ = find_tex(m.node_tree, bc)
        if img is not None:
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = web_image(img)
            nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
            tint = mult or (1.0, 1.0, 1.0)
        elif not bc.is_linked:
            col = tuple(bc.default_value)
        r = src.inputs["Roughness"]
        rimg, _, k = find_tex(m.node_tree, r)
        if rimg is not None:
            rt = nt.nodes.new("ShaderNodeTexImage")
            rt.image = web_image(rimg)
            rt.image.colorspace_settings.name = "Non-Color"
            nt.links.new(rt.outputs["Color"], bsdf.inputs["Roughness"])
            rough_k = k or 1.0
            rough = 1.0
        else:
            rough = r.default_value
        n = src.inputs["Normal"]
        nimg, _, _ = find_tex(m.node_tree, n)
        if nimg is not None:
            ntx = nt.nodes.new("ShaderNodeTexImage")
            ntx.image = web_image(nimg)
            ntx.image.colorspace_settings.name = "Non-Color"
            nm = nt.nodes.new("ShaderNodeNormalMap")
            srcnm = n.links[0].from_node if n.is_linked else None
            if srcnm is not None and srcnm.type == "NORMAL_MAP":
                nm.inputs["Strength"].default_value = srcnm.inputs["Strength"].default_value
            nt.links.new(ntx.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
        mt = src.inputs["Metallic"]
        metal = mt.default_value if not mt.is_linked else 0.8
        for key in ("Emission Color", "Emission"):
            if key in src.inputs:
                emit = tuple(src.inputs[key].default_value)
        if "Emission Strength" in src.inputs:
            strength = src.inputs["Emission Strength"].default_value
        alpha = src.inputs["Alpha"].default_value if "Alpha" in src.inputs else 1.0
        tr = src.inputs.get("Transmission Weight") or src.inputs.get("Transmission")
        if tr is not None and tr.default_value > 0.5:
            alpha = 0.25
    else:
        alpha = 1.0
    if m.name.lower().startswith(("glass", "sky glass", "clear glass", "frosted")) or "Glass" in m.name and alpha >= 1.0 and "Block" not in m.name:
        alpha = min(alpha, 0.3)
    if tint is None:
        bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit and strength > 0:
        for key in ("Emission Color", "Emission"):
            if key in bsdf.inputs:
                bsdf.inputs[key].default_value = emit
        bsdf.inputs["Emission Strength"].default_value = min(strength, 2.0)
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            fm.surface_render_method = "BLENDED"
        except Exception:
            fm.blend_method = "BLEND"
    if tint is not None:
        fm["tint"] = [float(c) for c in tint]
    if rough_k is not None:
        fm["rough"] = float(rough_k)
    fm["uvScale"] = float(1.0 / size_m)
    cache[m.name] = fm
    return fm


def main():
    os.makedirs(OUT, exist_ok=True)
    dg = bpy.context.evaluated_depsgraph_get()
    cache = {}
    jobs = [(k, bpy.data.objects["Floor.%s" % k], under) for k in FLOORS]
    jobs.append(("roof", bpy.data.objects["Floor.second"], under_roof))
    jobs.append(("site", bpy.data.objects["Site.Units"], under))
    for key, root, select in jobs:
        inv = root.matrix_world.inverted()
        groups = {}                     # (material name, high) -> bmesh
        n_obj = 0
        for o in bpy.data.objects:
            if o.type not in {"MESH", "CURVE", "FONT"} or not select(o, root):
                continue
            b = base(o.name)
            tail = o.name.split(".")[-1]
            if b in SKIP or tail in SKIP or o.hide_render:
                continue
            ev = o.evaluated_get(dg)
            me = bpy.data.meshes.new_from_object(ev)
            if not me.polygons:
                bpy.data.meshes.remove(me)
                continue
            me.transform(inv @ o.matrix_world)
            zmin = min(v.co.z for v in me.vertices)
            high = key != "roof" and zmin > HIGH_Z and "Tree" not in o.name and "Olive" not in o.name and "Frangipani" not in o.name
            if any(w in o.name for w in WALLISH) or b in WALLISH or tail in WALLISH:
                high = "wall"
            if key in ("roof", "site"):
                high = False
            mats = list(me.materials) or [None]
            uv_layer = me.uv_layers.active.data if me.uv_layers.active else None
            verts = [v.co.copy() for v in me.vertices]
            for mi, m in enumerate(mats):
                polys = [p for p in me.polygons if p.material_index == mi] if len(mats) > 1 else list(me.polygons)
                if not polys:
                    continue
                fm = web_material(m, cache)
                s = fm.get("uvScale", 1.0)
                grp = groups.setdefault((fm.name, high), {"v": [], "f": [], "uv": []})
                off = len(grp["v"])
                used = {}
                for poly in polys:
                    face = []
                    for li in range(poly.loop_start, poly.loop_start + poly.loop_total):
                        vi = me.loops[li].vertex_index
                        if vi not in used:
                            used[vi] = off + len(used)
                            grp["v"].append(verts[vi])
                        face.append(used[vi])
                        uv = uv_layer[li].uv if uv_layer is not None else (0.0, 0.0)
                        grp["uv"].append((uv[0] * s, uv[1] * s))
                    grp["f"].append(face)
            bpy.data.meshes.remove(me)
            n_obj += 1
        sc = bpy.data.scenes.new("export_" + key)
        for (mname, high), grp in groups.items():
            nm = mname[4:] + {True: "_high", "wall": "_wall"}.get(high, "")
            me = bpy.data.meshes.new(nm)
            me.from_pydata(grp["v"], [], grp["f"])
            uv = me.uv_layers.new(name="uv")
            for i, co in enumerate(grp["uv"]):
                uv.data[i].uv = co
            me.polygons.foreach_set("use_smooth", [False] * len(me.polygons))
            me.validate()
            me.update()
            me.materials.append(bpy.data.materials[mname])
            ob = bpy.data.objects.new(nm, me)
            sc.collection.objects.link(ob)
        win = bpy.context.window
        prev = win.scene
        win.scene = sc
        path = os.path.join(OUT, "%s.gltf" % key)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLTF_SEPARATE", use_active_scene=True,
                                  export_apply=False, export_yup=True, export_cameras=False,
                                  export_lights=False, export_extras=True, export_texture_dir="textures",
                                  export_image_format="JPEG", export_jpeg_quality=85, export_keep_originals=False)
        win.scene = prev
        print("[export] %s: %d objects -> %d meshes, %.0f KB" % (key, n_obj, len(groups), os.path.getsize(path) / 1024))
    # The old GLBs would shadow the new files in the site's fallback order.
    for f in os.listdir(OUT):
        if f.endswith(".glb"):
            os.remove(os.path.join(OUT, f))


main()
