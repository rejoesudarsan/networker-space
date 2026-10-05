# Space — complete website design comps

**42 image-generated comps:** 24 consecutive homepage frames at 1920×1080, four mobile views at 390×844, five interaction views, five utility/recovery states, one walkthrough view and three system boards. Generated and reviewed on 5 October 2026 with the built-in image model; exported to exact dimensions. This is a design delivery, not website implementation.

Open [the contact sheet](boards.html) to review everything in order. [CONTENT.md](CONTENT.md) contains the complete copy master, including all four floor overlays, memberships and recovery messages. [PROMPTS.json](PROMPTS.json) contains every generation/edit attempt. [MANIFEST.json](MANIFEST.json) is the file inventory.

The direction is the approved house and materials, with Igloo’s quiet corner HUD and fog-concealed scene changes. The user’s additions are incorporated: real content throughout, plus chairs, books and petals falling from the sky at the beginning. The objects settle into fog before the closed house appears, then return in the membership and final invitation scenes. The sequence is one journey through a day, ending at Book a call.

The supplied current brand facts and approved boards supersede the older painted-street direction in DESIGN.md and the old name in PRODUCT.md. Use **Space**, JetBrains Mono, Schibsted Grotesk and Newsreader; never import the old Bungee/pill/bright-sign system into this design.

## Tier naming proposal

**Visit / Regular / House** maps to the working Silver / Gold / Platinum. Visit describes mostly walk-in access with table booking; Regular describes quiet spaces and game rooms; House describes broader access with team and guests. These names are proposals. Each comp includes **Needs —**, with “Requirements to be confirmed on a call.” Eligibility, guest limits, booking terms and pricing are not invented. The full copy and boundaries are in CONTENT.md.

## Homepage sequence

Ranges are normalized scroll progress, inclusive at the start and exclusive at the end except 100%. They include hold time; the exact image is the representative pose within that range. A focus/selection frame shows an interaction state that can occur during its range, not a mandatory automatic selection.

**01 — [Objects arrive](home-01-falling.png) · 0–3% · 06:00 IST.** Two teak chairs, two books and a few gulmohar petals fall from above into a nearly empty dawn atmosphere. The house is fully hidden. Camera: Lock the exterior camera. Move the objects downward on scroll; introduce no orbit. Fog: Dense fog hides the destination and the entire building. Build mapping: `world.js, characters.js, environment.js, main.js`.

**02 — [Into the house](home-02-settling.png) · 3–5% · 06:00 IST.** The same objects descend and become faint. A small line reads “Make room for what comes next.” Camera: Hold the same camera; continue the same trajectories without spawning replacements. Fog: The objects disappear before they could intersect the closed roof; the landing and relocation into rooms happen unseen. Build mapping: `world.js, characters.js, environment.js, main.js`.

**03 — [Dawn / house at rest](home-03-dawn.png) · 5–10% · 06:00 IST.** The confirmed house appears intact, with the stepped roof, teak windows, grey gate and two sparse gulmohars. Four corners read SPACE / Book a call / Scroll / 06:00 IST. Camera: Hold the reference frontal street camera; use this as the exterior framing master. Fog: Fog reveals the facade while suppressing neighbours and the street edges. Build mapping: `world.js, details.js, windows.js, environment.js, main.js`.

**04 — [The first separation](home-04-opening.png) · 10–14% · 06:30 IST.** Floors begin parting vertically; fine survey lines in empty space describe the separation. No geometry rotates or breaks. Camera: Same azimuth, focal length and facade registration; move floor groups only. Fog: Low fog hides the basement and the ground contact. Build mapping: `world.js, details.js, windows.js, main.js`.

**05 — [A house for startup people](home-05-parted.png) · 14–18% · 07:00 IST.** The parting reaches its widest point. Copy: “A house for startup people. Four levels. Room to belong.” Seam glow is removed in this refinement. Camera: Keep the street camera fixed; the roof and floor groups lift along their original vertical axes. Fog: Rising fog begins masking the section edges and the lowest floor. Build mapping: `world.js, details.js, windows.js, environment.js, main.js`.

**06 — [An empty breath](home-06-fog-basement.png) · 18–21% · 08:00 IST.** Only a very faint upper silhouette and the corner HUD remain. This is a deliberate quiet interval. Camera: Reposition the one camera to the lower-level section only after opacity passes 0.98. Fog: The entire exterior-to-basement scene change is concealed. Build mapping: `world.js, environment.js, main.js`.

