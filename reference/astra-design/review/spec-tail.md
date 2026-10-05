## Secondary views and states

| File | Designed behavior |
|---|---|
| `mobile-01-dawn.png` | Complete facade and trees fit the portrait viewport. Copy sits below the house. The falling prologue uses the same timing and a narrower central trajectory; reduced motion skips it. |
| `mobile-02-courtyard.png` | Whole court fits above a short caption and Explore action. No wall or pendant crop; safe areas take priority over image scale. |
| `mobile-03-memberships.png` | One tier at a time; all three names remain visible. Previous/next buttons and direct name selection work without requiring swipe. Regular is the representative selected state. Each selection replaces the object and its matching inclusion/requirement copy together. |
| `mobile-04-call.png` | One chair with the invitation beneath it; booking is available in the corner and beside the chair. |
| `interaction-01-explore-closed.png` | Explore hover/focus: underline, a small orange dot and a short leader redraw. The world does not orbit. |
| `interaction-02-explore-open.png` | World dims, copy appears in an unboxed reading column and the top-right corner becomes Close. The camera and progress remain frozen. Final decoded text is shown. |
| `interaction-03-artists.png` | Artists selected; two quiet sketching figures and the corresponding caption replace the Founders activity. |
| `interaction-04-music.png` | Music selected; two people, one acoustic guitar, no stage or crowd. |
| `interaction-05-play.png` | Play selected; a small board game and the corresponding caption. |
| `state-01-loading.png` | Sparse petal motion with Preparing the house and an immediate Continue without motion link; no fictional percentage. |
| `state-02-not-found.png` | One closed book in fog, a useful explanation and Back to Space; booking remains available. Return an actual 404 status at the hosting layer. |
| `state-03-booking-unavailable.png` | Honest missing-destination state. Close restores the precise prior scene. It neither submits anything nor claims a booking. |
| `walkthrough-01-courtyard.png` | Separate eye-level room tour using p11/p01 as grounding. Previous/next navigation, return-to-story and booking remain visible. This is one representative room, as requested. |

### Explore interaction contract

Activate with pointer, touch or Enter/Space on the real Explore button. Save `{progress, floor, interest, focusTarget}`; stop wheel-to-world updates, clear inertial velocity and freeze the camera. Dim the world over 240 ms. Run a restrained 450 ms decoding reveal using a clipped/masked version of the final text, not random unreadable characters; accessible text is final and present immediately. Reduced motion displays final text immediately. The comp depicts the stable decoded state. No sound turns on automatically.

Implement a semantic dialog with a visible heading, Close button, contained focus and background inertness. Escape and Close restore saved state and focus. Allow the reading column to scroll when enlarged text or a small screen needs it; never capture that scrolling for the world. On mobile the dimmed world becomes a faint background and the text column uses 20 px side margins with safe-area clearance. Book a call uses the shared booking behavior. Walk through the house enters `/house?room=court` and preserves a return token for the story.

### Interest selection

Map Founders → existing `founders`, Artists → `artists`, Music → `musicians`, Play → `players`. Do not silently remove existing content data; the proposed public picker presents four interests while the current internal data also has Everyone and Dancers. This set needs product acceptance. Use semantic radio controls with the selected label announced once. Choice changes update caption and at most two or three occupants together over 250 ms. No live occupancy claim, member identity, named guest or real event schedule is implied.

### Booking

All primary actions share one valid HTTPS booking destination when supplied. In the current source `BOOKING_URL` is empty and links retain `#book` without a matching target. Replace this dead-end behavior in the eventual implementation: if configured, navigate directly to the real booking provider, preserving a non-sensitive tier context only when supported; if unconfigured, open `state-03-booking-unavailable`. Do not invent slots, duration, phone numbers or a provider-branded calendar. The external provider owns scheduling, confirmation and cancellation. Browser Back restores story position; do not announce success merely on outbound click. Owner-approved destination is a release prerequisite.

### Walkthrough route

Proposed route `/house` with a verified room key in the query. There is no current separate walkthrough page in the active site; archived pages are evidence, not a ready implementation. Reuse the same measured house and materials, with a separate camera-path mode. A room list should be generated from approved room data and verified adjacency, not from low-confidence photo guesses. Suggested editorial stops are entrance court → living/café → garden → lower work rooms and courts → first court → library/shared rooms → terrace. Stair transitions must follow real access; camera movement cannot cross a slab or closed wall. If exact adjacency is not yet authored, use a short fog/crossfade between room views rather than implying a false walking route. Previous is unavailable at the first stop; at the last stop Next becomes Book a call. Back to the story restores the saved state, or goes to the dawn hero on direct entry.

