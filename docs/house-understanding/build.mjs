// Builds house-understanding.html (then printed to PDF with headless Chrome).
import { writeFileSync } from 'node:fs';

// n: photo number (attachment order), x/y: pin position as a fraction of the plan image.
const photos = {
  1: ['First', 'Double-height courtyard, looking up to the skylight', 'Skylight, woven nest pendants, olive tree, teak louvred doors', 'Sure'],
  2: ['Basement', 'Garage / parking', 'Car, block wall, ladder', 'Sure'],
  3: ['Outside', 'Side drive and the ramp down to the garage', 'Facade, charcoal steel railing along the ramp', 'Likely'],
  4: ['First', 'First-floor outside entrance, at the top of the outside stair', 'Grass pendant, washed-concrete floor, mesh railing', 'Sure'],
  5: ['Outside', 'Street gate, no. 1172', 'Grey slatted gate, fern planter', 'Sure'],
  6: ['Ground → First', 'Outside stair from the entrance court up to the first floor', 'Frangipani, steel railing', 'Likely'],
  7: ['Ground?', 'Bathroom attached to a bedroom', 'Glass shower, granite counter', 'Guess'],
  8: ['First', 'Stair up to the second floor, beside the courtyard', 'Steel stair with timber treads; courtyard flagstones at right', 'Sure'],
  9: ['Ground', 'Side garden passage', 'Potted plants, steps, trees', 'Likely'],
  10: ['Basement?', 'Office / Den (or a first-floor bedroom)', 'Pinboard, teak windows, door to a toilet', 'Guess'],
  11: ['First', 'Double-height courtyard at floor level', 'Sandstone flagstones, nest pendants, louvred doors', 'Sure'],
  12: ['First', 'Family 2 or Dining 2, beside the courtyard', 'Pinboard, AC, corner windows, counter', 'Guess'],
  13: ['Ground', 'Kitchen 1 (long galley)', 'Black floor, black granite, mauve laminate', 'Likely'],
  14: ['First', 'Courtyard opening into Living 2', 'Flagstones meeting terrazzo, teak blinds', 'Likely'],
  15: ['Ground', 'Caretaker room', 'Red-oxide floor', 'Likely'],
  16: ['First', 'Room with the sliding teak door (Family 2?)', 'Cove light, terrazzo', 'Sure'],
  17: ['Ground', 'Kitchen 1 back store / utility', 'Same mauve laminate as #13', 'Guess'],
  18: ['Ground', 'Office toilet or powder room', 'Slate floor, vessel basin', 'Guess'],
  19: ['Outside', 'Street front', 'Gulmohar trees, facade', 'Sure'],
  20: ['Ground', 'Inside stair down to the basement. Below: the big tree and the workroom / gallery', 'Blue glass lantern, wooden balustrade', 'Sure'],
  21: ['Ground', 'Front lawn outside Living 1', 'Raised lawn, gulmohar beyond', 'Likely'],
  22: ['First', 'First-floor entrance / Foyer 2, toilet ahead', 'Coat rack, books, pendant', 'Guess'],
  23: ['First', 'Bedroom 3', 'Wall sconces, curtained window', 'Guess'],
  24: ['Ground', 'Entrance court, first-floor balcony above', 'Green bench, plants, stone floor', 'Likely'],
  25: ['Ground', 'Living 1: the teak-floored room towards the open entrance', 'Teak floor, brass lanterns, glazed doors', 'Sure'],
  26: ['First', 'Kitchen 2', 'Light-wood cabinets, double sink', 'Likely'],
  27: ['Ground', 'Living 1 (teak floor), door out to the lawn', 'Teak floor, lantern', 'Sure'],
  28: ['Ground', 'Room with the teak display unit (Dining 1?)', 'Teak display unit, glazed doors, sconces', 'Sure'],
  29: ['Second', 'Bedroom 5 bath (the tub is on the plan)', 'Bathtub, white tiles, teal glass blocks', 'Sure'],
  30: ['Second', 'Passage overlooking the courtyard void', 'Nest pendants hanging in the void', 'Sure'],
  31: ['Basement?', 'Office / Den', 'Office chair, whiteboard, AC', 'Guess'],
  32: ['Second', 'Study nook at the stair landing', 'Built-in desk, black pinboard', 'Likely'],
  33: ['Second', 'Terrace', 'Terracotta tiles, bench, white parapet', 'Sure'],
  34: ['Second', 'Dressing room', 'Wardrobes, mirror', 'Sure'],
  35: ['First', 'Same stair as #8, up to the second floor', 'Steel stair, courtyard beyond', 'Sure'],
  36: ['Ground', 'Garden steps up to the front lawn', 'Frangipani, lawn, potted plants', 'Likely'],
};