**07 — [Work / lower level](home-07-basement.png) · 21–27% · 09:00 IST.** A compact lower-level section reveals work space, the large-tree court, a separate open-to-sky access court and a distinct garage-ramp edge. “Work, with room to think.” leads to Explore. Camera: Hold a mild elevated view, matching the main house front orientation as far as plan visibility permits; no ongoing spin. Fog: Fog consumes external section edges and hides everything beyond the selected floor. Build mapping: `world.js, details.js, program.js, characters.js, environment.js, main.js`.

**08 — [Lower level leaves](home-08-basement-exit.png) · 27–29% · 09:30 IST.** The same section drifts up, with the table and floor disappearing first. Its caption and leader withdraw. Camera: Truck the camera gently down relative to the held section, with unchanged azimuth. Fog: Rising mist erases the lower geometry before the object leaves view. Build mapping: `world.js, environment.js, main.js`.

**09 — [Morning pause](home-09-fog-cafe.png) · 29–31% · 10:00 IST.** The viewport is empty warm-grey fog with four quiet corners. Camera: Complete the move to the ground-floor camera while fully masked. Fog: The basement is removed and the ground-floor section becomes ready entirely out of sight. Build mapping: `world.js, environment.js, main.js`.

**10 — [Coffee / ground floor](home-10-cafe.png) · 31–38% · 10:00 IST.** The teak-floored living room appears with the glazed doors, brass lanterns and two small tables. “Coffee. A table. An unhurried start.” accompanies the café hours, 08:00–18:00. Camera: Hold a shallow elevated frontal camera; keep the complete room inside the safe scene area. Fog: Fog obscures the cut edges and upper-floor absence. Build mapping: `world.js, windows.js, details.js, characters.js, program.js, environment.js, main.js`.

**11 — [The morning clears](home-11-cafe-exit.png) · 38–40% · 13:00 IST.** The café moves upward and its floor is veiled; all in-world copy has faded. Camera: Slow vertical travel only, retaining the café perspective. Fog: Mist erases the table legs and section perimeter first. Build mapping: `world.js, environment.js, main.js`.

**12 — [Afternoon pause](home-12-fog-courtyard.png) · 40–42% · 15:00 IST.** An empty afternoon atmosphere separates café and courtyard. Camera: Move the camera to the court overview only inside opaque fog. Fog: No room substitution or camera jump is visible. Build mapping: `world.js, environment.js, main.js`.

**13 — [Read / first floor](home-13-courtyard.png) · 42–49% · 16:00 IST.** The approved double-height court returns: olive tree, three nest pendants, sandstone and louvred teak. A library glimpse is a proposed adjacent use. The caption reads “Read. Talk. Let an idea take its time.” Camera: Hold the court overview established by approved board 04. Fog: Fog masks external walls and limits the view to one section. Build mapping: `world.js, details.js, characters.js, program.js, environment.js, main.js`.

**14 — [Who’s inside](home-14-whos-inside.png) · 49–55% · 17:00 IST.** A slightly wider court view makes space for Founders / Artists / Music / Play. Founders is selected; two people talk over a notebook. Labels and short callout lines live in empty fog. Camera: Ease back once, then hold the camera throughout all four selection states. Fog: A small local haze crossfade may hide activity replacement; never mask an unexpected architectural change. Build mapping: `program.js, characters.js, world.js, main.js`.

**15 — [Into sundown](home-15-fog-terrace.png) · 55–58% · 18:00 IST.** The screen becomes empty violet-grey fog. The rejected pass that invented a new terrace was replaced. Camera: Transition the single camera to the terrace view only while opaque. Fog: The court and activities disappear before the terrace is introduced. Build mapping: `environment.js, world.js, main.js`.

**16 — [Terrace / sundown](home-16-terrace.png) · 58–65% · 18:30 IST.** The full narrow terracotta terrace, white parapet openings, teak side room and timber bench appear. Three people talk under restrained warm lights. “The day opens into evening.” Camera: Hold a gentle downward view with the entire side room inside the image. Fog: Fog hides all neighbours, lower floors and the section base. Build mapping: `world.js, details.js, characters.js, program.js, environment.js, main.js`.

**17 — [Evening pause](home-17-fog-evening.png) · 65–68% · 19:30 IST.** Empty slate-blue atmosphere deepens toward night. Camera: Return to the exact exterior camera registration while masked. Fog: The floor sections can rejoin their parent house here. Build mapping: `world.js, environment.js, main.js`.

