---
name: Networker Space
description: A café by day and a club by night for startup people, in a four-floor house in HSR Layout, painted like a Bengaluru street of enamel shop boards.
colors:
  marigold: "#eba21c"
  sindoor: "#c2361e"
  peacock: "#0b5e57"
  indigo: "#24306e"
  night: "#0e1330"
  enamel: "#f4eee1"
  ink: "#16130f"
  rani-pink: "#d2487a"
typography:
  display:
    fontFamily: "Bungee, 'Anek Latin Variable', sans-serif"
    fontSize: "clamp(2.6rem, 1.2rem + 4.6vw, 5.2rem)"
    fontWeight: 400
    lineHeight: 0.88
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Bungee, 'Anek Latin Variable', sans-serif"
    fontSize: "clamp(2.6rem, 1.6rem + 4vw, 5.4rem)"
    fontWeight: 400
    lineHeight: 0.95
  title:
    fontFamily: "Bungee, 'Anek Latin Variable', sans-serif"
    fontSize: "clamp(1.8rem, 1.3rem + 1.8vw, 2.8rem)"
    fontWeight: 400
    lineHeight: 0.95
  body:
    fontFamily: "'Anek Latin Variable', system-ui, sans-serif"
    fontSize: "clamp(1rem, 0.95rem + 0.25vw, 1.15rem)"
    fontWeight: 400
    lineHeight: 1.5
  lead:
    fontFamily: "'Anek Latin Variable', system-ui, sans-serif"
    fontSize: "clamp(1.2rem, 1rem + 0.8vw, 1.65rem)"
    fontWeight: 600
    lineHeight: 1.2
    fontVariation: "'wdth' 90"
  label:
    fontFamily: "'Anek Latin Variable', system-ui, sans-serif"
    fontSize: "0.85rem"
    fontWeight: 700
    letterSpacing: "0.05em"
    fontVariation: "'wdth' 115"
  button:
    fontFamily: "Bungee, 'Anek Latin Variable', sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1
    letterSpacing: "0.02em"
  kannada:
    fontFamily: "'Anek Kannada Variable', 'Anek Latin Variable', sans-serif"
    fontSize: "clamp(1.15rem, 1rem + 0.6vw, 1.5rem)"
    fontWeight: 700
rounded:
  swatch: "3px"
  chip: "6px"
  plate: "8px"
  board: "10px"
  pill: "999px"
spacing:
  gutter: "clamp(1rem, 4vw, 3.5rem)"
  section: "clamp(4rem, 9vw, 8rem)"
  board-pad: "clamp(1.4rem, 2.6vw, 2.2rem)"
  stack: "1.2rem"
components:
  button-primary:
    backgroundColor: "{colors.sindoor}"
    textColor: "{colors.enamel}"
    typography: "{typography.button}"
    rounded: "{rounded.pill}"
    padding: "0.7em 1.3em 0.6em"
    height: "48px"
  button-ink:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.enamel}"
    rounded: "{rounded.pill}"
    padding: "0.7em 1.3em 0.6em"
    height: "48px"
  button-marigold:
    backgroundColor: "{colors.marigold}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0.7em 1.3em 0.6em"
    height: "48px"
  button-plain:
    backgroundColor: "{colors.enamel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.pill}"
    padding: "0.7em 1.3em 0.6em"
    height: "48px"
  button-big:
    height: "58px"
    padding: "0.7em 1.6em 0.6em"
  board:
    backgroundColor: "{colors.enamel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.board}"
    padding: "{spacing.board-pad}"
  board-marigold:
    backgroundColor: "{colors.marigold}"
    textColor: "{colors.ink}"
    rounded: "{rounded.board}"
  board-indigo:
    backgroundColor: "{colors.indigo}"
    textColor: "{colors.enamel}"
    rounded: "{rounded.board}"
  chip-walk-in:
    backgroundColor: "{colors.enamel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.chip}"
    padding: "0.35rem 0.6rem 0.25rem"
  chip-regular:
    backgroundColor: "{colors.marigold}"
    textColor: "{colors.ink}"
    rounded: "{rounded.chip}"
    padding: "0.35rem 0.6rem 0.25rem"
  chip-house:
    backgroundColor: "{colors.indigo}"
    textColor: "{colors.enamel}"
    rounded: "{rounded.chip}"
    padding: "0.35rem 0.6rem 0.25rem"
  nav-link:
    textColor: "{colors.enamel}"
    rounded: "{rounded.pill}"
    padding: "0.45rem 0.95rem"
  nav-link-hover:
    backgroundColor: "{colors.marigold}"
    textColor: "{colors.ink}"
  nav-link-current:
    backgroundColor: "{colors.enamel}"
    textColor: "{colors.ink}"