## System specification

The three generated system boards are visual references. These numeric values and the content master are authoritative where image-generation typography or color varies. Image generation approximates font appearance; it does not install or typeset licensed font files. In the build load actual **JetBrains Mono**, **Schibsted Grotesk** and **Newsreader**. Do not bake raster text into the WebGL canvas.

| Role | Font | CSS size / line height | Treatment |
|---|---|---|---|
| HUD and actions | JetBrains Mono 400 | 14 / 20 px desktop; 12 / 18 px mobile | Tiny, crisp, normal tracking; right corners right-aligned. |
| Metadata | JetBrains Mono 400 | 12 / 18 px | Used sparingly; never the only way to understand an action. |
| Captions / tier copy | Schibsted Grotesk 400 | 16 / 24 px | Keep short; in-world labels may use mono for the Igloo callout character. |
| Explore reading copy | Schibsted Grotesk 400; mono reveal treatment optional | 16 / 24 px | Maximum 52 characters per line; preserve readability at zoom. |
| Rare editorial line | Newsreader 400 | 28 / 34 px desktop; 22 / 28 px mobile | Final invitation only. No giant hero headline. |

The generated desktop HUD is somewhat larger than the final CSS targets; it was requested at 18 px for legibility in image comps. Mobile generation occasionally renders 11–14 px-looking labels. Use the table's minimums in the build, and grow type if it is not readable. Keep the tiny visual footprint through spacing and brevity, not illegible text.

Desktop corner inset: 48 px at 1920 width, smoothly reducing to 32 px by 1024. Mobile: 20 px plus device safe-area inset. Interactive hit boxes are at least 44 × 44 CSS px, even if their text is tiny. Desktop center safe region: x=25–78%, y=14–82%, adjusted per diorama. Leave at least 32 px of screen-space clearance between callout text/leader endpoints and the rendered architecture silhouette. Text never sits on windows or plaster. Callout roots follow scene progress, but collision-resolve in screen space into empty fog; they are not permanently pinned architectural labels.

Rest links have no container. Hover underlines over 120 ms; focus-visible uses a 2 px contrasting outline with 4 px offset. An orange dot may reinforce selection but never acts as the only signal. Press changes opacity briefly without moving the camera. Scroll hint disappears while a dialog is open and becomes Stay a while at the final hold. Sound is off by default, starts only after explicit activation, and lives beneath Scroll in the bottom-left corner; the pure hero rest comp omits it for the approved four-label composition. The implementation can reveal it after the first input. Do not autoplay sound on Explore. Provide a mute button even if ambient audio later fails.

| Material | Hex target |
|---|---|
| Lime-white plaster | `#E8E4DA` |
| Teak | `#805238` |
| Sandstone | `#B3A68B` |
| Terrazzo | `#CBC4B5` |
| Terracotta | `#B66E51` |
| Red oxide | `#884B45` |
| Charcoal steel / light-world text | `#383B3A` |
| Foliage | `#59634D` |
| Gulmohar accent | `#C96A3D` (proposed addition) |

| Scene hour | Fog target |
|---|---|
| 06:00 | `#D1BFC2` |
| 10:00 | `#BDB0B2` |
| 16:00 | `#CEC0C0` |
| 18:30 | `#786C7D` |
| 22:00 | `#1C2D4C` |
| Warm transition veil | `#CFBDC0` |

These retain approved board 08's values. They are art-direction targets, not physical color measurements. Interpolate hour color separately from fog opacity. Amber window light is warm illumination of the material palette; orange is the only saturated UI accent. No neon, emissive seams, sci-fi effects, traffic or neighbouring masses. Charcoal text is used on day fog; lime-white on dark fog. Validate actual composited contrast across all keyframes; small normal text needs 4.5:1. If cloud detail compromises contrast, simplify that local atmosphere instead of placing an opaque card behind the caption.

## Motion, responsiveness and recovery