**18 — [Coming back together](home-18-reassembling.png) · 68–72% · 20:00 IST.** The familiar facade comes back almost closed, with narrow seams and the first warm windows. The initial roof separation resolves as scrolling continues. Camera: Use the exterior master camera; do not orbit. Register the building to frame 03 in the actual build. Fog: Fog at the base conceals the joins and returning ground contact. Build mapping: `world.js, details.js, windows.js, environment.js, main.js`.

**19 — [A club by night](home-19-night.png) · 72–78% · 22:00 IST.** The closed house glows softly. The copy explains evening hours, 18:00–23:00, and membership-dependent access. No programme frequency is invented. Camera: Hold the original street camera and closed facade dimensions. Fog: Dark fog hides the neighbourhood and keeps attention on windows. Build mapping: `world.js, windows.js, environment.js, program.js, main.js`.

**20 — [Night pause](home-20-fog-memberships.png) · 78–81% · 22:00 IST.** The house vanishes into empty deep-blue mist. Camera: Move to a shallow view of the membership objects after full masking. Fog: All house-to-membership object changes happen unseen. Build mapping: `world.js, environment.js, main.js`.

**21 — [Three ways to belong](home-21-memberships.png) · 81–88% · 22:00 IST.** Visit, Regular and House appear as three furniture compositions on small sandstone fragments. Each lists inclusions, “Needs —” and Book a call. Requirements remain visibly unconfirmed. Camera: Hold one shallow arc view; the objects share a scale and ground plane. Fog: Fog eats the fragments’ bases so they belong to the same world. Build mapping: `world.js, characters.js, environment.js, main.js; proposed membership data`.

**22 — [Regular / selected](home-22-membership-focus.png) · 88–92% · 22:00 IST.** The Regular object brightens subtly with an underline and orange focus dot. The other two remain readable. The helper line says “For a more regular rhythm.” Camera: No camera movement or geometry change on hover, focus or selection. Fog: Fog stays constant; it is not used to conceal the other tiers’ copy. Build mapping: `main.js, world.js; proposed membership data`.

**23 — [One last breath](home-23-fog-cta.png) · 92–95% · 22:00 IST.** The three objects withdraw. “Stay a while” replaces the scroll hint as the final empty interval arrives. Camera: Set the final invitation camera while masked. Fog: This hides the change from three tier objects to one chair. Build mapping: `world.js, environment.js, main.js`.

**24 — [There’s room for you](home-24-call.png) · 95–100% · 22:00 IST.** One empty teak chair and one petal form the final in-world invitation. “There’s room for you. Tell us what you’re building. Book a call →.” The top-right action remains. Camera: Settle and hold. Clamp progress at the end; do not loop visitors away from booking. Fog: Fog leaves the chair alone and suppresses the floor fragment’s edge. Build mapping: `world.js, characters.js, environment.js, main.js`.

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
| `state-04-load-failed.png` | Retry and Continue without motion remain usable when the main scene fails to load. |
| `state-05-without-motion.png` | First stop of the six-chapter still reader; direct Previous/Next controls replace scrolling animation. |
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

Reduced motion or no WebGL: show still scene art with selectable copy and Previous/Next chapter controls; omit falling motion, object drift, decoding and camera interpolation. Use six still chapters: house; lower level; café; first floor with interest picker; terrace with the night-rhythm copy; memberships with the final invitation. Keep the same narrative order, all tier content and booking access. The final Next becomes Book a call. Loading's Continue without motion enters this mode immediately. Asset failure after a reasonable wait offers Try again and Continue without motion using CONTENT.md's exact copy. If a secondary model fails, retain the opaque transition only briefly, then provide the still/text version; never strand visitors in fog. A failed booking navigation must preserve a usable Back to Space action. Unknown routes use the 404 design.

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

The generation review rejected or corrected: a changed-scale house silhouette in the falling prologue; artificial floor-seam glow; an unwanted basement car; a leader crossing the workroom; a transition that invented a terrace; three swapped corner labels on the type board; and a wrong gulmohar hex label on the palette board. A final continuity pass regenerated reassembly and night directly from the dawn master to reduce facade scale drift, and removed the opening frame’s glowing seams. Some runs failed with a 504 tunnel timeout and were retried using the built-in image tool. The prompts are retained, including attempted prompts, with status annotations in PROMPTS.json.

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
