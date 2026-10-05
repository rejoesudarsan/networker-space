# Performance

## Baseline (5 Oct 2026, commit 32f0aa5)

How measured: `npm run build`, `vite preview`, headless Chromium (this host, no GPU:
SwiftShader software WebGL, local network), real time, 2 runs per viewport.
Times are from navigation start (Performance API marks `first-frame`, set after
the first `renderer.render`, and `house-shown`, set when `body.ready` fades the
stage in). Draw calls and triangles from `renderer.info.render` at the hero
(dev build, `window.__world.info()`).

### Size
- `dist/`: 43 MB on disk; `dist/models/`: 39 MB, of which 51 files in `baked/`.
- `dist/models/blender/` (13 MB) and `dist/models/*.glb` are only used by the old
  `src/world/` scene, which nothing imports: shipped but never fetched.
- JS: `scene-*.js` 664 kB (173 kB gzip), `index-*.js` 12 kB; CSS 15 kB; fonts ~0.4 MB.

### What the first load fetches (same on desktop and phone)
- 45 requests, 22.3 MB (encoded; the preview server does not compress `.bin`).
- Largest: `ground-day.bin` 6.9 MB, `first-day.bin` 3.1 MB, `second-day.bin` 1.8 MB,
  `basement-day.bin` 1.6 MB, `site-day.bin` 1.3 MB, `sunrise_1k.hdr` 1.3 MB.
- Every floor loads before anything shows; the hero needs only site, ground,
  roof and the outside of the upper floors.

### Times
| viewport | first contentful paint | house-shown | first-frame |
|---|---|---|---|
| desktop 1280×800 | 0.68–0.79 s | 2.96–3.10 s | 6.02–6.16 s |
| phone 390×844 | 0.72 s | 2.96–3.08 s | 6.04–6.08 s |

`house-shown` comes ~3 s **before** `first-frame`: the stage starts fading in
while the first frame is still compiling shaders, so the fade can begin on an
empty canvas. (For the loading-state item: mark ready after the first frame.)
Software rendering exaggerates compile and frame time; a real GPU will be
faster, but the order of events is the same.

### Rendering at the hero
| viewport | draw calls | triangles | geometries | textures |
|---|---|---|---|---|
| desktop | 115 | 214 k | 66 | 12 |
| phone | 59 | 211 k | 37 | 11 |

Headless frame rate here is ~1 fps (software), so not a useful number; measure
fps on a real phone in the adaptive-quality item.