Use a single normalized progress value `p` from 0 to 1. Ranges above are percentages of that value, not elapsed seconds. Do not tie the clock to real time or let it advance while the visitor stops. Wheel, touch and keyboard update a target; a damped follower eases toward it. A useful tuning start is 0.12 s smoothing, but preserve a full opaque mask whenever a fast scroll skips through a change. Before replacing a scene, require transition opacity ≥0.98 for at least one presented frame; on slower hardware hold the mask until assets are ready. Reverse scrolling must return through the same mask, poses and camera positions.

For the opening, use two chairs and two books plus a small petal cluster; at most five grouped objects are active. Reuse these object designs later. The falling phase occupies 0–3%, settling 3–5%; no gravity physics simulation is required. Keyframe bounded downward paths and slight rotation, with most objects disappearing in fog before reaching roof level. Do not rain objects over the rest of the website. A visitor who stops at 0% sees the first falling pose with no auto-loop; optional ambient petals must remain extremely subtle. The whole first beat can be skipped with keyboard navigation or reduced motion.

Use one perspective camera object, with explicit scene anchors. Exterior camera is fixed across dawn/open/reassembly/night. The comp images show small generative drift in facade scale and roof registration; **do not turn that drift into animation**. In the build register all exterior frames to home-03-dawn and the approved facade. Floor camera translations and elevations happen inside fog; their visible holds remain still. Disable the current pointer camera offset for these scenes or constrain it to a nearly imperceptible range that never changes framing. Use the measured GLB/house.json for all rooms, not image-to-mesh reconstruction from these comps.

For widths below 760 px, change to portrait camera framing and put captions below the world. Never crop the facade to fill width. Memberships become the one-at-a-time treatment in mobile-03. At 200% zoom, permit ordinary text scrolling and collapse nonessential atmosphere rather than clipping copy. Avoid pinning a large overlay over the house. Long explorer copy is the intentional dimmed reading state.

Reduced motion or no WebGL: show still scene art with selectable copy and Previous/Next chapter controls; omit falling motion, object drift, decoding and camera interpolation. Keep the same chapter order, all tier content and booking access. Loading's Continue without motion enters this mode immediately. Asset failure after a reasonable wait offers Try again and Continue without motion using CONTENT.md's exact copy. If a secondary model fails, retain the opaque transition only briefly, then provide the still/text version; never strand visitors in fog. A failed booking navigation must preserve a usable Back to Space action. Unknown routes use the 404 design.

## Build handoff: current modules and proposed work

This is a source audit, not a patch or a claim that the design already exists. Each frame above lists the current modules it maps to. Read these paths as future responsibilities; nothing under `site/` was changed in this task.

| Existing module | Current responsibility | Handoff change |
|---|---|---|
| `site/src/world/main.js` | Virtual scroll, touch/keyboard input, clock, people controls and `BOOKING_URL`. | Drive the 24-frame progress map; semantic HUD, in-world buttons, dialog state and restored focus; safe booking fallback; route handoff and still mode. |
| `site/src/world/world.js` | House/floor groups, lighting, perspective camera, `SHOTS`, floor opening/cutaway and transition orchestration. | Replace shot order with basement → ground → first → terrace; add falling prologue, stable exterior registration, membership objects and final chair; enforce fog gates and clamp final progress. |
| `site/src/world/environment.js` | Scene atmosphere presets and shader environments including café, studio, courtyard, terrace and night. | Use the five hour chips; separate color interpolation from opaque transition masks; quiet cloud detail and maintain legible caption zones. |
| `site/src/world/program.js` | `ROOMS`, `PEOPLE`, `PARTS`, `PROGRAM`, room usage by time and interest. | Keep measured room positions; author restrained proposed uses and public four-interest aliases; replace event-like claims with approved copy. Membership data is new and should remain separate from room activity data. |
| `site/src/world/characters.js` | Articulated figures, poses and gathering furniture. | Limit settled scenes to 0–3 people; reuse chairs/books, add subtle sketch/guitar/game activities; prevent a crowd from existing programme counts. |
| `site/src/world/details.js` | Architectural details, basement access, planting and neighbourhood dressing attached to floors. | Preserve distinct ramp/office access and two double-height courts; keep details floor-local while lifting; suppress off-property/traffic dressing. |
| `site/src/world/windows.js` | CAD-derived frames/glazing that follow cutaway walls. | Retain real sill/window arrangement during sectioning and closure; add restrained night glow without changing openings. |
| `site/src/world/traffic.js` | Moving autos and scooters. | Disable for this art direction; the sparse world does not need street traffic. |
| `site/src/world/world.css`, `site/index.html` | Current presentation and chapter markup. | Future semantic text and actual fonts, corner grid, focus states, dialogs, responsive/static content. These files were read only, not edited. |

