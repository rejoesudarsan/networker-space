import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js'
import { Reflector } from 'three/examples/jsm/objects/Reflector.js'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'
import { createClouds } from './clouds.js'
import { createPeople } from './people.js'
import { SKY } from './beats.js'

// The house, baked in Blender (blender/tools/bake_site.py): each floor is one
// unlit mesh whose atlas already holds its light, so what the site shows is
// what Cycles rendered. One camera, one house on its street among its
// neighbours, fog that carries the hour. When the house opens, the camera
// visits each floor whole: the floors above lift clear and the walls of the
// floor in view are cut down to a section, so every room on it shows.
// Units: 1 = 8 ft. Floors sit in their own frames (house.json offsets).

const FLOORS = {
  basement: { y: -0.72, x: 0.416, z: 1.387 },
  ground: { y: 0.73, x: 0, z: 0 },
  first: { y: 2.18, x: -0.208, z: -0.842 },
  second: { y: 3.63, x: 0.417, z: -0.217 },
}
const ORDER = ['basement', 'ground', 'first', 'second']
// How far each floor lifts when the house parts on the street.
const PART = { basement: 0, ground: 0.32, first: 0.66, second: 1.0 }
// How far the floors above the one in view rise: clear out of the frame.
const CLEAR = 9
const WALL = 1.3
const LIME = '#e8e4da'

const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}
const lerp = (a, b, k) => a + (b - a) * k
const srgb = (hex) => {
  const c = new THREE.Color(hex)
  return new THREE.Vector3(...c.clone().convertLinearToSRGB().toArray())
}

// ---------- shared shader bits ----------
const NOISE = /* glsl */ `
  float h21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
  float vnoise(vec2 p) {
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(h21(i), h21(i + vec2(1, 0)), u.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1, 1)), u.x), u.y);
  }
  float fbm(vec2 p) {
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++) { v += a * vnoise(p); p = p * 2.03 + 17.1; a *= 0.5; }
    return v;
  }
`

// Fog every material shares: distance haze, a cloud bed below the diorama
// in view, and the colour of the hour. Mixed after the colour-space
// conversion, so the fog shows its hex exactly.
const fogUniforms = {
  uFog: { value: srgb('#dfe3e3') },
  uNear: { value: 20 },
  uFar: { value: 60 },
  uBedY: { value: -100 },
  uBedDepth: { value: 1 },
  uTime: { value: 0 },
  // Margin fog (board 01): beyond |x| = uSideX the street goes to fog, so the
  // house stands alone. uSide 0 turns it off.
  uSide: { value: 0 },
  uSideX: { value: 5 },
}
function fogify(material, extra = {}) {
  material.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, fogUniforms, extra.uniforms || {})
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWorldP;')
      .replace('#include <fog_vertex>', '#include <fog_vertex>\nvWorldP = (modelMatrix * vec4(transformed, 1.0)).xyz;')
    shader.fragmentShader = shader.fragmentShader
      .replace(
        '#include <common>',
        `#include <common>
        varying vec3 vWorldP;
        uniform vec3 uFog; uniform float uNear, uFar, uBedY, uBedDepth, uTime, uSide, uSideX;
        ${extra.pars || ''}
        ${NOISE}`,
      )
      .replace('#include <map_fragment>', `#include <map_fragment>\n${extra.map || ''}`)
      .replace('#include <clipping_planes_fragment>', extra.clip || '#include <clipping_planes_fragment>')
      .replace(
        '#include <fog_fragment>',
        `{
          float d = distance(cameraPosition, vWorldP);
          float f = smoothstep(uNear, uFar, d);
          float n = fbm(vWorldP.xz * 0.9 + vec2(uTime * 0.02, uTime * 0.013));
          float bed = smoothstep(uBedY, uBedY - uBedDepth, vWorldP.y + (n - 0.5) * 0.9);
          f = max(f, bed);
          f = max(f, uSide * smoothstep(uSideX, uSideX + 2.5, abs(vWorldP.x) + (n - 0.5) * 1.2));
          f = max(f, uSide * smoothstep(-4.0, -9.0, vWorldP.z));
          gl_FragColor.rgb = mix(gl_FragColor.rgb, uFog, clamp(f, 0.0, 1.0));
        }`,
      )
  }
  // Same function text for every fogged material: key the program on what
  // it injects, or two kinds could share one.
  const key = `fog|${extra.pars || ''}|${extra.map || ''}|${extra.clip || ''}`
  material.customProgramCacheKey = () => key
  material.fog = true
  return material
}