const floors = [
  {
    key: 'basement', name: 'Basement', sub: 'Half below the street. Two separate entrances.',
    notes: [
      '<b>Garage:</b> reached down the ramp from the side drive. Room for about three cars.',
      '<b>Office side:</b> its own entrance through the small open-to-sky court and its outside stair (bottom right). The large Office has the curved wall, plus the Office/Den and the Store/UPS room.',
      '<b>Double-height space 1, Court 1:</b> the court with the big tree, rising through the ground floor ("Double height" on the ground plan). The wooden-balustrade stair connects it to the ground floor from inside (#20).',
      '<b>Workroom / gallery</b> beside the court (Office/Den on the PDF plan, "Studio/Gallery" in the CAD file).',
    ],
    zones: [{ x: .53, y: .22, w: .39, h: .21, label: 'Double height 1' }],
    pins: { 2: [.23, .30], 3: [.2, .84], 10: [.76, .11], 31: [.66, .11] },
    extra: [{ x: .80, y: .86, t: 'Office entrance' }, { x: .76, y: .2, t: 'Workroom / gallery' }, { x: .63, y: .31, t: 'Big tree' }],
  },
  {
    key: 'ground', name: 'Ground floor', sub: 'The main arrival floor: entrance court, gardens, the teak-floored living room.',
    notes: [
      '<b>Arrival:</b> gate (#5), the entrance court (#24), then Foyer 1. The outside stair (#6) rises from the entrance court to the first floor.',
      '<b>Living 1</b> has the teak floor, faces the open entrance and opens onto the front lawn under the gulmohar trees (#21, #25, #27).',
      'Family 1, Dining 1, Kitchen 1 (galley), Bedrooms 1 and 2, the puja room and the caretaker room.',
      'The "Double height" box is the top of basement Court 1. The wooden-balustrade stair under it goes down to the basement (#20).',
      'The room with the teak display unit (#28) is also on this floor.',
    ],
    zones: [{ x: .59, y: .435, w: .23, h: .145, label: 'Over Court 1' }],
    pins: { 24: [.18, .53], 6: [.12, .45], 9: [.10, .70], 13: [.12, .15], 17: [.31, .11], 15: [.83, .06], 7: [.76, .33], 18: [.81, .61], 25: [.70, .72], 27: [.78, .76], 20: [.77, .555], 28: [.47, .20], 21: [.59, .91], 36: [.81, .96], 5: [.06, .95] },
  },
  {
    key: 'first', name: 'First floor', sub: 'Reached from inside and by its own outside stair. Built around the double-height courtyard.',
    notes: [
      '<b>Two ways in:</b> from outside, up the stair from the entrance court (#6) to the first-floor porch (#4) and Foyer 2 (#22); or from inside the house.',
      '<b>Double-height space 2, the courtyard:</b> olive tree, sandstone flagstones, teak louvred doors, woven nest lights. It opens up past the second floor to the skylight (#1, #11, #14).',
      'Living 2, Dining 2, Family 2 (the sliding teak door, #16), Kitchen 2 with its utility room, the library, Bedroom 3, and a store and service room.',
      'The steel stair beside the courtyard goes up to the second floor (#8, #35).',
    ],
    zones: [{ x: .62, y: .51, w: .30, h: .19, label: 'Double height 2' }],
    pins: { 1: [.80, .60], 11: [.86, .64], 14: [.77, .71], 22: [.56, .62], 4: [.37, .56], 26: [.37, .24], 12: [.49, .42], 16: [.75, .24], 8: [.80, .45], 35: [.86, .45], 23: [.38, .88] },
  },
  {
    key: 'second', name: 'Second floor', sub: 'Bedrooms, the terrace and the view down into the courtyard.',
    notes: [
      'Bedroom 4, Bedroom 5 with the bathtub (#29), and the dressing room (#34).',
      'The passage looks down into the first-floor courtyard; the skylight is above it (#30). A study nook sits at the stair (#32).',
      'The large terracotta-tiled terrace runs along the whole west side (#33).',
    ],
    zones: [{ x: .54, y: .43, w: .37, h: .22, label: 'Void over courtyard' }],
    pins: { 29: [.44, .82], 34: [.82, .09], 30: [.48, .52], 32: [.65, .42], 33: [.20, .45] },
  },
];

