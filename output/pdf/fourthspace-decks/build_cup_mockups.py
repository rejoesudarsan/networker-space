from pathlib import Path
import math
import bpy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'assets' / 'cups'
OUT.mkdir(parents=True, exist_ok=True)

BRANDS = [
    {'slug': 'openai', 'company': 'OpenAI', 'drink': 'PROMPT & POUR', 'sleeve': '#18251F', 'ink': '#F5F1E8'},
    {'slug': 'razorpay', 'company': 'Razorpay', 'drink': 'CHECKOUT COLD BREW', 'sleeve': '#3157C8', 'ink': '#FFFFFF'},
    {'slug': 'notion', 'company': 'Notion', 'drink': 'BLANK PAGE MATCHA', 'sleeve': '#F5F1E8', 'ink': '#18251F'},
    {'slug': 'postman', 'company': 'Postman', 'drink': 'THE DELIVERY', 'sleeve': '#D85B32', 'ink': '#18251F'},
    {'slug': 'your-brand', 'company': 'YOUR BRAND', 'drink': 'YOUR SIGNATURE DRINK', 'sleeve': '#B6532F', 'ink': '#FFFCF5'},
]


def rgba(value):
    value = value.lstrip('#')
    rgb = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return (*rgb, 1)


def material(name, color, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba(color)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = rgba(color)
    bsdf.inputs['Roughness'].default_value = roughness
    return mat


def smooth(obj):
    if obj.type == 'MESH':
        for poly in obj.data.polygons:
            poly.use_smooth = True


def frustum(name, bottom, top, height, z, mat, segments=128):
    vertices = []
    for radius, level in ((bottom, z - height / 2), (top, z + height / 2)):
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), level))
    faces = []
    for i in range(segments):
        j = (i + 1) % segments
        faces.append((i, j, segments + j, segments + i))
    faces.append(tuple(reversed(range(segments))))
    faces.append(tuple(range(segments, segments * 2)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.data.materials.append(mat)
    smooth(obj)
    bevel = obj.modifiers.new('Soft paper edges', 'BEVEL')
    bevel.width = 0.008
    bevel.segments = 3
    return obj


def cylinder(name, radius, depth, z, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=radius, depth=depth, location=(0, 0, z))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    smooth(obj)
    bevel = obj.modifiers.new('Rounded edge', 'BEVEL')
    bevel.width = 0.015
    bevel.segments = 3
    return obj


def torus(name, radius, tube, z, mat):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=tube, major_segments=128, minor_segments=16, location=(0, 0, z))
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    smooth(obj)
    return obj


def text(name, value, z, size, mat, font_path=None, y=-0.505):
    curve = bpy.data.curves.new(name, 'FONT')
    curve.body = value
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.size = size
    curve.extrude = 0.0003
    if font_path:
        curve.font = bpy.data.fonts.load(font_path)
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.location = (0, y, z)
    obj.rotation_euler = (math.radians(90), 0, 0)
    obj.data.materials.append(mat)
    return obj


def point_at(obj, target):
    from mathutils import Vector
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.samples = 40
scene.cycles.use_denoising = True
scene.render.resolution_x = 900
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
scene.view_settings.exposure = -0.6

paper = material('Warm white paper', '#EEE9DE', 0.72)
lid = material('Charcoal lid', '#202A25', 0.32)
ground = material('Warm studio floor', '#D8C9B4', 0.82)
sleeve = material('Partner sleeve', '#18251F', 0.56)
ink = material('Sleeve print', '#F5F1E8', 0.6)

frustum('Paper cup', 0.35, 0.50, 1.35, 0.77, paper)
frustum('Partner sleeve', 0.435, 0.49, 0.55, 0.79, sleeve)
cylinder('Lid base', 0.515, 0.10, 1.47, lid)
cylinder('Lid crown', 0.45, 0.12, 1.55, lid)
torus('Lid rim', 0.50, 0.025, 1.50, lid)
torus('Cup bottom', 0.35, 0.012, 0.10, paper)

bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, 0.045))
plane = bpy.context.object
plane.name = 'Studio floor'
plane.data.materials.append(ground)

bpy.ops.object.camera_add(location=(2.2, -6.5, 2.7))
camera = bpy.context.object
point_at(camera, (0, 0, 0.80))
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.05
scene.camera = camera

for name, location, energy, size in [
    ('Key softbox', (-3, -4, 6), 650, 4.0),
    ('Fill softbox', (4, -2, 3), 350, 3.0),
    ('Rim softbox', (0, 4, 5), 500, 3.0),
]:
    bpy.ops.object.light_add(type='AREA', location=location)
    light = bpy.context.object
    light.name = name
    light.data.energy = energy
    light.data.shape = 'DISK'
    light.data.size = size
    point_at(light, (0, 0, 0.7))

scene.world.color = (0.22, 0.22, 0.22)
labels = [
    text('House mark', 'FOURTHSPACE', 0.98, 0.052, ink, '/Users/rejoesudarsan/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts/Ubuntu-B.ttf'),
    text('Co-built line', 'CO-BUILT WITH', 0.86, 0.042, ink, '/Users/rejoesudarsan/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts/Ubuntu-R.ttf'),
    text('Company', 'YOUR BRAND', 0.73, 0.115, ink, '/Users/rejoesudarsan/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts/Ubuntu-B.ttf'),
    text('Drink', 'YOUR SIGNATURE DRINK', 0.59, 0.038, ink, '/Users/rejoesudarsan/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts/Ubuntu-B.ttf'),
]

for brand in BRANDS:
    sleeve.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = rgba(brand['sleeve'])
    sleeve.diffuse_color = rgba(brand['sleeve'])
    ink.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = rgba(brand['ink'])
    ink.diffuse_color = rgba(brand['ink'])
    labels[2].data.body = brand['company']
    labels[2].data.size = 0.095 if len(brand['company']) > 9 else 0.115
    labels[3].data.body = brand['drink']
    labels[3].data.size = 0.031 if len(brand['drink']) > 20 else 0.038
    scene.render.filepath = str(OUT / f'{brand["slug"]}-cup.png')
    bpy.ops.render.render(write_still=True)

bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'cup-mockup-scene.blend'))
print(f'Created {len(BRANDS)} cup mockups in {OUT}')