// Baked surfaces: the atlas as is, back faces filled with lime plaster so a
// clipped wall reads as a solid section, a cooler white balance (the
// sunrise HDRI leaves the lime plaster pink), and a night grade.
const bakedUniforms = { uNight: { value: 0 }, uCap: { value: srgb(LIME) } }
// `lit`: how far the floor's lamps are on (the floor in view, at night).
// Until each floor has its night bake, its rooms take a warm lamp grade
// instead of the cold one.
// `keep`: a world-space box (x0, z0, x1, z1) the cutaway leaves standing,
// the basement court, so its big tree still rises through the house.
function bakedMaterial(map, lit, keep) {
  map.colorSpace = THREE.SRGBColorSpace
  const m = new THREE.MeshBasicMaterial({ map, side: THREE.DoubleSide, toneMapped: false })
  return fogify(m, {
    uniforms: { ...bakedUniforms, uLit: lit, uKeep: { value: keep || new THREE.Vector4() } },
    pars: 'uniform float uNight; uniform vec3 uCap; uniform float uLit; uniform vec4 uKeep;',
    clip: `bool kept = vWorldP.x > uKeep.x && vWorldP.x < uKeep.z && vWorldP.z > uKeep.y && vWorldP.z < uKeep.w;
      if (!kept) {
      #include <clipping_planes_fragment>
      }`,
    map: `
      if (!gl_FrontFacing) diffuseColor.rgb = pow(uCap, vec3(2.2)) * 0.82;
      #if NUM_CLIPPING_PLANES > 0
        // Just under the cut, upright faces the bake never lit (wall ends
        // between rooms) show black texels that shimmer: give them the cap too.
        float underCut = clippingPlanes[0].w - dot(vClipPosition, clippingPlanes[0].xyz);
        float upness = abs(normalize(cross(dFdx(vWorldP), dFdy(vWorldP))).y);
        if (underCut < 0.14 && upness < 0.2 && dot(diffuseColor.rgb, vec3(0.333)) < 0.05) diffuseColor.rgb = pow(uCap, vec3(2.2)) * 0.82;
      #endif
      diffuseColor.rgb *= vec3(0.87, 1.0, 0.99);
      vec3 nightCol = diffuseColor.rgb * mix(vec3(0.16, 0.19, 0.3), vec3(0.62, 0.47, 0.32), uLit);
      diffuseColor.rgb = mix(diffuseColor.rgb, nightCol, uNight);
    `,
  })
}

function canWebp() {
  return new Promise((done) => {
    const img = new Image()
    img.onload = () => done(img.width === 1)
    img.onerror = () => done(false)
    img.src = 'data:image/webp;base64,UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA=='
  })
}