const palette = [
  ['Lime plaster', '#ecebe4'], ['Terrazzo', '#d9d3c7'], ['Kota / sandstone', '#b9a68a'], ['Teak', '#7a3f1f'],
  ['Terracotta', '#b5562f'], ['Red oxide', '#7d2a22'], ['Charcoal steel', '#4a4d4f'], ['Black granite', '#1d1d1c'],
  ['Foliage', '#3f5a2c'], ['Gulmohar', '#e0531f'],
];

const conf = { Sure: 'sure', Likely: 'likely', Guess: 'guess' };
const card = n => {
  const [floor, room, what, c] = photos[n];
  return `<figure class="ph"><img src="img/p${String(n).padStart(2, '0')}.jpg"><figcaption><span class="num">${n}</span><div><b>${room}</b><small>${floor} · ${what}</small></div><span class="c ${conf[c]}">${c}</span></figcaption></figure>`;
};

const floorPages = floors.map(f => {
  const ids = Object.keys(f.pins).map(Number);
  const pins = ids.map(n => `<span class="pin" style="left:${f.pins[n][0] * 100}%;top:${f.pins[n][1] * 100}%">${n}</span>`).join('');
  const zones = f.zones.map(z => `<span class="zone" style="left:${z.x * 100}%;top:${z.y * 100}%;width:${z.w * 100}%;height:${z.h * 100}%"><em>${z.label}</em></span>`).join('');
  const extra = (f.extra || []).map(e => `<span class="tag" style="left:${e.x * 100}%;top:${e.y * 100}%">${e.t}</span>`).join('');
  return `
<section class="page floor">
  <header><h2>${f.name}</h2><p>${f.sub}</p></header>
  <div class="split">
    <div class="plan"><img src="plans/${f.key}.png">${zones}${pins}${extra}</div>
    <ul class="notes">${f.notes.map(n => `<li>${n}</li>`).join('')}</ul>
  </div>
</section>
<section class="page grid">
  <header><h2>${f.name}: photos</h2></header>
  <div class="photos${ids.length > 9 ? ' dense' : ''}">${ids.sort((a, b) => a - b).map(card).join('')}</div>
</section>`;
}).join('');

const outside = [5, 19, 3];

