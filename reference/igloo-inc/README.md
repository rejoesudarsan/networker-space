# igloo.inc — scroll reference

Captured 2026-10-04 from https://igloo.inc/ in headless Chrome at 1440×900.
One frame per 100 px of wheel travel, 700 ms settle between ticks. The site
is a single WebGL canvas with virtual scroll (the document never moves), and
the scroll is infinite: one full loop is about 12 000 px, after which the
camera dives back into the igloo and the intro restarts.

`scroll-NNN-PPPPPpx.jpg` — frame index and cumulative wheel distance.
`interaction-NN-*.jpg` — hover and click states captured separately.

## One loop, by chapter

| Frames | px | What happens |
|---|---|---|
| 000–010 | 0–1000 | **Intro.** Igloo on a snowfield, fixed camera. Scroll pulls the ice blocks apart from the dome, with numbered survey lines between them. Left: logo, copyright. Right: "Manifesto" and the mission statement. Bottom-left: "Scroll down to discover", sound toggle. |
| 011–015 | 1100–1500 | **Reassemble.** Blocks fall back into a closed igloo. Chromatic-aberration glitch on the HUD text. Ground fog rises. |
| 016–021 | 1600–2100 | **Into the cloud.** Fog swallows the terrain, the HUD copy fades, only the logo and sound toggle remain. Faint "LOAD OFF/2" and coordinate text drift in the fog. |
| 022–035 | 2200–3500 | **Portfolio 01.** An ice block with a frozen Pudgy Penguin floats up from below, rotating. Callout: `PORTFOLIO_CO_01 / PUDGY PENGUINS`, a TEMP readout, a date, and `CLICK TO EXPLORE`. It drifts up and out of frame. |
| 036–043 | 3600–4300 | **Gap.** Empty fog with ghost text, the next block enters from the bottom. |
| 044–049 | 4400–4900 | **Portfolio 02.** `PORTFOLIO_CO_02 / OVERPASS`, same treatment. |
| 050–055 | 5000–5500 | Gap. |
| 056–061 | 5600–6100 | **Portfolio 03.** `PORTFOLIO_CO_03 / ABSTRACT`. |
| 062–068 | 6200–6800 | Last block leaves, white glowing shapes rise from below. |
| 069–077 | 6900–7700 | **The ring.** A segmented ice ring with a smaller "C" ring inside, seen head-on. It opens and brightens. |
| 078–092 | 7800–9200 | **Portal.** Camera flies through the glowing ring into a bright core, then out the other side. |
| 093–100 | 9300–10000 | **Arena, from above.** Top-down view of concentric terraces, a particle sculpture on the central dais. Camera tilts down to eye level. |
| 101–113 | 10100–11300 | **Arena.** Particle-cloud sculpture on the dais under a halo light. Left/right arrows flank it; a link label (`LinkedIn`, neighbours `Medium`, `X / Twitter`) sits on the dais rim. This is the team / contact section. |
| 114–117 | 11400–11700 | **Dissolve.** The sculpture breaks up, the arena floor glitches into terrain colour. |
| 118–119 | 11800–11900 | **Dive.** Camera falls back into the igloo from above, blocks fly past. |
| 120 → | 12000 | Loop: frame 000 again. |

## Interactions

| File | What it shows |
|---|---|
| interaction-01 | Hovering "Manifesto" at the start: no visible change at rest. |
| interaction-02 | Hovering the sound toggle. |
| interaction-03 → 04 | Portfolio 01 before and with the cursor on the block. The callout lines redraw; the block stays. |
| interaction-05 | Immediately after clicking `CLICK TO EXPLORE`. The world fades to near-black, a "Summary" panel appears with its text still scrambled, "Close" top-right, sound switches to On. |
| interaction-06 → 07 | The scramble decodes into the real summary over about five seconds. Below it: `/// Discover` with `[X] [IG] [LI] [TK]` links and `/// Visit [website]`. The frozen block is still faintly visible behind the text. |
| interaction-08 | Scrolling inside the panel does nothing: the panel is fixed, scroll is captured. |
| interaction-09 | Escape closes the panel and returns to the same block in the fog. |
| interaction-10 | Arena at rest: particle sculpture of the LinkedIn "in" on the dais, `LinkedIn` selected in the rim label, `Medium` and `X / Twitter` greyed either side. |
| interaction-11 → 13 | Clicking the right arrow morphs the particles into an X, then an M. The rim label advances with it. |
| interaction-14 | Hovering the rim label. |
| interaction-15 | Left arrow goes back to X. |
| interaction-16 | Scrolling on from the arena starts the dissolve into the dive. |

## What makes it feel the way it does

- **One object, one camera, one scroll.** Nothing on the page competes with the
  canvas. HUD text is small mono type at the corners and never overlaps the
  object.
- **Transitions are hidden in cloud.** Every scene change happens inside fog so
  the swap is never seen. Between scenes there is a deliberate empty beat.
- **Scroll maps to camera, not to a timeline.** The camera moves along a path;
  objects are placed on that path. Momentum and easing make slow ticks and
  fast ticks land differently.
- **Monochrome.** Grey-blue palette, one highlight (the cold white glow),
  chromatic aberration as the only effect.
- **Interactions are inside the world.** `CLICK TO EXPLORE` on each block, arrows
  in the arena, nothing in the chrome.