// ---------- the scene ----------
export async function createScene(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' })
  // Quality: phones and weak or software GPUs start lower, and a frame rate
  // that stays low steps the pixel ratio down, then settles on a still frame.
  const gl = renderer.getContext()
  const dbg = gl.getExtension('WEBGL_debug_renderer_info')
  const gpu = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : ''
  const weak = /swiftshader|llvmpipe|software|mali-[24t]|adreno \(tm\) [3-5]\d\d|powervr sgx/i.test(gpu)
  const small = Math.max(screen.width, screen.height) <= 1024
  const quality = { ratio: Math.min(devicePixelRatio, weak ? 1 : small ? 1.5 : 1.75), floor: 0.75, low: false }
  renderer.setPixelRatio(quality.ratio)
  renderer.toneMapping = THREE.ACESFilmicToneMapping
  renderer.toneMappingExposure = 1.0
  renderer.localClippingEnabled = true
  const scene = new THREE.Scene()
  scene.fog = new THREE.Fog('#dfe3e3', 20, 60)   // enables the fog chunks; ours replace the maths
  const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 400)

  // The sky: a full-screen gradient with slow cloud, in the fog's colour.
  const sky = new THREE.Mesh(
    new THREE.PlaneGeometry(2, 2),
    new THREE.ShaderMaterial({
      depthTest: false,
      depthWrite: false,
      uniforms: { uFog: fogUniforms.uFog, uGlow: { value: srgb(SKY.glow) }, uGlowK: { value: 0.5 }, uTime: fogUniforms.uTime, uAspect: { value: 1 } },
      vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.9999, 1.0); }',
      fragmentShader: `
        varying vec2 vUv; uniform vec3 uFog, uGlow; uniform float uGlowK, uTime, uAspect;
        ${NOISE}
        void main() {
          vec2 p = vec2(vUv.x * uAspect, vUv.y);
          float streak = fbm(vec2(p.x * 1.4 + uTime * 0.006, p.y * 4.0));
          float band = smoothstep(0.35, 0.75, vUv.y) * (1.0 - smoothstep(0.75, 1.0, vUv.y));
          vec3 col = mix(uFog * 0.94, uFog * 1.04, vUv.y);
          col = mix(col, uGlow, uGlowK * band * smoothstep(0.45, 0.8, streak));
          col += (fbm(p * 3.0 + uTime * 0.01) - 0.5) * 0.035;
          gl_FragColor = vec4(col, 1.0);
        }`,
    }),
  )
  sky.frustumCulled = false
  sky.renderOrder = -10
  scene.add(sky)

  // The veil: drifting cloud that fills the frame between scenes.
  const veilMat = new THREE.ShaderMaterial({
    transparent: true,
    depthTest: false,
    depthWrite: false,
    uniforms: { uFog: fogUniforms.uFog, uVeil: { value: 0 }, uTime: fogUniforms.uTime, uAspect: { value: 1 } },
    vertexShader: 'varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }',
    fragmentShader: `
      varying vec2 vUv; uniform vec3 uFog; uniform float uVeil, uTime, uAspect;
      ${NOISE}
      void main() {
        vec2 p = vec2(vUv.x * uAspect, vUv.y) * 2.2;
        float n = fbm(p + vec2(uTime * 0.03, -uTime * 0.02));
        float a = smoothstep(0.0, 1.0, uVeil * 1.6 - 0.6 + n * 0.9);
        a = max(a, smoothstep(0.85, 1.0, uVeil));
        vec3 col = uFog * (0.97 + 0.08 * n);
        gl_FragColor = vec4(col, a);
      }`,
  })
  const veil = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), veilMat)
  veil.frustumCulled = false
  veil.renderOrder = 10
  scene.add(veil)

  // Light for the loose props (the baked house needs none).
  const hemi = new THREE.HemisphereLight('#f3f5f2', '#5f5a50', 0.6)
  const key = new THREE.DirectionalLight('#fff0dc', 2.2)
  key.position.set(3, 6, 4)
  scene.add(hemi, key, key.target)
  try {
    const hdr = await new RGBELoader().loadAsync('/world/env/sunrise_1k.hdr')
    const pmrem = new THREE.PMREMGenerator(renderer)
    scene.environment = pmrem.fromEquirectangular(hdr).texture
    hdr.dispose()
    pmrem.dispose()
  } catch {
    /* props fall back to the hemisphere light */
  }

  // ---------- the baked house ----------
  // The build meshopt-compresses the glTFs (scripts/compress-models.mjs) and
  // writes WebP textures beside the JPEGs, half size for phones
  // (scripts/compress-textures.mjs). The dev server has only the JPEGs.
  const manager = new THREE.LoadingManager()
  const webp = import.meta.env.PROD && (await canWebp())
  if (webp) manager.setURLModifier((url) => (/\/models\/.*\.jpg$/.test(url) ? url.replace(/\.jpg$/, small ? '-sm.webp' : '.webp') : url))
  const loader = new GLTFLoader(manager).setMeshoptDecoder(MeshoptDecoder)
  const glassMats = []
  const glassDay = new THREE.Color('#cfd8d6')
  const glassNight = new THREE.Color('#ffb466')
  // One cutaway plane per floor (the walls cut down to a section).
  const cuts = Object.fromEntries([...ORDER, 'roof', 'site', 'none'].map((k) => [k, new THREE.Plane(new THREE.Vector3(0, -1, 0), 1e5)]))
  const lit = {}
  // The basement's Court 1 (x 0.2..2.0, z -2.08..-1.0 in its frame, a hair
  // inside its walls), where the big tree stands (court1_big_tree.py).
  const b = FLOORS.basement
  const KEEP = { basement: new THREE.Vector4(b.x + 0.26, b.z - 2.02, b.x + 1.94, b.z - 1.06) }
  const load = async (name) => {
    const clip = [cuts[name] || cuts.none]
    const g = await loader.loadAsync(`/models/baked/${name}-day.gltf`).catch(() => null)
    if (!g) return null
    g.scene.traverse((o) => {
      if (!o.isMesh) return
      o.material = bakedMaterial(o.material.map, lit[name] || (lit[name] = { value: 0 }), KEEP[name])
      o.material.clippingPlanes = clip
    })
    const fx = await loader.loadAsync(`/models/baked/${name}-fixtures.gltf`).catch(() => null)
    if (fx) {
      fx.scene.traverse((o) => {
        if (!o.isMesh) return
        const x = o.material.userData || {}
        const glow = !!x.glow
        // Glass, lamps, and anything untagged (the street gulmohars' leaves
        // and blossom, in flat colour): lit, so it goes dark with the night.
        const m = x.glass
          ? new THREE.MeshBasicMaterial({ color: '#cfd8d6', transparent: true, opacity: 0.22, depthWrite: false, toneMapped: false })
          : glow
            ? new THREE.MeshBasicMaterial({ color: o.material.emissive?.getHex() ? o.material.emissive : o.material.color, toneMapped: false })
            : new THREE.MeshLambertMaterial({ color: o.material.color, side: THREE.DoubleSide })
        if (x.glass) glassMats.push(m)
        m.clippingPlanes = clip
        o.material = fogify(m)
        o.userData.glow = glow
      })
      g.scene.add(fx.scene)
    }
    return g.scene
  }
  const house = new THREE.Group()
  scene.add(house)
  const floors = {}
  // First only what the street shows: the basement sits below the road and
  // follows after the first frame (see `later`), behind the veil into the house.
  const FIRST = ['ground', 'first', 'second', 'roof', 'site']
  const loaded = Object.fromEntries((await Promise.all(FIRST.map(load))).map((g, i) => [FIRST[i], g]))
  ORDER.forEach((id) => {
    const g = new THREE.Group()
    const f = FLOORS[id]
    g.position.set(f.x, f.y, f.z)
    if (loaded[id]) g.add(loaded[id])
    floors[id] = g
    house.add(g)
  })
  const roof = loaded.roof
  if (roof) floors.second.add(roof)
  const site = loaded.site || new THREE.Group()
  house.add(site)

  // The street: wet asphalt holding a soft, broken reflection of the house,
  // going to fog before the frame's edge (Astra frames 03 and 19).
  const street = new Reflector(new THREE.PlaneGeometry(200, 200), {
    textureWidth: weak || small ? 512 : 1024,
    textureHeight: weak || small ? 512 : 1024,
    multisample: 0,
    clipBias: 0.003,
    shader: {
      name: 'WetStreet',
      uniforms: {
        color: { value: null }, tDiffuse: { value: null }, textureMatrix: { value: null },
        uFog: { value: new THREE.Vector3() }, uNear: { value: 20 }, uFar: { value: 60 }, uTime: { value: 0 }, uNight: { value: 0 }, uMist: { value: 0 },
      },
      vertexShader: `
        uniform mat4 textureMatrix;
        varying vec4 vUv;
        varying vec3 vWorldP;
        void main() {
          vUv = textureMatrix * vec4(position, 1.0);
          vWorldP = (modelMatrix * vec4(position, 1.0)).xyz;
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }`,
      fragmentShader: `
        uniform sampler2D tDiffuse;
        uniform vec3 uFog; uniform float uNear, uFar, uTime, uNight, uMist;
        varying vec4 vUv;
        varying vec3 vWorldP;
        ${NOISE}
        void main() {
          // Ripples and puddles break the mirror up.
          float n = fbm(vWorldP.xz * 1.7);
          float puddle = smoothstep(0.45, 0.62, fbm(vWorldP.xz * 0.35 + 3.0));
          vec2 wob = vec2(fbm(vWorldP.xz * 6.0 + uTime * 0.05) - 0.5, fbm(vWorldP.zx * 6.0 - uTime * 0.04) - 0.5) * mix(0.06, 0.012, puddle);
          vec4 uv = vUv; uv.xy += wob * uv.w;
          vec3 refl = pow(max(texture2DProj(tDiffuse, uv).rgb, 0.0), vec3(1.0 / 2.2));
          vec3 asphalt = mix(uFog * 0.62, uFog * 0.5, n);
          vec3 col = mix(asphalt, refl, mix(0.22, 0.6, puddle) * mix(1.0, 1.25, uNight));
          float d = distance(cameraPosition, vWorldP);
          col = mix(col, uFog, smoothstep(uNear, uFar, d));
          // The low fog lying on the road (board 01): thick, drifting.
          col = mix(col, uFog * 0.84, uMist * mix(0.35, 0.7, fbm(vWorldP.xz * 0.4 + uTime * 0.02)));
          gl_FragColor = vec4(col, 1.0);
        }`,
    },
  })
  street.rotation.x = -Math.PI / 2
  street.position.y = -0.002
  house.add(street)

  // The neighbours: plain plaster massing, two to four storeys (photos p03,
  // p19), so the house stands in a real street at its real size.
  // Only the two sides: the row across the street would stand between the
  // camera and the house.
  const NEIGHBOURS = [
    [-10.5, 6, 9, 2.1, -0.4], [10.8, 6.4, 9.4, 2.7, -1.2], [-18, 6.4, 9, 1.8, 0], [18.4, 6.2, 9.2, 2.4, -0.3],
  ]
  const nMat = [fogify(new THREE.MeshStandardMaterial({ color: '#d9d1c4', roughness: 0.95 })), fogify(new THREE.MeshStandardMaterial({ color: '#cfc6b8', roughness: 0.95 }))]
  const winMat = fogify(new THREE.MeshStandardMaterial({ color: '#6d6460', roughness: 0.6, emissive: new THREE.Color('#ffb466'), emissiveIntensity: 0 }))
  const neighbours = new THREE.Group()
  house.add(neighbours)
  NEIGHBOURS.forEach(([x, w, d, h, z], i) => {
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), nMat[i % 2])
    m.position.set(x, h / 2, z)
    neighbours.add(m)
    // Windows on every face, a row per storey, and a parapet.
    for (let y = 0.5; y < h - 0.3; y += 0.62) {
      for (let k = -1; k <= 1; k++) {
        const front = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.34), winMat)
        front.position.set(x + k * w * 0.28, y, z + d / 2 + 0.01)
        neighbours.add(front)
        for (const sx of [-1, 1]) {
          const side = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.34), winMat)
          side.position.set(x + sx * (w / 2 + 0.01), y, z + k * d * 0.3)
          side.rotation.y = sx * Math.PI / 2
          neighbours.add(side)
        }
      }
    }
    const parapet = new THREE.Mesh(new THREE.BoxGeometry(w + 0.08, 0.14, d + 0.08), nMat[(i + 1) % 2])
    parapet.position.set(x, h + 0.07, z)
    neighbours.add(parapet)
  })

  // The street (street frame, y = 0 the asphalt), on the line the house's
  // fence keeps (site mesh: gates and piers at z 5.79..5.91, x -3.3..3.25):
  // a kerbed footpath along the compound walls, the neighbours' yards dry
  // behind them, the road, and a footpath across it (nothing built there: it
  // would stand between the camera and the house, as the board keeps the
  // foreground open). Street lamps on the near kerb.
  const env = new THREE.Group()
  house.add(env)
  const PAVE = 0.025                       // footpath top (6 cm)
  const NEAR = [5.91, 6.75]                // footpath, fence to kerb
  const FAR = [9.15, 9.97]
  const ROW = 40                           // half the street's length shown
  // Square pavers with grey joints, a stain here and there.
  const paveMat = fogify(new THREE.MeshStandardMaterial({ color: '#756e66', roughness: 0.9 }), {
    map: `{
      vec2 g = abs(fract(vWorldP.xz / 0.25) - 0.5);
      float joint = smoothstep(0.47, 0.49, max(g.x, g.y));
      diffuseColor.rgb *= (1.0 - 0.28 * joint) * mix(0.88, 1.04, fbm(vWorldP.xz * 2.3));
    }`,
  })
  // Bengaluru kerbs: painted in bands, gone soft with the weather.
  const kerbMat = fogify(new THREE.MeshStandardMaterial({ color: '#d3c39b', roughness: 0.85 }), {
    map: `diffuseColor.rgb *= mix(0.3, 1.0, step(0.5, fract(vWorldP.x / 0.5))) * mix(0.85, 1.0, fbm(vWorldP.xz * 9.0));`,
  })
  const gateMat = fogify(new THREE.MeshStandardMaterial({ color: '#3b3836', roughness: 0.6, metalness: 0.3 }))
  // Built as loose boxes, merged into one mesh per material.
  const parts = new Map()
  const add = (mat, geo, x, y, z) => {
    if (!parts.has(mat)) parts.set(mat, [])
    parts.get(mat).push(geo.translate(x, y, z))
  }
  const box = (mat, w, h, d, x, y, z) => add(mat, new THREE.BoxGeometry(w, h, d), x, y, z)
  for (const [z0, z1] of [NEAR, FAR]) {
    box(paveMat, ROW * 2, PAVE, z1 - z0, 0, PAVE / 2, (z0 + z1) / 2)
    const kz = z0 === NEAR[0] ? z1 - 0.03 : z0 + 0.03
    box(kerbMat, ROW * 2, PAVE + 0.012, 0.06, 0, (PAVE + 0.012) / 2, kz)
  }
  const yardMat = fogify(new THREE.MeshStandardMaterial({ color: '#7d766f', roughness: 0.95 }))
  for (const [x0, x1] of [[-ROW, -3.32], [3.3, ROW]]) box(yardMat, x1 - x0, 0.01, 16, (x0 + x1) / 2, 0.005, NEAR[0] - 8.13)
  // Compound walls, plot by plot, each with a pier-hung gate; the house's
  // own plot (x -3.3..3.3) is in the site mesh.
  const plots = (z, h, x0, x1) => {
    for (let a = x0; a < x1 - 0.1; ) {
      const b = Math.min(x1, a + 5.2 + ((a * 7.31) % 1.6 + 1.6) % 1.6)
      const mat = nMat[Math.abs(Math.round(a)) % 2]
      const gw = b - a > 2.4 ? 0.75 : 0
      const gx = a + 0.9 + ((a * 3.7) % 1 + 1) % 1 * (b - a - 2.4)
      for (const [s0, s1] of gw ? [[a + 0.02, gx - gw / 2], [gx + gw / 2, b - 0.02]] : [[a + 0.02, b - 0.02]]) {
        box(mat, s1 - s0, h, 0.12, (s0 + s1) / 2, h / 2, z)
        box(mat, s1 - s0 + 0.02, 0.04, 0.15, (s0 + s1) / 2, h + 0.02, z)
      }
      if (gw) {
        for (const px of [gx - gw / 2 - 0.05, gx + gw / 2 + 0.05]) box(mat, 0.1, h + 0.12, 0.14, px, (h + 0.12) / 2, z)
        for (let y = 0.06; y < h; y += 0.07) box(gateMat, gw, 0.025, 0.02, gx, y, z)
      }
      a = b
    }
  }
  plots(NEAR[0] - 0.07, 0.55, -ROW, -3.32)
  plots(NEAR[0] - 0.07, 0.55, 3.3, ROW)
  // Lamps: a pole, an arm out over the road, a warm head at night.
  const poleMat = fogify(new THREE.MeshStandardMaterial({ color: '#57534f', roughness: 0.7, metalness: 0.4 }))
  const lampMat = fogify(new THREE.MeshStandardMaterial({ color: '#d8d2c6', roughness: 0.5, emissive: new THREE.Color('#ffc27a'), emissiveIntensity: 0 }))
  for (const x of [-19, -7.4, 7.6, 19.5]) {
    const z = NEAR[1] - 0.04
    add(poleMat, new THREE.CylinderGeometry(0.025, 0.035, 3.1, 8), x, 1.55, z)
    box(poleMat, 0.03, 0.03, 0.55, x, 3.05, z + 0.26)
    box(lampMat, 0.09, 0.035, 0.2, x, 3.02, z + 0.5)
  }
  for (const [mat, geos] of parts) {
    env.add(new THREE.Mesh(mergeGeometries(geos), mat))
    geos.forEach((g) => g.dispose())
  }

  let firstFrameDone
  const firstFrame = new Promise((r) => (firstFrameDone = r))
  // What waits for the first frame: the basement, below the road.
  const pending = new Set(['basement'])
  let started = false
  function later() {
    if (started) return
    started = true
    load('basement').then((g) => {
      if (g) floors.basement.add(g)
      pending.delete('basement')
      dirty = true
    })
  }

  const clouds = createClouds(scene, fogUniforms.uFog.value)
  const people = createPeople(floors, house, fogify)

  // ---------- cameras ----------
  // Shots orbit a target: azimuth from the street side (degrees, + from the
  // east), elevation, distance, vertical field of view, and `side`: how far
  // (units) the subject sits right of centre, leaving the left for copy.
  const shot = { pos: new THREE.Vector3(), look: new THREE.Vector3(), fovY: 30 }
  const deg = THREE.MathUtils.degToRad
  const right = new THREE.Vector3()
  function orbit(out, target, azD, elD, dist, fovY, side = 0, drop = 0) {
    const az = deg(azD)
    const el = deg(elD)
    right.set(Math.cos(az), 0, -Math.sin(az))
    out.look.copy(target).addScaledVector(right, -side)
    out.look.y -= drop
    out.pos.set(out.look.x + Math.sin(az) * Math.cos(el) * dist, out.look.y + Math.sin(el) * dist, out.look.z + Math.cos(az) * Math.cos(el) * dist)
    out.fovY = fovY
  }
  // The house on its street, from above and three-quarters on, its
  // neighbours either side (the earlier "house world" view).
  const HERO = new THREE.Vector3(-0.3, 1.9, 0.9)
  // Each floor from its own side, the earlier world's swing round the house
  // (src/world/world.js SHOTS): azimuth, elevation, and the distance that
  // frames the whole floor.
  const FLOOR_VIEW = {
    basement: { az: -28, el: 42, dist: 17 },
    ground: { az: 24, el: 38, dist: 20 },
    first: { az: -34, el: 42, dist: 20.5 },
    second: { az: -58, el: 42, dist: 19 },
  }
  // At night the open house is seen from the lit side.
  const NIGHT_VIEW = { az: 32, el: 38 }
  // The street shot through the day: [progress, azimuth, elevation, distance].
  // Low at dawn, rising before it dives in; lower again as the house closes.
  const STREET = [[0, 30, 13, 34], [0.1, 28, 22, 34], [0.86, 34, 26, 32], [1, 38, 19, 31]]
  const street3 = (p) => {
    let i = 0
    while (i < STREET.length - 2 && p > STREET[i + 1][0]) i++
    const a = STREET[i]
    const b = STREET[i + 1]
    const k = smooth(a[0], b[0], p)
    return a.map((v, j) => lerp(v, b[j], k))
  }
  const fTarget = new THREE.Vector3()

  // ---------- room pins ----------
  // The rooms the copy names, pinned on the floor in view: [name, x, z] in
  // the floor's frame, from the fit-out modules (blender/details/*.py).
  const PINS = {
    basement: [['Founders’ lounge', 0.7, 0.7], ['The tree court', 1.1, -1.54], ['Work area', 0.97, -2.84]],
    ground: [['Café', 1.5, 2.27], ['Coffee bar', -0.63, -1.45], ['Garden', 0.4, 4.1]],
    first: [['Event room', 1.72, 2.9], ['Courtyard', 1.66, 0.94], ['PS5 room', 1.46, -2.13], ['Game room', -0.97, 3.24], ['Library', 0.2, -1.46]],
    second: [['Quiet room', 1.1, 2.1], ['Quiet room', 0.18, -2.48], ['Terrace', -1.58, 0]],
  }
  const pinLayer = document.createElement('div')
  pinLayer.className = 'pins'
  pinLayer.setAttribute('aria-hidden', 'true')
  document.body.appendChild(pinLayer)
  const pins = Object.entries(PINS).flatMap(([floor, list]) => list.map(([name, x, z]) => {
    const el = document.createElement('span')
    el.className = 'pin'
    el.textContent = name
    pinLayer.appendChild(el)
    return { floor, el, at: new THREE.Vector3(x, 0.35, z), shown: -1 }
  }))
  const pv = new THREE.Vector3()
  function placePins(weights, inside, veil) {
    const show = smooth(0.85, 1, inside) * (1 - smooth(0.1, 0.4, veil))
    for (const p of pins) {
      const g = floors[p.floor]
      let o = show * smooth(0.6, 0.95, weights[p.floor] / Math.max(inside, 1e-3))
      if (o > 0.01) {
        pv.copy(p.at)
        g.localToWorld(pv).project(camera)
        if (pv.z > 1 || Math.abs(pv.x) > 0.96 || Math.abs(pv.y) > 0.92) o = 0
        else p.el.style.transform = `translate(${((pv.x + 1) / 2) * width}px, ${((1 - pv.y) / 2) * height}px)`
      }
      o = Math.round(o * 50) / 50
      if (o !== p.shown) {
        p.shown = o
        p.el.style.opacity = o
        p.el.style.visibility = o ? 'visible' : 'hidden'
      }
    }
  }

  // ---------- state ----------
  const state = {
    scene: 'exterior', p: 0, inside: 0, focus: 0, local: 0, open: 0, night: 0, veil: 0, fog: '#dfe3e3', glow: 0.5,
    mx: 0, my: 0, still: false,
  }
  let width = 1
  let height = 1
  function resize() {
    width = canvas.clientWidth
    height = canvas.clientHeight
    renderer.setSize(width, height, false)
    camera.aspect = width / height
    sky.material.uniforms.uAspect.value = camera.aspect
    veilMat.uniforms.uAspect.value = camera.aspect
  }
  resize()
  addEventListener('resize', resize)

  const clock = new THREE.Clock()
  orbit(shot, HERO, 36, 21, 32, 30, 2.6)
  const cur = { pos: shot.pos.clone(), look: shot.look.clone(), fovY: shot.fovY }

  // Frame-rate watch: two-second windows, from three seconds after the first frame.
  const watch = { from: 0, frames: 0, slow: 0 }
  function pace(now) {
    if (!watch.from) watch.from = now + 3000
    if (now < watch.from || state.still) return
    watch.frames++
    if (now - watch.from < 2000) return
    const fps = (watch.frames * 1000) / (now - watch.from)
    watch.from = now
    watch.frames = 0
    if (fps >= 28) return (watch.slow = 0)
    if (quality.ratio > quality.floor) {
      quality.ratio = Math.max(quality.floor, quality.ratio * 0.8)
      renderer.setPixelRatio(quality.ratio)
      resize()
    } else if (fps < 18 && ++watch.slow >= 2) {
      quality.low = true
    }
  }
  // Still (reduced motion, or the frame rate gave out): time stops, nothing
  // drifts, and a frame is drawn only when what it shows has changed.
  let tStill = 0
  let shown = ''
  let dirty = true

  function frame(now) {
    const dt = Math.min(clock.getDelta(), 0.05)
    pace(now)
    if (quality.low) state.still = true
    if (!state.still) tStill = clock.elapsedTime
    const t = tStill
    fogUniforms.uTime.value = t
    fogUniforms.uFog.value.copy(srgb(state.fog))
    sky.material.uniforms.uGlowK.value = state.glow
    veilMat.uniforms.uVeil.value = state.veil
    bakedUniforms.uNight.value = state.night
    {
      const u = street.material.uniforms
      u.uFog.value.copy(fogUniforms.uFog.value)
      u.uNear.value = fogUniforms.uNear.value
      u.uFar.value = fogUniforms.uFar.value
      u.uTime.value = t
      u.uNight.value = state.night
      u.uMist.value = fogUniforms.uSide.value * lerp(1, 0.6, state.night)
    }
    // Until the night bake lands: lit windows are warm glass.
    for (const m of glassMats) {
      m.color.copy(glassDay).lerp(glassNight, state.night)
      m.opacity = lerp(0.22, 0.9, state.night)
    }

    // How far into the open house: 0 on the street, 1 with a floor in view.
    // It runs continuously, so the house opens as the camera flies in.
    const inside = state.inside
    const inFloors = inside > 0.5
    const phone = camera.aspect < 0.8
    winMat.emissiveIntensity = 1.4 * state.night
    lampMat.emissiveIntensity = 2.2 * state.night

    // Floors: on the street they part a little (the opening); inside, the
    // floors above the one in view rise clear and its walls are cut down.
    const weights = {}
    ORDER.forEach((id, i) => {
      const g = floors[id]
      const f = FLOORS[id]
      const above = smooth(0, 1, i - state.focus)
      const w = Math.max(0, 1 - Math.abs(i - state.focus))
      weights[id] = w * inside
      g.position.y = f.y + lerp(PART[id] * state.open, CLEAR * above, smooth(0, 1, inside))
      g.visible = above * inside < 0.98
      // The walls drop to a section as the camera comes in.
      const section = lerp(WALL * 1.4, WALL * 0.48, smooth(0, 1, w))
      cuts[id].set(new THREE.Vector3(0, -1, 0), inside < 0.01 ? 1e5 : g.position.y + lerp(WALL * 6, section, smooth(0, 0.8, inside)))
    })
    if (roof) roof.visible = inside < 0.25
    // The lower level sits below the street: while it is in view the street,
    // the compound wall and the trees step aside so it can be seen.
    const below = inFloors && state.focus < 0.6
    street.visible = site.visible = env.visible = !below
    // Fog per scene.
    const camDist = cur.pos.distanceTo(cur.look)
    // The house in view stays sharp; the fog takes only what lies beyond it.
    fogUniforms.uNear.value = camDist * 1.2
    fogUniforms.uFar.value = camDist * 2.6
    // The low fog lies on the street, or under the floor in view.
    fogUniforms.uBedY.value = lerp(0.05, Math.min(0.05, lerp(FLOORS.basement.y, 0.05, Math.min(1, state.focus)) - 0.25), smooth(0, 1, inside))
    fogUniforms.uBedDepth.value = 0.6
    // No margin fog: the street and its neighbours stay in view.
    fogUniforms.uSide.value = 0
    // Night: the lit plaster (neighbours, walls, walkers) goes dark with the house.
    const dusk = state.night
    hemi.intensity = lerp(0.6, 0.05, dusk)
    key.intensity = lerp(2.2, 0.08, dusk)
    scene.environmentIntensity = lerp(1, 0.06, dusk)

    // Cloud: a low bed along the street.
    clouds.gather('street', 0, -0.2, 2.5, 9, 7, { size: 0.6, ring: 0.7, bed: 0.4 })
    clouds.update(t, 0.35 * (1 - state.veil * 0.5), 1 - state.night * 0.7)
    people.update(dt, t, weights, !below, state.still)

    // Camera: the street shot and the floor shot, blended by how far in we
    // are, so the move from one to the other is a flight, not a cut. The
    // orbit is what blends (angle, height, distance), so the camera arcs
    // round the house instead of passing through it.
    {
      // On a phone the copy takes the lower half; the house sits above it.
      const [, az, el, dist] = street3(state.p)
      const out = phone ? [az, el + 2, dist * 1.22, 40, 0, 4.4] : [az, el, dist, 30, 3.2, 0]
      const i0 = Math.min(3, Math.floor(state.focus))
      const i1 = Math.min(3, i0 + 1)
      const u = smooth(0, 1, state.focus - i0)
      const a = FLOORS[ORDER[i0]]
      const b = FLOORS[ORDER[i1]]
      const va = FLOOR_VIEW[ORDER[i0]]
      const vb = FLOOR_VIEW[ORDER[i1]]
      // Never parked: the camera drifts round and in through each chapter.
      const night = smooth(0.72, 0.78, state.p)
      // (A slow wave on the whole scroll, so it never jumps at a chapter's edge.)
      const fAz = lerp(lerp(va.az, vb.az, u), NIGHT_VIEW.az, night) + Math.sin(state.p * 42) * 5
      const fEl = lerp(lerp(va.el, vb.el, u), NIGHT_VIEW.el, night)
      const fDist = lerp(va.dist, vb.dist, u) * (1 - 0.04 * Math.sin(state.p * 29))
      const into = phone ? [fAz, fEl + 8, fDist * 1.95, 36, 0, 2.9] : [fAz, fEl, fDist, 30, 3.0, 0]
      const k = smooth(0, 1, inside)
      fTarget.set(lerp(a.x, b.x, u), lerp(a.y, b.y, u) + 0.15, lerp(a.z, b.z, u) + 0.3).lerpVectors(HERO, fTarget, k)
      const [oAz, oEl, oDist, oFov, oSide, oDrop] = out.map((v, j) => lerp(v, into[j], k))
      // The pointer turns the view round the house a little.
      const look = state.still ? 0 : 1
      orbit(shot, fTarget, oAz + state.mx * 5 * look, oEl - state.my * 3 * look, oDist, oFov, oSide, oDrop)
    }
    // The camera eases after the shot; only a full veil (a floor still
    // loading) lets it jump.
    const k = state.veil > 0.97 || state.still ? 1 : 1 - Math.pow(0.0015, dt)
    cur.pos.lerp(shot.pos, k)
    cur.look.lerp(shot.look, k)
    cur.fovY = lerp(cur.fovY, shot.fovY, k)

    camera.position.copy(cur.pos)
    camera.lookAt(cur.look)
    camera.fov = cur.fovY
    // Near plane with the distance: depth precision for the street's thin
    // layers (road, yards, paving millimetres apart) without z-fighting.
    camera.near = Math.min(1, Math.max(0.05, cur.pos.distanceTo(cur.look) * 0.04))
    camera.clearViewOffset()
    camera.updateProjectionMatrix()
    camera.updateMatrixWorld()
    placePins(weights, inside, state.veil)
    // From the street at night the whole house keeps a low glow.
    for (const id of ORDER) if (lit[id]) lit[id].value = state.night * Math.max(smooth(0.5, 1, weights[id]), 0.4 * (1 - inside))

    if (state.still) {
      const key = [...camera.position.toArray(), ...cur.look.toArray(), camera.fov, width, height, state.fog, state.veil, state.night, state.open, state.focus, state.glow]
        .map((v) => (typeof v === 'number' ? v.toFixed(4) : v)).join()
      if (key === shown && !dirty) return
      shown = key
      dirty = false
    }
    renderer.render(scene, camera)
    if (!started) {
      performance.mark('first-frame')
      firstFrameDone()
      later()
    }
  }
  renderer.setAnimationLoop(frame)

  return {
    state,
    people,
    // Still loading: 'basement'. A scene that needs it stays veiled.
    pending: (what) => pending.has(what),
    // Resolves once a frame is on the canvas (shaders compiled), not before.
    firstFrame,
    quality: () => ({ gpu, weak, small, ...quality }),
    // Draw calls and triangles of the last frame, for site/PERF.md.
    info: () => ({ ...renderer.info.render, geometries: renderer.info.memory.geometries, textures: renderer.info.memory.textures }),
  }
}