const html = `<!doctype html><html><head><meta charset="utf-8"><title>Networker Space: the house as understood</title>
<style>
@page { size: A4; margin: 0 }
* { box-sizing: border-box; margin: 0 }
body { font: 10.5pt/1.45 -apple-system, "Helvetica Neue", sans-serif; color: #1d1d1c; background: #ecebe4 }
.page { width: 210mm; height: 297mm; padding: 16mm 15mm; page-break-after: always; overflow: hidden; background: #f4f2ec }
h1 { font: 500 34pt/1.05 Georgia, serif; letter-spacing: -.01em }
h2 { font: 500 20pt/1.1 Georgia, serif; margin-bottom: 2mm }
header { border-bottom: 1px solid #b9a68a; padding-bottom: 4mm; margin-bottom: 6mm }
header p { color: #6b5a48 }
.cover { display: flex; flex-direction: column; justify-content: space-between; background: #1d1d1c; color: #ecebe4 }
.cover .hero { height: 150mm; background: url(img/p01.jpg) center/cover; border-radius: 2px }
.cover p { color: #c9bfae; max-width: 140mm }
.sw { display: grid; grid-template-columns: repeat(5, 1fr); gap: 3mm }
.sw div { font-size: 8pt; color: #c9bfae }
.sw i { display: block; height: 12mm; border-radius: 2px; margin-bottom: 1.5mm; border: 1px solid #ffffff22 }
.split { display: grid; grid-template-columns: 108mm 1fr; gap: 8mm; align-items: start }
.plan { position: relative; background: #fff; border: 1px solid #d9d3c7 }
.plan img { width: 100%; display: block }
.pin { position: absolute; transform: translate(-50%, -50%); width: 6.5mm; height: 6.5mm; border-radius: 50%; background: #b5562f; color: #fff; font: 700 7.5pt/6.5mm sans-serif; text-align: center; box-shadow: 0 0 0 1.2px #fff }
.zone { position: absolute; border: 1.6px dashed #3f5a2c; background: #3f5a2c1f }
.zone em { position: absolute; left: 1mm; bottom: 1mm; font: italic 600 7.5pt sans-serif; color: #3f5a2c; background: #fffc; padding: 0 1mm }
.tag { position: absolute; transform: translate(-50%, -50%); font: 700 7pt sans-serif; color: #fff; background: #4a4d4f; padding: .6mm 1.5mm; border-radius: 1mm; white-space: nowrap }
.notes { padding-left: 4mm; display: grid; gap: 4mm }
.photos { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4mm }
.dense { grid-template-columns: repeat(4, 1fr); gap: 3mm } .dense .ph img { height: 36mm } .dense figcaption { padding: 1.5mm } .dense figcaption b { font-size: 7.8pt } .dense figcaption small { font-size: 7pt }
.ph { position: relative; background: #fff; border: 1px solid #d9d3c7; break-inside: avoid }
.ph img { width: 100%; height: 52mm; object-fit: cover; display: block }
figcaption { display: flex; gap: 2mm; padding: 2mm; align-items: flex-start; font-size: 8pt; line-height: 1.3 }
figcaption b { display: block; font-size: 8.5pt }
figcaption small { color: #6b5a48; font-size: 7.5pt }
.num { flex: none; width: 5.5mm; height: 5.5mm; border-radius: 50%; background: #b5562f; color: #fff; font-weight: 700; text-align: center; line-height: 5.5mm; font-size: 7pt }
.c { position: absolute; top: 2mm; right: 2mm; font-size: 6.5pt; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; padding: .4mm 1.2mm; border-radius: 1mm }
.c.sure { background: #3f5a2c; color: #fff } .c.likely { background: #b9a68a; color: #1d1d1c } .c.guess { background: #fff1ea; color: #7d2a22; border: 1px solid #e0531f88 }
.section { display: grid; grid-template-columns: repeat(4, 1fr); gap: 5mm; margin-top: 6mm }
.section div { border-top: 3px solid #1d1d1c; padding-top: 2mm; font-size: 9pt }
.section b { display: block; font: 500 12pt Georgia, serif; margin-bottom: 1mm }
.vid img { width: 112mm; display: block; border: 1px solid #d9d3c7; margin: 2mm 0 5mm }
ol.q { padding-left: 5mm; display: grid; gap: 3mm; font-size: 11pt }
</style></head><body>

<section class="page cover">
  <div>
    <p style="letter-spacing:.12em;text-transform:uppercase;font-size:8pt;margin-bottom:5mm">Networker Space · HSR Layout, Bengaluru · Working document</p>
    <h1>The house, as understood</h1>
    <p style="margin-top:4mm">Four floors read from the plans and placed against the 36 photos and 3 videos. Each photo carries a confidence mark. Corrections go by photo number.</p>
  </div>
  <div class="hero"></div>
  <div>
    <p style="margin-bottom:3mm;font-size:8pt;letter-spacing:.12em;text-transform:uppercase">Materials of the house, the source of the brand palette</p>
    <div class="sw">${palette.map(([n, c]) => `<div><i style="background:${c}"></i>${n}</div>`).join('')}</div>
  </div>
</section>

<section class="page">
  <header><h2>The house in one page</h2><p>Four levels, two double-height spaces, two separate basement entrances, and a first floor reachable from inside or by its own outside stair.</p></header>
  <div class="section">
    <div><b>Basement</b>Garage down the ramp. Office suite with its own entrance through an open-to-sky court. Double-height Court 1 with the big tree and the workroom / gallery; an inside stair up to the ground floor.</div>
    <div><b>Ground</b>Entrance court and Foyer 1. Living 1 with the teak floor, facing the open entrance and the front lawn. Family, dining, galley kitchen, two bedrooms, puja, caretaker.</div>
    <div><b>First</b>Reached from inside or by its own outside stair and porch. Double-height courtyard with olive tree and flagstones, open to the skylight. Living, dining, family, kitchen, library, Bedroom 3.</div>
    <div><b>Second</b>Bedrooms 4 and 5, the dressing room and the bath with the tub. A passage over the courtyard void, a study nook, and the long terracotta terrace.</div>
  </div>
  <div style="margin-top:10mm;display:grid;grid-template-columns:1fr 1fr;gap:6mm">
    <div><h2 style="font-size:13pt">Double-height space 1</h2><p>Basement Court 1, 14'6" × 12', with the big tree and the workroom / gallery beside it. Rises through the ground floor; the wooden-balustrade stair joins the two floors from inside (#20).</p>${card(20)}</div>
    <div><h2 style="font-size:13pt">Double-height space 2</h2><p>The first-floor courtyard, 13'10" × 12'. Olive tree, flagstones, nest lights. Open past the second floor to the skylight (#1, #11, #14, #30).</p>${card(11)}</div>
  </div>
</section>

${floorPages}

<section class="page grid">
  <header><h2>Outside and the approach</h2><p>Tree-lined street, the gate at no. 1172, the side drive and ramp to the garage.</p></header>
  <div class="photos">${outside.map(card).join('')}</div>
  <div class="vid" style="margin-top:6mm">
    <h2 style="font-size:13pt">Video 15.54.10 (0:23): the street approach</h2>
    <img src="img/v-15.54.10.jpg">
  </div>
</section>

<section class="page">
  <header><h2>Videos</h2><p>Frames sampled evenly through each clip.</p></header>
  <div class="vid"><b>15.53.16 (4:51): interior walk.</b> From an upper floor, down the teak stair, through the halls, down the narrow stair, out to the garden steps.<img src="img/v-15.53.16.jpg"></div>
  <div class="vid"><b>18.52.51 (1:07): first floor.</b> The double-height courtyard and the rooms around it.<img src="img/v-18.52.51.jpg"></div>
</section>

<section class="page">
  <header><h2>Settled, and what is left</h2><p>The floors, entrances and both double-height spaces are confirmed. Nothing here blocks the homepage.</p></header>
  <ol class="q">
    <li>Rooms still marked <i>Guess</i> (#7, #10, #12, #17, #18, #22, #23, #31) are left as they are; the walls are what matter for the model.</li>
    <li>Which inside stair joins the ground and first floors is still to be confirmed on the plan.</li>
  </ol>
</section>
</body></html>`;

writeFileSync(new URL('./house-understanding.html', import.meta.url), html);
console.log('ok');
