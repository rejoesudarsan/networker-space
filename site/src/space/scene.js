import * as THREE from 'three'
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js'
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js'
import { RGBELoader } from 'three/examples/jsm/loaders/RGBELoader.js'
import { Reflector } from 'three/examples/jsm/objects/Reflector.js'
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js'
import { createClouds } from './clouds.js'
import { createPeople } from './people.js'

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
  uFog: { value: srgb('#d1bfc2') },
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
  material.fog = true
  return material
}

// Baked surfaces: the atlas as is, back faces filled with lime plaster so a
// clipped wall reads as a solid section, and a night grade.
const bakedUniforms = { uNight: { value: 0 }, uCap: { value: srgb(LIME) } }
function bakedMaterial(map) {
  map.colorSpace = THREE.SRGBColorSpace
  const m = new THREE.MeshBasicMaterial({ map, side: THREE.DoubleSide, toneMapped: false })
  return fogify(m, {
    uniforms: bakedUniforms,
    pars: 'uniform float uNight; uniform vec3 uCap;',
    map: `
      if (!gl_FrontFacing) diffuseColor.rgb = pow(uCap, vec3(2.2)) * 0.82;
      #if NUM_CLIPPING_PLANES > 0
        // Just under the cut, upright faces the bake never lit (wall ends
        // between rooms) show black texels that shimmer: give them the cap too.
        float underCut = clippingPlanes[0].w - dot(vClipPosition, clippingPlanes[0].xyz);
        float upness = abs(normalize(cross(dFdx(vWorldP), dFdy(vWorldP))).y);
        if (underCut < 0.14 && upness < 0.2 && dot(diffuseColor.rgb, vec3(0.333)) < 0.05) diffuseColor.rgb = pow(uCap, vec3(2.2)) * 0.82;
      #endif
      vec3 nightCol = diffuseColor.rgb * vec3(0.16, 0.19, 0.3);
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
  scene.fog = new THREE.Fog('#d1bfc2', 20, 60)   // enables the fog chunks; ours replace the maths
  const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 400)

  // The sky: a full-screen gradient with slow cloud, in the fog's colour.
  const sky = new THREE.Mesh(
    new THREE.PlaneGeometry(2, 2),
    new THREE.ShaderMaterial({
      depthTest: false,
      depthWrite: false,
      uniforms: { uFog: fogUniforms.uFog, uGlow: { value: srgb('#e8b9a8') }, uGlowK: { value: 0.5 }, uTime: fogUniforms.uTime, uAspect: { value: 1 } },
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
  const hemi = new THREE.HemisphereLight('#fff4ea', '#6b5a4c', 0.6)
  const key = new THREE.DirectionalLight('#ffe2c4', 2.2)
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
  const load = async (name) => {
    const clip = [cuts[name] || cuts.none]
    const g = await loader.loadAsync(`/models/baked/${name}-day.gltf`).catch(() => null)
    if (!g) return null
    g.scene.traverse((o) => {
      if (!o.isMesh) return
      o.material = bakedMaterial(o.material.map)
      o.material.clippingPlanes = clip
    })
    const fx = await loader.loadAsync(`/models/baked/${name}-fixtures.gltf`).catch(() => null)
    if (fx) {
      fx.scene.traverse((o) => {
        if (!o.isMesh) return
        const x = o.material.userData || {}
        const glow = !x.glass
        const m = glow
          ? new THREE.MeshBasicMaterial({ color: o.material.emissive?.getHex() ? o.material.emissive : o.material.color, toneMapped: false })
          : new THREE.MeshBasicMaterial({ color: '#cfd8d6', transparent: true, opacity: 0.22, depthWrite: false, toneMapped: false })
        if (!glow) glassMats.push(m)
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

  // ---------- the loose props (blender/tools/build_props.py) ----------
  // Only the memberships and the call use them, so they load after the first
  // frame; until then each prop is an empty slot, filled when they arrive.
  const slots = []
  const clone = (name) => {
    const g = new THREE.Group()
    slots.push([name, g])
    return g
  }
  async function loadProps() {
    const propsG = await loader.loadAsync('/models/props/props.gltf').catch(() => null)
    if (!propsG) return
    propsG.scene.traverse((o) => {
      if (o.isMesh) {
        o.castShadow = o.receiveShadow = false
        const m = o.material
        if (m.map) m.map.anisotropy = 8
        // The CC0 teak photo is pale; pull it to the palette's teak.
        if (m.name === 'Teak') m.color.set('#d4a283')
        if (m.name === 'Sandstone') m.color.set('#d8cbb0')
        fogify(m)
      }
    })
    const proto = {}
    for (const child of [...propsG.scene.children]) {
      child.position.set(0, 0, 0)
      proto[child.name] = child
    }
    for (const [name, g] of slots) {
      if (!proto[name]) continue
      const o = proto[name].clone()
      // A slot given its own scale replaces the prop's.
      if (g.scale.x !== 1) o.scale.set(1, 1, 1)
      g.add(o)
    }
  }

  let firstFrameDone
  const firstFrame = new Promise((r) => (firstFrameDone = r))
  // What waits for the first frame: the basement, then the props.
  const pending = new Set(['basement', 'props'])
  let started = false
  function later() {
    if (started) return
    started = true
    load('basement').then((g) => {
      if (g) floors.basement.add(g)
      pending.delete('basement')
      dirty = true
    })
    loadProps().finally(() => {
      pending.delete('props')
      dirty = true
    })
  }

  const clouds = createClouds(scene, fogUniforms.uFog.value)
  const people = createPeople(floors, house, fogify)

  // Memberships: three compositions on sandstone fragments; the call: one chair.
  const stage = new THREE.Group()
  stage.position.set(0, 0, -60)
  scene.add(stage)
  const tierAnchors = []
  const tier = (x, build) => {
    const g = new THREE.Group()
    g.position.set(x, 0, 0)
    const slab = clone('slab')
    g.add(slab)
    build(g)
    stage.add(g)
    const a = new THREE.Object3D()
    a.position.set(0, -0.2, 0.25)
    g.add(a)
    tierAnchors.push(a)
    return g
  }
  const put = (g, name, x, z, ry = 0) => {
    const o = clone(name)
    o.position.set(x, 0, z)
    o.rotation.y = ry
    g.add(o)
    return o
  }
  const members = new THREE.Group()
  stage.add(members)
  const tiers = [
    tier(-1.05, (g) => put(g, 'chair', 0, 0, 0.5)),
    tier(0, (g) => {
      put(g, 'armchair', 0, 0, -0.35)
      const b = put(g, 'book', 0.02, 0.03, 0.4)
      b.position.y = 0.2
      const p = put(g, 'petal', 0.15, 0.12, 1)
      p.scale.setScalar(2.2)
    }),
    tier(1.05, (g) => {
      put(g, 'table', 0, 0)
      put(g, 'chair', -0.17, 0.02, Math.PI / 2 + 0.3)
      put(g, 'chair', 0.17, 0.02, -Math.PI / 2 - 0.3)
    }),
  ]
  for (const t of tiers) members.add(t)
  const callG = new THREE.Group()
  stage.add(callG)
  const callSlab = clone('slab_wide')
  callG.add(callSlab)
  put(callG, 'chair', -0.05, 0, 0.45)
  const petal = put(callG, 'petal', 0.18, 0.12, 2)
  petal.scale.setScalar(2.4)
  const callAnchor = new THREE.Object3D()
  callAnchor.position.set(0.3, 0.2, 0)
  callG.add(callAnchor)

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
  const fovYFor = (fovX) => THREE.MathUtils.radToDeg(2 * Math.atan(Math.tan(deg(fovX) / 2) / camera.aspect))
  // The house on its street, square on from across the road at eye level,
  // alone in the fog (board 01).
  const HERO = new THREE.Vector3(0, 2.05, 0.9)
  // Distance that frames each whole floor.
  const FLOOR_DIST = { basement: 14, ground: 17.5, first: 15.5, second: 14.5 }
  const fTarget = new THREE.Vector3()

  // ---------- state ----------
  const state = {
    scene: 'exterior', focus: 0, local: 0, open: 0, night: 0, veil: 0, fog: '#d1bfc2', glow: 0.5,
    mx: 0, my: 0, still: false, tierFocus: -1, brief: 0,
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
  const tmp = new THREE.Vector3()
  orbit(shot, HERO, 0, 2, 27, 26, 0, -0.55)
  const cur = { pos: shot.pos.clone(), look: shot.look.clone(), fovY: shot.fovY }
  let lastScene = null

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

    const s = state.scene
    const changed = s !== lastScene
    const inFloors = s === 'floors'
    const outside = s === 'exterior' || inFloors
    const phone = camera.aspect < 0.8
    house.visible = outside
    stage.visible = s === 'members' || s === 'call'
    members.visible = s === 'members'
    callG.visible = s === 'call'
    winMat.emissiveIntensity = 1.4 * state.night
    lampMat.emissiveIntensity = 2.2 * state.night

    // Floors: on the street they part a little (the opening); inside, the
    // floors above the one in view rise clear and its walls are cut down.
    const weights = {}
    ORDER.forEach((id, i) => {
      const g = floors[id]
      const f = FLOORS[id]
      if (inFloors) {
        const above = smooth(0, 1, i - state.focus)
        const w = Math.max(0, 1 - Math.abs(i - state.focus))
        weights[id] = w
        g.position.y = f.y + CLEAR * above
        g.visible = above < 0.98
        cuts[id].set(new THREE.Vector3(0, -1, 0), g.position.y + lerp(WALL * 1.4, WALL * 0.48, smooth(0, 1, w)))
      } else {
        weights[id] = 0
        g.visible = true
        g.position.y = f.y + PART[id] * state.open
        cuts[id].set(new THREE.Vector3(0, -1, 0), 1e5)
      }
    })
    if (roof) roof.visible = !inFloors
    // The lower level sits below the street: while it is in view the street,
    // the compound wall and the trees step aside so it can be seen.
    const below = inFloors && state.focus < 0.6
    street.visible = site.visible = env.visible = !below
    // Fog per scene.
    const camDist = cur.pos.distanceTo(cur.look)
    if (outside) {
      fogUniforms.uNear.value = camDist * 0.95
      fogUniforms.uFar.value = camDist * 2.3
      // The low fog lies on the street, or under the floor in view.
      fogUniforms.uBedY.value = inFloors ? Math.min(0.05, lerp(FLOORS.basement.y, 0.05, Math.min(1, state.focus)) - 0.25) : 0.6
      fogUniforms.uBedDepth.value = inFloors ? 0.6 : 0.8
      fogUniforms.uSide.value = inFloors ? 0 : 1
    } else {
      fogUniforms.uSide.value = 0
      fogUniforms.uNear.value = 3.5
      fogUniforms.uFar.value = 9
      fogUniforms.uBedY.value = 0.0
      fogUniforms.uBedDepth.value = 0.4
    }
    // Night outside: the lit plaster (neighbours, walls, walkers) goes dark
    // with the house; the memberships keep their light.
    const dusk = outside ? state.night : 0
    hemi.intensity = lerp(0.6, 0.1, dusk)
    key.intensity = lerp(2.2, 0.2, dusk)
    scene.environmentIntensity = lerp(1, 0.15, dusk)

    // Cloud: a low bed along the street; round the stones for the memberships.
    if (outside) clouds.gather('street', 0, -0.2, 2.5, 9, 7, { size: 0.6, ring: 0.7, bed: 0.4 })
    else clouds.gather('stage', 0, -0.32, -60, 2.2, 1.1, { size: 0.7, ring: 0.6 })
    clouds.update(t, (outside ? 0.35 : 0.5) * (1 - state.veil * 0.5), 1 - state.night * 0.7)
    people.update(dt, t, weights, outside && !below, state.still)

    // Camera target for the scene.
    if (s === 'exterior') {
      // On a phone the brief takes the lower half; the house rises above it.
      if (phone) orbit(shot, HERO, 0, 4, 34, 40, 0, 2.2 + 4.2 * state.brief - 2.6 * state.open)
      else orbit(shot, HERO, 0, 2, 27, 26, 3.6 * state.brief, -0.55)
    } else if (inFloors) {
      const i0 = Math.min(3, Math.floor(state.focus))
      const i1 = Math.min(3, i0 + 1)
      const u = state.focus - i0
      const a = FLOORS[ORDER[i0]]
      const b = FLOORS[ORDER[i1]]
      fTarget.set(lerp(a.x, b.x, u), lerp(a.y, b.y, u) + 0.15, lerp(a.z, b.z, u) + 0.3)
      const dist = lerp(FLOOR_DIST[ORDER[i0]], FLOOR_DIST[ORDER[i1]], u)
      const drift = (state.local - 0.5) * 4
      if (phone) orbit(shot, fTarget, 28 + drift, 52, dist * 1.75, 36, 0, 1.6)
      else orbit(shot, fTarget, 30 + drift, 44, dist, 30, 2.6)
    } else if (s === 'members') {
      // A phone shows one membership at a time.
      const fx = phone ? tiers[Math.max(0, state.tierFocus)].position.x : 0
      shot.look.set(fx, phone ? -0.05 : 0.1, -60)
      shot.pos.set(fx, 0.85, -60 + 4.4)
      shot.fovY = fovYFor(phone ? 26 : 38)
    } else {
      shot.look.set(phone ? 0 : 0.25, phone ? -0.05 : 0.15, -60)
      shot.pos.set(phone ? 0 : 0.1, 0.75, -60 + 3.2)
      shot.fovY = fovYFor(phone ? 30 : 36)
    }
    // Inside a full veil the camera jumps; otherwise it eases.
    const k = state.veil > 0.97 || (changed && state.veil > 0.5) || state.still ? 1 : 1 - Math.pow(0.004, dt)
    cur.pos.lerp(shot.pos, k)
    cur.look.lerp(shot.look, k)
    cur.fovY = lerp(cur.fovY, shot.fovY, k)
    lastScene = s

    camera.position.copy(cur.pos)
    // A breath of parallax from the pointer.
    if (!state.still) {
      camera.position.x += state.mx * 0.12
      camera.position.y -= state.my * 0.08
    }
    camera.lookAt(cur.look)
    camera.fov = cur.fovY
    // Near plane with the distance: depth precision for the street's thin
    // layers (road, yards, paving millimetres apart) without z-fighting.
    camera.near = Math.min(1, Math.max(0.05, cur.pos.distanceTo(cur.look) * 0.04))
    camera.clearViewOffset()
    camera.updateProjectionMatrix()

    // The membership in focus lifts a touch.
    tiers.forEach((g, i) => {
      g.position.y = lerp(g.position.y, state.tierFocus === i ? 0.03 : 0, state.still ? 1 : 1 - Math.pow(0.001, dt))
    })

    if (state.still) {
      const key = [...camera.position.toArray(), ...cur.look.toArray(), camera.fov, width, height, state.fog, state.veil, state.night, state.open, state.focus, state.tierFocus, state.glow]
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

  // Screen position of an anchor, for the copy that sits beside objects.
  const toScreen = (obj) => {
    obj.getWorldPosition(tmp)
    tmp.project(camera)
    return { x: (tmp.x * 0.5 + 0.5) * width, y: (-tmp.y * 0.5 + 0.5) * height, behind: tmp.z > 1 }
  }

  // Where each floor's level sits on screen, for the 01 / 02 / 03 markers.
  const markerAnchors = ['ground', 'first', 'second'].map((id) => {
    const o = new THREE.Object3D()
    o.position.set(-3.4, 0.55, 5.2)
    floors[id].add(o)
    return o
  })

  return {
    state,
    people,
    // Still loading: 'basement' or 'props'. A scene that needs one stays veiled.
    pending: (what) => pending.has(what),
    // Resolves once a frame is on the canvas (shaders compiled), not before.
    firstFrame,
    quality: () => ({ gpu, weak, small, ...quality }),
    // Draw calls and triangles of the last frame, for site/PERF.md.
    info: () => ({ ...renderer.info.render, geometries: renderer.info.memory.geometries, textures: renderer.info.memory.textures }),
    markerScreens: () => markerAnchors.map(toScreen),
    tierScreens: () => tierAnchors.map(toScreen),
    callScreen: () => toScreen(callAnchor),
  }
}
