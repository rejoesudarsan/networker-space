"""Environment (Astra comps home-03, home-19): the street as dark wet asphalt
with soft reflections fading into the fog.

Edits the Asphalt material in finish() (only Site.Street uses it): the base
colour is multiplied down to the darker wet tone (x0.55, x0.42 in puddles),
the roughness drops from ~0.9 to ~0.35 and to ~0.08 in puddles, and the
normal map flattens in the puddles. Puddles are a large-scale noise in the
street disc's object space (metres). The street fade (add_street_fade in
build_house.py: a Mix Shader toward emissive fog colour) is left as it is,
downstream of the BSDF.

The bake is Diffuse, so only the darker colour reaches the site (as bounce
light: the street itself is not baked; the site's fog and its own street
handle the reflections). Renders of Camera.Street show the gloss."""
import bpy

WET = 0.55          # base colour multiplier, dry -> wet
PUDDLE = 0.42       # ... in the puddles
ROUGH = 0.38        # roughness multiplier on the texture's map (mean 0.9 -> ~0.34)
ROUGH_PUDDLE = 0.08


def build(ctx):
    return []


def finish(ctx):
    warn = ctx["helpers"]["warn"]
    mat = bpy.data.materials.get("Asphalt")
    if mat is None or not mat.node_tree:
        warn("street_wet: no Asphalt material")
        return
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    bsdf = next((n for n in nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        warn("street_wet: Asphalt has no Principled BSDF")
        return

    def math(op, a=None, b=None, clamp=False):
        n = nodes.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                links.new(v, n.inputs[i])
        return n.outputs[0]

    # Puddle mask: broad, soft-edged patches.
    tc = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.12
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.55
    links.new(tc.outputs["Object"], noise.inputs["Vector"])
    mr = nodes.new("ShaderNodeMapRange")
    mr.clamp = True
    mr.inputs["From Min"].default_value = 0.52
    mr.inputs["From Max"].default_value = 0.62
    links.new(noise.outputs["Fac"], mr.inputs["Value"])
    puddle = mr.outputs["Result"]

    # Colour: darker overall, darker still in the puddles.
    k = math("ADD", math("MULTIPLY", puddle, PUDDLE - WET), WET)
    col_in = bsdf.inputs["Base Color"]
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    if col_in.is_linked:
        links.new(col_in.links[0].from_socket, mix.inputs["A"])
    else:
        mix.inputs["A"].default_value = col_in.default_value
    links.new(k, mix.inputs["B"])
    links.new(mix.outputs["Result"], col_in)

    # Roughness: glossy, near mirror in the puddles.
    r_in = bsdf.inputs["Roughness"]
    if r_in.is_linked:
        dry = math("MULTIPLY", r_in.links[0].from_socket, ROUGH)
    else:
        dry = math("MULTIPLY", r_in.default_value, ROUGH)
    links.new(math("ADD", dry, math("MULTIPLY", puddle, math("SUBTRACT", ROUGH_PUDDLE, dry))), r_in)

    # Water fills the texture: flatten the normal map in the puddles.
    nm = next((n for n in nodes if n.type == "NORMAL_MAP"), None)
    if nm is not None:
        s0 = nm.inputs["Strength"].default_value
        links.new(math("MULTIPLY", math("SUBTRACT", 1.0, puddle), s0), nm.inputs["Strength"])

    mat.diffuse_color = tuple(c * WET for c in mat.diffuse_color[:3]) + (1.0,)
    out = next(n for n in nodes if n.type == "OUTPUT_MATERIAL")
    src = out.inputs["Surface"].links[0].from_node if out.inputs["Surface"].is_linked else None
    if src is None or src.type != "MIX_SHADER":
        warn("street_wet: Asphalt surface no longer ends in the street-fade Mix Shader")
    ctx["helpers"]["info"]("street_wet: Asphalt darkened x%.2f (puddles x%.2f), roughness x%.2f (puddles %.2f)"
                           % (WET, PUDDLE, ROUGH, ROUGH_PUDDLE))