---

# Design System: Networker Space

## Overview

**Creative North Star: "The Painted Street"**

The house is a Bengaluru street of hand-painted enamel shop boards. Every surface is a board: a flat field of paint, a hard ink keyline, a thin pinstripe painted just inside the edge, Bungee lettering with a hard ink drop, and a Kannada sub-line the way real shop boards carry one. Grounds are whole fields of a single paint (marigold street, peacock memberships, sindoor call-to-action, night evenings), separated by 3px ink rules rather than by gaps or fades.

The 3D house follows the same paint. Its four floor plates are one connected strip joined by enamel stairs, each slab a flat colour per face direction with ink edges, never lit or shaded. The camera walks room by room; a rani-pink dashed route, room outline and flag marker say "you are here". At the end the plates lift into the stacked house. Density is generous and loud: big type, few words per board, every path ending at "Book a call".

Rejected by the world itself: dark-glass "immersive WebGL", gradients, glass, soft shading on the model, and the generic pricing grid.

**Key Characteristics:**
- Flat paint fields with 3px ink keylines and an inset painted pinstripe.
- Bungee display lettering with a hard 0.045em ink drop; Anek Latin for reading.
- Bilingual: Kannada sub-lines under names and floor labels, never uppercased.
- Day is marigold, night is indigo and night-blue; the hours strip pairs them.
- Rani pink is reserved for "you are here".
- An unshaded, ink-edged 3D model of the real house plans.

## Colors

Six flat sign paints plus ink and a single wayfinding pink; every fill is solid.

### Primary
- **Sindoor** (`sindoor`): the call to action. "Book a call" buttons, the nav mark plate, the hero name, the closing CTA band, step numerals, text selection, form accent colour. The first floor plate.

### Secondary
- **Marigold** (`marigold`): the day street. Page ground (sky), day half of every hours/rhythm pair, the Regular tier board, display heads on peacock/indigo/night grounds, nav hover. The second-floor plate.
- **Peacock** (`peacock`): the memberships ground and the Walk-In tier's name and pinstripe; check marks in the comparison table. The lower-level plate.

### Tertiary
- **Indigo** (`indigo`): night boards. The club half of the hours pair, the House tier board, the programme board, the House chip. Always carries enamel text and a marigold pinstripe.
- **Night** (`night`): the evenings page ground and its sky.
- **Rani Pink** (`rani-pink`): position only. The route ribbon, the visited-room outline and the flag marker in the 3D house.

### Neutral
- **Enamel** (`enamel`): board paint, light text on dark grounds, focus halo, the ground-floor plate and stairs.
- **Ink** (`ink`): keylines, button plinths, headline drops, nav and footer ground, rails and hangers, default text.

### Named Rules
**The Flat Paint Rule.** Every painted surface is one flat, opaque paint: no gradient fills, no glass, no backdrop blur. The 3D model takes one tone per face direction and is never lit. The only soft tones are the ambient lift under boards and the ink ground pool under the 3D plates.

**The Day and Night Rule.** Marigold means day (8:00 to 18:00), indigo and night mean club hours (18:00 to 23:00). Where the rhythm is featured (the hero hours strip, the day/night band), the two sit side by side as paired fields split by an ink rule.

