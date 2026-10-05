# The website: performance, polish, copy, and the way to a membership

Worked by a Ralph loop, one item per iteration (prompt: `site/RALPH.md`).
The site is `site/` (Vite + Three.js; the page is `index.html`, the scroll story
`src/space/`). `PRODUCT.md` and `DESIGN.md` at the repo root are the brief.

Markers: `[ ]` to do, `[x]` done, `[-]` skipped after three failures, `[?]` needs the user.

Rules:
- **Done** means: `npm run build` passes, and you have looked at the change in a
  headless browser (desktop 1280×800 and phone 390×844) and it reads right.
  Headless WebGL on this host is software-rendered: keep screenshots ≤ 960 px
  and wait ~20 s after a load before you capture.
- Never fabricate prices, member names, testimonials, partner logos, an address
  or dates (PRODUCT.md, "Evidence on Hand"). Where a fact is missing, write the
  copy so it does not need it, or leave a clearly marked placeholder and add a
  `[?]` item with the question.
- Do not edit `blender/` or `site/public/models/baked/`: the bake loop owns them.
  If the site needs something from the bake, add a `[?]` item.
- Copy: plain, specific, short. No marketing filler ("elevate", "unlock",
  "seamless", "curated", "vibrant", "community-driven"). Say what happens, when,
  and for whom. Keep the existing voice in `index.html`.
- Every path ends at a membership: each section should leave the reader one
  clear next step.

The user's latest plan (5 Oct 2026), newer than PRODUCT.md where they differ:
- Ground floor a walk-in café; basement open work area with a maker space and
  a "maker's table"; the basement office a private founders' lounge (premium);
  a seating platform round the big tree; first floor events with informal
  seating and private rooms; two quiet founder work rooms above; the terrace
  for grills, work and rooftop parties.
