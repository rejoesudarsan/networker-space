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