`world.js` currently focuses second/overview → first → basement → second → terrace/second → first → overview, so the requested floor sequence is a real handoff change, not merely new copy. Existing fog stops near .145/.30/.46/.62/.77/.91 need retiming to the ranges above. The current picker has Everyone, Founders, Artists, Musicians, Dancers and Players; the proposed four-label interface is a deliberate change. The current `BOOKING_URL = ''` and missing `#book` target are an existing dead end. A separate active walkthrough route, membership data/objects, explore dialog, loading recovery and 404 route are proposed additions; do not describe them as implemented.

For implementation boundaries, keep an immutable scene manifest (ranges, camera anchors, atmosphere, content key, room/interest key), a membership content source (three tiers with nullable requirements), and explicit route/dialog state. Small new `story.js`, `memberships.js` and walkthrough route modules may be appropriate when implementing; these are proposed names, not files claimed to exist. Reuse the rendering and room model rather than forking a second house for the walkthrough.

## Grounding, critique and remaining uncertainty

The approved front elevation is the exterior identity reference. p19/p05 support its facade and gate; p25/p27 support the café room; p11/p01 support the first-floor court; p33 supports the terrace; p20 and the photo labels distinguish basement access and the large-tree court. p31's floor attribution is low confidence, so it supports finish/furniture character only. The basement comp is the least geometrically certain: it demonstrates distinct access and atmosphere but is **not** a reconstruction of measured room positions. Keep `house.json`'s basement offset `[0.416, 1.387]` and the authoritative plan openings in the build. First-floor court and basement Court 1 must never be merged.

The generation review rejected or corrected: a changed-scale house silhouette in the falling prologue; artificial floor-seam glow; an unwanted basement car; a leader crossing the workroom; a transition that invented a terrace; and three swapped corner labels on the type board. A final continuity pass regenerated reassembly and night directly from the dawn master to reduce facade scale drift, and removed the opening frame’s glowing seams. Some runs failed with a 504 tunnel timeout and were retried using the built-in image tool. The prompts are retained, including attempted prompts, with status annotations in PROMPTS.json.

The final images retain small generative differences in facade size, fine window divisions, furnishings, people count and cutaway edges. They are finished visual comps, not pixel-registered animation frames or construction drawings. The handoff explicitly locks those details to the approved house/model. Typography is legible and reviewed visually but font identity is approximate; the exact font files and spacing must be applied by the engineer. The in-image hex labels are reviewed, but rendered chip pixels are illustrative. No raster text compositing was used to disguise model errors.

## Decisions for the owner

1. Accept or revise **Visit / Regular / House**. Silver / Gold / Platinum remain the source labels until accepted.
2. Define requirements for each tier, booking rules, team/guest limits and evening entitlements. The visible dashes are intentional until then.
3. Choose the final invitation: **Tell us what you’re building.** (shown) or the broader **Tell us what brings you here.**
4. Supply the booking destination and confirm proposed café/library/game uses before production copy is published. Programme frequency remains unconfirmed.
5. Confirm the falling objects (chairs, books, petals) as the opening motif. They appear only at the start and return as membership/CTA objects.

## Validation and scope

The delivery is design imagery, content and a build specification, not a coded website. All PNG exports are validated for format, dimensions and count; every frame has been visually inspected during generation and in the final review sheet. The contact sheet references local relative files and includes captions in narrative order. The image tool returned native sizes close to the requested aspect ratios; export normalization uses only `sips` resizing to exact 1920×1080 or 390×844, without content or text edits. PROMPTS.json preserves every generation and edit prompt used.

Concurrent source change: the initial details.js/world.js hashes match `2eedc67`; during design work a separate commit `8dba5c7` added Blender roof/site loading and related cutaway handling. The resulting hashes match that commit. This task made no site edits or commits. The current working tree has only this design directory untracked. The initial-to-final source hashes therefore differ for those two modules, and validation records the difference explicitly rather than claiming an unchanged shared checkout. When implementing, preserve the newer Blender roof/site path and apply this design’s visibility and fog rules to those imported objects.

Final scope evidence is in `review/validation.json`, `review/final-status.txt` and `review/site-after.sha1`. The source audit does not constitute a browser test, a build, deployment or production proof. No commit was made.
