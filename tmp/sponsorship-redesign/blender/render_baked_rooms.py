"""Render baked room glTFs as clean proposal dioramas.

Usage from the repository root:
  Blender -b --factory-startup --python tmp/sponsorship-redesign/blender/render_baked_rooms.py

The baked atlases are displayed through emission so the render does not add a
second light pass. Glass/fixture glTFs are imported alongside each room.
"""
import math
import os
import bpy
from mathutils import Vector

ROOT = "/Users/rejoesudarsan/Dev/networker-space"
BAKED = os.path.join(ROOT, "site/public/models/baked")
OUT = os.path.join(ROOT, "output/pdf/fourthspace-decks/redesign/assets/blender")
ROOMS = {
    "cafe": (14, 42),
    "court": (-18, 46),
    "event": (20, 46),
}

def import_gltf(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    return [o for o in bpy.data.objects if o not in before]

def make_baked_emission():
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        nt = mat.node_tree
        tex = next((n for n in nt.nodes if n.type == "TEX_IMAGE"), None)
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if tex is None or bsdf is None:
            continue
        # Blender 5.2 renamed the socket; support both current and older names.
        em = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        strength = bsdf.inputs.get("Emission Strength")
        if em is not None:
            nt.links.new(tex.outputs["Color"], em)
        if strength is not None:
            strength.default_value = 1.0
        # The atlas already contains the day light and material colour.
        # Keep the Principled shader only as an emission carrier.
        bsdf.inputs["Base Color"].default_value = (1.0, 1.0, 1.0, 1.0)
        bsdf.inputs["Metallic"].default_value = 0.0
        bsdf.inputs["Roughness"].default_value = 1.0

def frame_room(objects, az_deg, el_deg):
    pts = []
    for obj in objects:
        if obj.type != "MESH":
            continue
        pts += [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre = (lo + hi) / 2
    # glTF import presents these files z-up in Blender: x/y are the plan and
    # z is height. Keep the full horizontal footprint in frame.
    horizontal = max(hi.x - lo.x, hi.y - lo.y)
    vertical = hi.z - lo.z
    az, el = math.radians(az_deg), math.radians(el_deg)
    direction = Vector((math.sin(az) * math.cos(el), -math.cos(az) * math.cos(el), math.sin(el)))
    cam = bpy.data.cameras.new("ProposalCamera")
    camera = bpy.data.objects.new("ProposalCamera", cam)
    bpy.context.scene.collection.objects.link(camera)
    cam.type = "ORTHO"
    aspect = 1600 / 1100
    distance = max(horizontal, vertical) * 2.0
    camera.location = centre + direction * distance
    camera.rotation_euler = (centre - camera.location).to_track_quat("-Z", "Y").to_euler()
    # Fit the actual projected corners, since a diagonal view makes the
    # screen extents larger than the raw x/y/z bounds.
    q = camera.rotation_euler.to_quaternion()
    right, up = q @ Vector((1, 0, 0)), q @ Vector((0, 1, 0))
    rx = [p.dot(right) for p in pts]
    uy = [p.dot(up) for p in pts]
    screen_w, screen_h = max(rx) - min(rx), max(uy) - min(uy)
    cam.ortho_scale = max(screen_h, screen_w / aspect) * 1.16
    bpy.context.scene.camera = camera

def render_one(room, az, el):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    shell = import_gltf(os.path.join(BAKED, f"room-{room}-day.gltf"))
    fixtures = import_gltf(os.path.join(BAKED, f"room-{room}-fixtures.gltf"))
    make_baked_emission()
    frame_room(shell + fixtures, az, el)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.resolution_x, scene.render.resolution_y = 1600, 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    world = bpy.data.worlds.new(f"Ivory-{room}")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.91, 0.89, 0.84, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.filepath = os.path.join(OUT, f"{room}-baked.png")
    bpy.ops.render.render(write_still=True)
    print(f"[baked-room] wrote {scene.render.filepath}")

os.makedirs(OUT, exist_ok=True)
for room, (az, el) in ROOMS.items():
    render_one(room, az, el)