- 08:00–18:00 work and learn (breakfast, work, maker's table, workshops).
  After 18:00 no working: meetups, learning events, movie nights, PlayStation,
  rooftop parties, lounge access.
- Three ways in: walk-in (pay as you go), one paid membership, and a lifetime
  membership capped at 20 people. What each unlocks is still being decided:
  draft it from the zones above and mark it as a `[?]` for the user to confirm.

## Performance
- [x] measure: record a baseline in `site/PERF.md`: `dist/` size, the largest assets, time to first frame and to the house showing on desktop and phone viewports (Performance API marks), and draw calls / triangles from `renderer.info` on the hero. Done: PERF.md; first load 22.3 MB / 45 requests, house-shown ~3.0 s, first-frame ~6.0 s (software GL), hero 115 calls / 214 k tris desktop.
- [x] lazy-floors: load only what the hero needs first (site, ground, roof, street); fetch the other floors after the first frame or when the scroll nears them. No pop-in: a floor not loaded yet stays veiled. Done: basement and props load after the first frame, held behind the veil if reached early (the hero needs every above-ground floor: their walls are the façade). 4 MB less before first frame; house-shown 3.0 → 1.4 s.
- [x] compress-geometry: serve the baked glTFs with meshopt (or Draco) compression via a build step that writes to `dist/` only; leave `public/models/baked/` as the bake writes it. Record the size win in PERF.md. Done: meshopt + quantize in `scripts/compress-models.mjs` (runs in `npm run build`); geometry 18.2 → 4.9 MB, first load 22.3 → 10.6 MB.
- [x] compress-textures: atlases as KTX2/Basis (or at least resized WebP with a JPEG fallback); a smaller tier for phones. Record the win. Done: WebP + half-size phone tier written to dist (`scripts/compress-textures.mjs`), JPEG fallback; textures 7.4 → 2.6 MB (1.1 MB phone); first load 7.7 MB desktop / 6.7 MB phone.
- [x] adaptive-quality: cap pixel ratio and Reflector resolution on phones and weak GPUs; drop to a still frame when the frame rate stays low; respect `prefers-reduced-motion`. Done: start tier by screen/GPU (ratio 1.75/1.5/1, reflector 1024/512), fps watch steps ratio to 0.75 then a still frame; reduced motion = still frame drawn on change only.
- [x] loading-state: a quiet loading state in the design's style (no spinner), progress from real bytes, and a no-WebGL fallback showing a still image of the house with the full copy. Done: loader shows bytes received and a hairline filling against announced sizes; the fog lifts only after the first drawn frame; the reader (no WebGL, ?still, failure, noscript) opens on a still render of the house and carries the full copy.
- [x] cache: long-lived cache headers for hashed assets in the Cloudflare config (`wrangler.jsonc` / `_headers`); check the HTML stays fresh. Done: `public/_headers`; model buffers/textures content-hashed into `/models/immutable/` (1 year, immutable), HTML and .gltf revalidate; verified with `wrangler dev`. Also fixed a build-only props regression from compress-geometry.

## Polish
- [x] hero-board01 (user, 5 Oct): the hero rebuilt to look like art-direction board 01/07: square-on street camera at eye level, house centred at ~54% of the frame height, margin fog beyond |x| 5 and behind the house, a fog bed on the road; first frame shows only the four corners; the brief fades in with the first scroll as the house steps right (on a phone, up). Board 06's night uses the same camera.
- [x] two-angles (user, 5 Oct): opens on the house with the brief (as the earlier version), the first scroll goes straight into the house; only two camera angles: the street (board 01, no pan) and one fixed cutaway angle rising floor to floor (drift removed); the opening/markers beat and the chair-on-stone memberships and call scenes are gone: night, memberships and the call are copy in the fog margin beside the lit house. Props no longer load.
- [x] flicker-aa: check the hero, each floor and the night beat for z-fighting, shimmering edges and flicker; fix (polygon offset, depth, AA). Done: near plane scales with camera distance (0.05 → up to 1.0; ~20× depth precision on the street's mm-apart layers); unlit wall ends exposed by the floor cut (black dashes that shimmer) painted with the plaster cap; lights dim outdoors at night so side walls and walkers no longer glow white. MSAA was already on.
- [x] phone-layout: every beat on a 390×844 phone: copy never covers the house's key part, tap targets ≥ 44 px, no horizontal scroll, safe areas. Done: all 10 beats toured at 390×844; no horizontal scroll; tier tabs widened to 44 px (only targets under); phone floor camera pulled back and up so captions no longer cover the floors; corners, sheet close and bottom panels clear safe areas (env(safe-area-inset-*)).
- [x] scroll-feel: scroll pacing per beat; veils neither too long nor abrupt; the captions appear in time; keyboard and trackpad both feel right. Done: wheel/trackpad capped at 0.025 per event (a fling can't skip a beat); touch slowed to 1/8 of the day per full swipe; Space/Page keys go beat to beat (STOPS), arrows 0.015; resting inside a veil carries on to the next beat in the direction of travel after 0.7 s.
- [x] a11y: semantic headings in order, focus states, the booking sheet traps focus and closes on Esc, alt text / aria for the canvas, contrast of copy on every fog colour (WCAG AA). Done: headings h1 → h2 (floors, night, memberships, call) → h3 (tiers); copy not in view and the faded loader are `inert`; a skip link "Read it as text" opens the reader and focuses it; sheet is a native modal (focus stays in, Esc closes, focus returns: tested); canvas stays aria-hidden (text equivalents everywhere). Contrast computed over the whole day: all copy ≥ 4.5:1 (soft light text raised to 0.9); only the corner labels during the 17:00–18:00 move dip below (3.4:1, mid-grey fog), given a halo. Also restored the sheet/loader/reader CSS that the two-angles commit had deleted.
- [x] meta: title, description, Open Graph image (a render of the house), favicon set, theme colour. Done: canonical, description, Open Graph + Twitter card with `og.jpg` (1200×630 from the street view still), new favicon (the house's stepped façade and tower on dawn fog; SVG + 32 px + 180 px apple-touch), theme colour #d1bfc2.

## Copy
- [x] copy-audit: read every line on the page in order, as a founder seeing it first. List in this file what is vague, repeated or missing; then rewrite `index.html`, `FLOOR_COPY` and `TIERS` in one pass. Done: audit below; `index.html` (brief, night, memberships, call, reader), `FLOOR_COPY` and `TIERS` rewritten to the 5 Oct plan.
  Audit (5 Oct, read in order as a founder seeing it first):
  1. Brief, "To join: three memberships, each starting with a call": out of date. The plan is walk-in (pay as you go), one membership, and a lifetime membership for 20.
  2. "A house for work, shared interests and time together": vague; says nothing about what happens. Say work and learn by day, meet after six.
  3. "By day: a walk-in café": half the day. The plan's day is work and learn (breakfast, desks, the maker's table, workshops), the café is one floor of it.
  4. Floor titles are moods, not facts ("Read. Talk. Bring the room together.", "The day opens into evening."). A first-time reader can't tell what each floor is for.
  5. Lower level lists quiet work rooms and a games room; the plan makes it the open work area, the maker space and maker's table, the platform round the big tree, and the founders' lounge.
  6. First floor lists a library and game room; the plan makes it the events floor, with informal seating and private rooms.
  7. Second floor lists quiet rooms and a phone booth; the plan has two quiet founder work rooms and the terrace for grills, work and rooftop parties.
  8. Repeated: "Membership shapes your access" (×3) and "Access depends on membership" (×3) say nothing; cut to one honest line where access is actually explained (the memberships).
  9. Night lists talks, demo nights, music and long dinners; the plan's evenings are meetups, learning events, film nights, PlayStation, rooftop parties, lounge access. And the plan's rule "no work after 18:00" is missing.
  10. Tiers Visit / Regular / House with "Needs —": names and contents out of date; walk-in needs nothing, which can be said.
  11. The call says only "Book a call"; a walk-in doesn't need one. Say they can just come in.
  12. Missing and not to be invented: prices, address beyond HSR Layout, dates, how often evenings run.
- [ ] floor-copy: each floor caption says what you do there and when (morning work, the café, the court and library, the evening on the terrace), using the zone plan in `PRODUCT.md` and `DESIGN.md`.
- [ ] night-copy: what an evening is: the kinds of nights (talks, demo nights, dinners, film nights, rooftop), how often, who comes, how a member gets in. No made-up dates or names.

## The way to a membership
- [ ] tiers-detail: each membership shows what it includes, what it needs (eligibility), who it is for, and its hours/access, side by side and comparable at a glance. Prices: a placeholder only, plus a `[?]` item for the user.
- [ ] how-to-join: a short "How joining works" beat between the memberships and the call: 1. book a call, 2. visit the house, 3. get your invite, 4. first day in. Each step one line.
- [ ] faq: 6–8 short answers prospects will ask (Can I walk in? Can I bring guests or my team? Is there a desk for me? Wi-Fi, calls, quiet? Evenings without membership? Lifetime tier?). Answer only from PRODUCT.md and the notes above; anything unknown becomes a `[?]`.
- [ ] apply-form: replace the dead "Book a call" sheet with a short apply form (name, email, what you are building, which membership, how you heard). It submits to a Cloudflare Worker endpoint or Formspree-style service: build it behind one config value, add a `[?]` for which service and inbox, and show a clear thank-you state ("We'll write within two days to set up a call").
- [ ] membership-cta: every beat ends with one next step toward a membership (the right tier pre-selected in the form when coming from a tier).
- [ ] end-to-end: walk the whole path on desktop and phone, from first frame to the thank-you state; fix anything that breaks the flow. Then output the promise.

## Needs your input
- [?] the three ways in (drafted in `TIERS`, src/space/beats.js): confirm what each unlocks. Drafted: Walk-in = café + open work area 08:00–18:00, pay as you go; Member = every day 08:00–23:00, the maker's table and workshops, the evening programme, private rooms to book; Lifetime = all of that + the founders' lounge + team and guests, 20 places. Open: which tier gets the founders' lounge and the two quiet founder rooms; can walk-ins come to any evenings; prices.
- [?] bake: the first-floor court tree's inner canopy is unlit (black) when the floor cut opens it; the bake could light or fill those faces (site leaves it as baked).
- [?] still image: `public/still/house-dawn.*` is the site's own hero, captured headless (software GL, soft). Re-capture on a real GPU (`?debug`, hide the corners) or have the bake render one; same frame serves the OG image.
- [?] bake: the two trees beside the gate are low-poly blobs; board 01 has two sparse gulmohars (thin trunks, open canopy, a few orange blossoms). That lives in the bake (`site-day.gltf`), so the bake loop needs to change it. Also the left tree sits further out than the right, so the margin fog swallows it at night.
