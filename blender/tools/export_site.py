"""Export the Blender details for the website, one GLB per floor.

  /snap/bin/blender -b blender/space-house.blend --python blender/tools/export_site.py

Writes site/public/models/blender/<floor>.glb. Each file holds what the
Blender build adds to a floor (slab with its openings, finishes, site works
and every detail module), in that floor's local Three.js units with the slab
top at y = 0, so the site can add it to its floor group as is. Left out: what
the site already draws (the CAD walls, columns, sills, plan lines, windows and
the heads above openings), the roof, and everything outside the floors (street,
neighbours, gulmohars, cameras, lights).

Meshes are merged per material, in two groups per floor: '<mat>' and
'<mat>_high'. High parts are those that start more than 0.45 units above the
floor (lanterns, fans, wall cabinets, pinboards): the site hides them while
its walls are lowered for the cutaway. Procedural Blender materials become
flat colours (their viewport colour); emission is kept.

Heads over doors, windows and gaps, and the sliver fills, are included; they
start high on the wall, so they land in the _high group and hide in the
cutaway. Also writes site.glb: everything under Site.Units (gulmohars,
neighbour houses, office gate) in the street frame. Also writes roof.glb: everything under Floor.roof (roof slab with the
courtyard opening, parapets, the terrace eave, the skylight) in the second
floor's frame. The site shows it while the house is closed and hides it in
the cutaway."""
import os

import bmesh
import bpy
from mathutils import Matrix

FLOORS = ["basement", "ground", "first", "second"]
# What the site already draws: the CAD walls, columns, sills and plan lines,
# and its own windows (which lower with the cutaway).
SKIP = ("walls", "columns", "sills", "details", "windowFrames", "windowGlass")
HIGH_Z = 0.45
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(os.path.dirname(HERE), "site", "public", "models", "blender")


def base(name):
    import re
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


def flat_material(m, cache):
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
    if src is not None:
        bc = src.inputs["Base Color"]
        if not bc.is_linked:
            col = tuple(bc.default_value)
        rough = src.inputs["Roughness"].default_value
        metal = src.inputs["Metallic"].default_value
        for k in ("Emission Color", "Emission"):
            if k in src.inputs:
                emit = tuple(src.inputs[k].default_value)
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
    bsdf.inputs["Base Color"].default_value = col
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emit and strength > 0:
        for k in ("Emission Color", "Emission"):
            if k in bsdf.inputs:
                bsdf.inputs[k].default_value = emit
        bsdf.inputs["Emission Strength"].default_value = min(strength, 2.0)
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        try:
            fm.surface_render_method = "BLENDED"
        except Exception:
            fm.blend_method = "BLEND"
    cache[m.name] = fm
    return fm


def main():
    os.makedirs(OUT, exist_ok=True)
    dg = bpy.context.evaluated_depsgraph_get()
    cache = {}
    jobs = [(k, bpy.data.objects["Floor.%s" % k], under) for k in FLOORS]
    jobs.append(("roof", bpy.data.objects["Floor.second"], under_roof))
    # Outside the house: gulmohars, neighbours, office gate, in the street frame
    # (ground-floor x/z, street level at y = 0).
    jobs.append(("site", bpy.data.objects["Site.Units"], under))
    for key, root, select in jobs:
        inv = root.matrix_world.inverted()
        groups = {}                     # (material name, high) -> bmesh
        n_obj = 0
        for o in bpy.data.objects:
            if o.type not in {"MESH", "CURVE", "FONT"} or not select(o, root):
                continue
            if base(o.name) in SKIP or o.name.split(".")[-1] in SKIP or o.hide_render:
                continue
            ev = o.evaluated_get(dg)
            me = bpy.data.meshes.new_from_object(ev)
            if not me.polygons:
                bpy.data.meshes.remove(me)
                continue
            me.transform(inv @ o.matrix_world)
            zmin = min(v.co.z for v in me.vertices)
            high = key != "roof" and zmin > HIGH_Z and "Tree" not in o.name and "Olive" not in o.name and "Frangipani" not in o.name
            if o.name.split(".")[-1] == "sliverFill" or "CladdingStrip" in o.name or "WindowBox" in o.name:
                high = "wall"            # wall and facade pieces: the site lowers them with its walls
            mats = list(me.materials) or [None]
            for mi, m in enumerate(mats):
                polys = [p for p in me.polygons if p.material_index == mi] if len(mats) > 1 else list(me.polygons)
                if not polys:
                    continue
                fm = flat_material(m, cache)
                bm = groups.setdefault((fm.name, high), bmesh.new())
                part = bmesh.new()
                part.from_mesh(me)
                if len(mats) > 1:
                    keep = {p.index for p in polys}
                    bmesh.ops.delete(part, geom=[f for f in part.faces if f.index not in keep], context="FACES")
                tmp = bpy.data.meshes.new("_tmp")
                part.to_mesh(tmp)
                part.free()
                bm.from_mesh(tmp)
                bpy.data.meshes.remove(tmp)
            bpy.data.meshes.remove(me)
            n_obj += 1
        # Build an export scene
        sc = bpy.data.scenes.new("export_" + key)
        for (mname, high), bm in groups.items():
            nm = mname[4:] + {True: "_high", "wall": "_wall"}.get(high, "")
            me = bpy.data.meshes.new(nm)
            bm.to_mesh(me)
            bm.free()
            me.materials.append(bpy.data.materials[mname])
            ob = bpy.data.objects.new(nm, me)
            sc.collection.objects.link(ob)
        win = bpy.context.window
        prev = win.scene
        win.scene = sc
        path = os.path.join(OUT, "%s.glb" % key)
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_active_scene=True,
                                  export_apply=False, export_yup=True, export_cameras=False,
                                  export_lights=False, export_extras=False)
        win.scene = prev
        print("[export] %s: %d objects -> %d meshes, %.0f KB" % (key, n_obj, len(groups), os.path.getsize(path) / 1024))


main()
