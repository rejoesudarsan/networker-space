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