**The You Are Here Rule.** Rani pink marks the visitor's position in the house and nothing else.

## Typography

**Display Font:** Bungee (with Anek Latin Variable)
**Body Font:** Anek Latin Variable, width axis in use (with system-ui)
**Kannada Font:** Anek Kannada Variable

**Character:** Bungee is the sign painter's block letter, used at weight 400 only; Anek's width axis gives the body a condensed lead (90%) and wide, tracked labels (112 to 120%), and its Kannada sibling matches stroke for stroke.

### Hierarchy
- **Display** (Bungee 400, clamp 2.6 to 5.2rem, 0.88): the hero board name and page h1s (to 6rem). Sindoor on enamel, marigold on peacock or night, with the hard ink drop.
- **Headline** (Bungee 400, clamp 2.6 to 5.4rem, 0.95): section heads on full-bleed grounds.
- **Title** (Bungee 400, 1.35 to 3.4rem): board names: tier names, room stops, programme slots, floor rows, time numerals.
- **Lead** (Anek 600, width 90%, clamp 1.2 to 1.65rem, 1.2, max 24ch): the line under a board name.
- **Body** (Anek 400, clamp 1 to 1.15rem, 1.5, 34 to 52ch): reading copy.
- **Label** (Anek 700, width 115%, 0.85rem, 0.05em, uppercase): data labels that name a place or state: floor level, room location, clock phase, address plate. They sit beside or below what they label.
- **Kannada** (Anek Kannada 700, 1.15 to 1.5rem): the sub-line under names; in labels it drops case and tracking.

### Named Rules
**The Sign Drop Rule.** Display and headline lettering on a coloured ground carries a hard ink drop (`text-shadow: 0.045em 0.045em 0 ink`), the painted shadow of shop lettering. Body type never does.

**The Bilingual Board Rule.** Names of the house, its floors and its sections carry a Kannada line set directly beneath in Anek Kannada, never uppercased or tracked.

## Layout

Full-bleed bands of single paint, each opened by a 3px ink rule, padded by the section rhythm (clamp 4 to 8rem vertical) and the gutter (clamp 1 to 3.5rem). Boards sit inside bands at constrained widths (hero 40rem, assemble 26rem, book 46rem) rather than in card grids. Inner pages clear the fixed header with 7.5 to 10rem top padding.

Paired halves (day/night rhythm, hours strip) split 1fr 1fr and stack below 900px. Floor rows stagger, odd rows indented 1.5rem, flattening below 900px. On the house page the scroll is a sticky stage: room card bottom-left, clock bottom-right, progress rule under the header; on phones the card spans the bottom and the clock moves top-right. Breakpoints: 1000px (tiers and steps to one column), 900px, 760px (nav collapses to a Menu pill). Without WebGL or with reduced motion the page goes static and each room card shows its plan image.

## Elevation & Depth

Depth is hybrid: flat paint, plus two painted-on shadow devices and one ambient lift. Boards and floor rows hover off their ground on a soft ink lift; buttons stand on a hard ink plinth that compresses when pressed; the 3D plates cast a soft ink pool on the ground below.

### Shadow Vocabulary
- **Lift** (`box-shadow: 0 18px 30px -16px rgb(22 19 15 / 0.55), 0 4px 8px -4px rgb(22 19 15 / 0.35)`): every board, floor row and the nav mark.
- **Pinstripe** (`box-shadow: inset 0 0 0 7px paint, inset 0 0 0 9px stripe`): the painted inner line on boards; nav mark uses 3px / 4.5px.
- **Plinth** (`box-shadow: 0 6px 0 -1px ink, 0 12px 18px -10px rgb(22 19 15 / 0.6)`): buttons at rest; 8px on hover with a 2px rise, 2px on press with a 4px drop.
- **Sign drop** (`text-shadow: 0.045em 0.045em 0 ink`): display lettering, see Typography.