## lazy-floors (5 Oct 2026)
The street view needs ground, first, second, roof and site (the closed house is
made of the floors' own walls), so only the basement (2.3 MB, below the road)
and the props (1.2 MB + textures, memberships and call only) wait for the first
frame. A scene that needs one before it arrives stays veiled.
- Bytes before the first frame: 22.3 MB → 18.3 MB (total unchanged).
- house-shown: ~3.0 s → 1.3–1.5 s; first-frame: ~6.0 s → 2.9 s desktop, 5.7 s phone (SwiftShader).

## compress-geometry (5 Oct 2026)
`npm run build` now runs `scripts/compress-models.mjs` after Vite: every glTF in
`dist/models/baked` and `dist/models/props` gets dedup + reorder + quantize
(positions 14 bit, UVs 16 bit or float where out of [0,1]) + EXT_meshopt_compression.
`public/` is untouched; the dev server still serves the raw bake. The loader has
the meshopt decoder. Compressed and raw renders compared side by side: no visible difference.
- glTF geometry: 18.2 MB → 4.9 MB (ground-day 6.9 MB → 1.7 MB; site 1.3 MB → 0.39 MB; props 1.1 MB → 0.43 MB).
- Bytes before the first frame: 18.3 MB → 8.4 MB; whole page 22.3 MB → 10.6 MB.
- On localhost the times did not move (house-shown 2.6–2.9 s, first-frame 5.5–5.9 s,
  SwiftShader, noisy): bytes are nearly free locally. The win is on a real network:
  ~10 MB less, e.g. ~16 s less on a 5 Mbit/s phone link.
- Textures (JPEG atlases + HDR) are now the largest part: ~5.7 MB of what remains.

## compress-textures (5 Oct 2026)
`scripts/compress-textures.mjs` (in `npm run build`) writes, next to each JPEG in
`dist/models`, a WebP (q80, same size) and a `-sm.webp` at half size. The loader's
URL modifier picks WebP when the browser decodes it (else the JPEG) and the
`-sm` tier when the screen's long side is ≤ 1024 px. Production only.
- Textures: 7.4 MB JPEG → 2.6 MB WebP → 1.1 MB phone tier (atlases 2048 → 1024 on phones).
- Whole first load (to the ground floor): desktop 10.6 → 7.7 MB, phone 10.6 → 6.7 MB.
- Before the first frame: desktop 6.2 MB, phone 5.6 MB.
- KTX2/Basis not done: it would cut GPU memory too, but needs a transcoder
  (~0.5 MB wasm) and a toktx/basisu step; worth it if phones show memory trouble.
- Left: `world/env/sunrise_1k.hdr` 1.3 MB, used only for prop lighting.

## adaptive-quality (5 Oct 2026)
- Start tier: pixel ratio ≤ 1.75 (desktop), ≤ 1.5 (screen long side ≤ 1024),
  1 on weak/software GPUs (SwiftShader, llvmpipe, old Mali/Adreno/PowerVR by
  renderer string); street reflection 1024² → 512² on phones and weak GPUs.
- Watch: from 3 s after the first frame, 2 s windows; under 28 fps the pixel
  ratio steps ×0.8 down to 0.75; then two windows under 18 fps → still frame.
- Still frame (that, or `prefers-reduced-motion`): time stops (fog, cloud,
  walkers, parallax), the camera cuts instead of easing, and a frame is drawn only
  when the camera, size, fog, veil or scene state changes.
- Headless here (SwiftShader, ~1 fps): detected weak, 1 → 0.8 → 0.75, then still;
  jumping to a floor still redraws. `window.__world.quality()` with `?debug`.

## loading-state (5 Oct 2026)
- `house-shown` (the fog lifting, `body.ready`) now waits for the first drawn
  frame: before, it came ~3 s before it; now 1 ms after (5.99 s / 5.99 s here).
- The loader counts real bytes off the network (models + light) against the
  sizes the server announced so far: "Preparing the house 5.8 MB" and a hairline.
- No WebGL / `?still` / a failed load: the reader opens on a still of the house
  (`public/still/house-dawn.webp` 40 kB, `.jpg` 83 kB fallback, lazy), then the
  full copy, now including the day/night rhythm, Inside and Evenings.

## cache (5 Oct 2026)
`public/_headers` (Cloudflare static assets; rules kept from overlapping since
matching rules merge). `scripts/hash-models.mjs` (last step of `npm run build`)
moves every buffer and texture the glTFs reference, with its WebP tiers, to
`dist/models/immutable/<name>.<sha256:10>.<ext>` and rewrites the glTF URIs, so a
new bake never pairs a fresh .gltf with a stale cached .bin.
- `/`, `/index.html`, `/models/baked/*`, `/models/props/*` (.gltf only):
  `max-age=0, must-revalidate` (ETag revalidation).
- `/assets/*` (Vite-hashed) and `/models/immutable/*`: `max-age=31536000, immutable`.
- `/world/*`, `/still/*`, `/favicon.svg`: `max-age=3600, stale-while-revalidate=86400`.
Checked with `wrangler dev`: each route answers with its header; the page loads
with no 4xx. A repeat visit revalidates only the small .gltf files and the HTML.

Fix found here: the compress-geometry step had quantized the props, and the
scene's prop placement reset the dequantizing transform (memberships rendered as
huge orange planes in the build only). The script now nests each prop under a
layout node first; memberships and call checked against the raw files.