### Named Rules
**The Keyline First Rule.** Edges are drawn, not shaded: a 3px ink border on boards, buttons, plates and band joins (2px on chips and swatches). Shadow adds weight under a keyline; it never replaces one.

## Shapes

Softly cornered sign plates: boards 10px, nav mark and hours strip 8px, chips 6px, legend swatches 3px. Buttons and the nav rail are full pills. Step numerals are ink-ringed sindoor discs. Rules inside boards are 2px solid currentColor under small heads, 2px dashed between list sections and programme slots, and a 3px double rule under board titles. Tier boards hang from a 10px ink rail on 4px ink hangers.

## Components

### Buttons
Chunky enamel pills that stand on an ink plinth.
- **Shape:** full pill (999px), 3px ink keyline, min 48px tall (58px big).
- **Primary:** sindoor with enamel Bungee lettering at 0.95rem, 0.02em tracking.
- **Variants:** ink (secondary action on light boards), marigold (on peacock and indigo), plain enamel (on sindoor and alongside primary).
- **Hover / Active:** rises 2px with a taller plinth; press sinks 4px onto a 2px plinth; 0.25s on the expo-out ease.
- **Focus:** 3px ink outline, 3px offset, 6px enamel halo.

### Chips
- **Style:** tier stamps in Bungee 0.78rem, 2px ink keyline, 6px corners, painted in the tier's own board colour (Walk-In enamel, Regular marigold, House indigo).
- **Use:** who a room or evening is open to, and table column heads.

### Boards
The signature container: flat paint, 3px ink keyline, 10px corners, inset pinstripe, ambient lift. Enamel boards take an ink or sindoor stripe, marigold takes sindoor, indigo takes marigold. Room stop cards take their floor's paint.

### Tier Boards
Three boards hang from one painted ink rail at three scales (columns 0.86fr / 1fr / 1.16fr): Walk-In drops 1.2rem and tilts -1.2deg, Regular hangs level, House drops 2.4rem and tilts 0.8deg with a larger name. Under each name the metal (Silver / Gold / Platinum) is flat label text at 80% opacity. "You get" and "It takes" lists use stroked SVG check and arrow icons. Below 1000px the rail and hangers drop away and boards stack untilted.

### Navigation
Fixed header: the sindoor nav mark (stacked Bungee wordmark, enamel pinstripe) left, a pill rail of ink at 88% holding Anek 600 links right, then the primary button. Hover paints a link marigold; the current page is enamel. Over content the header turns solid ink. Below 760px the rail becomes a Menu pill that opens a full-width stacked list.

### The Painted House (3D)
Real floor plans built as four flat-painted plates in a connected strip at stepping heights, joined by six-step enamel stairs, every solid edged in ink. Wall tops are painted in the floor's ink like poché. The visited room stays bright with a rani-pink outline while the rest of the plate dims toward its paint; the dashed rani-pink route draws itself as you scroll and a pink flag walks with it. The final scroll lifts the plates into the stacked house and orbits it.

## Do's and Don'ts

### Do:
- **Do** give every painted surface a 3px ink keyline and, on boards, the inset pinstripe.
- **Do** set board names in Bungee 400 with the hard ink drop on coloured grounds, and a Kannada line beneath.
- **Do** pair marigold with indigo whenever day and night hours appear together.
- **Do** paint the 3D model one flat tone per face with ink edges, using the floor paints from content.
- **Do** end each band and page at a sindoor "Book a call".

### Don't:
- **Don't** use gradient fills, glass, backdrop blur or lit, shaded materials on painted surfaces or the model.
- **Don't** use rani pink for anything other than the visitor's position in the house.
- **Don't** uppercase or track Kannada text.
- **Don't** set a small uppercase label above a heading; labels name places and sit beside or under their subject.
- **Don't** use a Bungee weight other than 400 or a display face for reading copy.
