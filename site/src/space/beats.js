// The homepage as one scroll through a day, told in chapters by the hour
// (the earlier "house world" site), on the baked house. The camera flies:
// in from the street as the house opens, round to each floor from its own
// side, the event floor lit at night, and closed up on the street at the end
// (scene.js; the earlier world's camera, src/world/world.js). The floors come
// in the order the day uses them: the café, the work floor, the rooms, the
// terrace. A light cloud passes at the two big moves (in, and out to night).

// Scenes: exterior (the house on its street), floors (the open house; FOCUS 0
// basement … 3 second). A beat with `floor` is that floor's chapter.
export const BEATS = [
  { id: 'hero', from: 0, to: 0.1, scene: 'exterior' },
  { veil: true, from: 0.1, to: 0.13 },
  { id: 'ground', from: 0.13, to: 0.25, scene: 'floors', floor: 'ground' },
  { id: 'move', from: 0.25, to: 0.28, scene: 'floors' },
  { id: 'lower', from: 0.28, to: 0.4, scene: 'floors', floor: 'lower' },
  { id: 'move', from: 0.4, to: 0.43, scene: 'floors' },
  { id: 'first', from: 0.43, to: 0.55, scene: 'floors', floor: 'first' },
  { id: 'move', from: 0.55, to: 0.58, scene: 'floors' },
  { id: 'second', from: 0.58, to: 0.7, scene: 'floors', floor: 'second' },
  { veil: true, from: 0.7, to: 0.73 },
  { id: 'night', from: 0.73, to: 0.86, scene: 'exterior', night: true },
  { id: 'end', from: 0.86, to: 1.0001, scene: 'exterior', night: true },
]

// Which floor the open house is showing; at night, the event floor.
export const FOCUS = [[0.13, 1], [0.25, 1], [0.28, 0], [0.4, 0], [0.43, 2], [0.55, 2], [0.58, 3], [0.7, 3], [0.74, 2], [0.86, 2]]

// Hour of the day at each progress point; the rail on the right jumps by it.
export const HOURS = [
  [0, 6], [0.1, 7], [0.13, 8], [0.25, 10], [0.28, 12], [0.4, 13], [0.43, 15],
  [0.55, 16], [0.58, 19], [0.7, 19.6], [0.73, 21], [0.86, 22], [1, 23.3],
]
export const RAIL = [['06', 0, 'Dawn, the house'], ['09', 0.14, 'Morning'], ['13', 0.29, 'Midday'], ['16', 0.44, 'Afternoon'], ['19', 0.59, 'Evening'], ['21', 0.74, 'Night'], ['23', 0.87, 'Back to the house']]
export const partAt = (h) => (h < 7.5 ? 'Dawn' : h < 11.5 ? 'Morning' : h < 14 ? 'Midday' : h < 17.5 ? 'Afternoon' : h < 20 ? 'Evening' : 'Night')

// The sky by hour: the fog, the sky and the page take it. `glow` is the
// sunrise and sunset band in the sky. Pick one with ?sky=<name>; clear is the
// default. No pink: dawn is a cool pale grey, the evening goes gold, then
// indigo into a navy night.
export const SKIES = {
  // A clear day: cool dawn, warm white noon, a gold hour, an indigo night.
  clear: {
    glow: '#f1d9a6',
    fog: [[6, '#dfe3e3'], [8, '#ecebe5'], [12, '#f2f1ec'], [16, '#eee6d6'], [17.8, '#dcb878'], [19, '#33395a'], [20.5, '#161b2e'], [23.5, '#0f1322']],
  },
  // The monsoon: overcast greens and greys, a slate evening.
  monsoon: {
    glow: '#e4e2cf',
    fog: [[6, '#d5dbd7'], [8, '#e1e5e0'], [12, '#e7e9e3'], [16, '#dfe0d6'], [17.8, '#b9b8a0'], [19, '#3e4a50'], [20.5, '#1a2126'], [23.5, '#12171b']],
  },
  // The brand's sign paints (DESIGN.md): enamel by day, marigold at five,
  // indigo dusk, the night blue.
  marigold: {
    glow: '#f3cf86',
    fog: [[6, '#e9e4d6'], [8, '#f2ede1'], [12, '#f4eee1'], [16, '#f1e2c2'], [17.8, '#e3b45c'], [19, '#2c3770'], [20.5, '#151b42'], [23.5, '#0e1330']],
  },
}
const pick = typeof location !== 'undefined' && new URLSearchParams(location.search).get('sky')
export const SKY = SKIES[pick] || SKIES.clear
export const FOG = SKY.fog

// One caption per floor: what you do there and when, from the user's zone
// plan (site/POLISH.md, 5 Oct), the Explore copy, and the next step toward a
// membership (`next`: the link text and the way in it picks in the form).
export const FLOOR_COPY = {
  lower: {
    label: 'Lower level',
    title: 'Make things, round the big tree.',
    next: { text: "Use the maker's table: become a member →", tier: 'member' },
    line: "08:00–18:00 · Open work area · The maker's table and workshops · The founders' lounge",
    explore: {
      head: 'The working floor, below the street.',
      body: [
        'An open work area, lit by a court where a big tree rises through two floors. A seating platform runs round its trunk.',
        "Work here from 08:00 to 18:00. The maker's table is for building things by hand, and the daytime workshops run round it.",
        "Off the court, the old office is a private lounge for founders, open into the evening.",
      ],
    },
  },
  ground: {
    label: 'Ground floor',
    title: 'The café. Walk in from 08:00.',
    next: { text: 'Here most days? Become a member →', tier: 'member' },
    line: 'Walk-in café, 08:00–18:00 · Breakfast · The garden',
    explore: {
      head: 'The café.',
      body: [
        'Anyone can walk in, from 08:00 to 18:00: breakfast, coffee and a table to work at. Pay as you go.',
        'It opens onto the garden. At 18:00 the work stops and the evening begins.',
      ],
    },
  },
  first: {
    label: 'First floor',
    title: 'Where the evenings happen.',
    next: { text: 'Evenings come with membership →', tier: 'member' },
    line: '18:00–23:00 · The event room · Seats round the courtyard · Private rooms',
    explore: {
      head: 'Meetups, talks and film nights.',
      body: [
        'From 18:00 to 23:00 the event room holds meetups, learning events and film nights: a low stage, a screen and tiered teak seats.',
        'Informal seating runs round the courtyard. Private rooms off it take a meeting or a small group.',
      ],
    },
  },
  second: {
    label: 'Second floor',
    title: 'Two quiet rooms, and the roof.',
    next: { text: 'Book a call →', tier: 'unsure' },
    line: 'Quiet founder rooms by day · The terrace: work by day, grills and parties after 18:00',
    explore: {
      head: 'Up to the terrace.',
      body: [
        'Two quiet rooms for founders who need a closed door to work, 08:00 to 18:00.',
        'The terrace takes a laptop by day; after 18:00, the grill and the rooftop parties.',
      ],
    },
  },
}

// Three ways in (the user's plan, 5 Oct). What each includes is a draft for
// the user to confirm, and there are no prices yet (site/POLISH.md, Needs your
// input). Shown as one comparison: a row per fact, a column per way in.
export const FEATURES = [
  { id: 'cafe', label: 'Café, work area' },
  { id: 'maker', label: "Maker's table" },
  { id: 'evenings', label: 'Evenings' },
  { id: 'rooms', label: 'Private rooms' },
  { id: 'lounge', label: "Founders' lounge" },
  { id: 'guests', label: 'Team, guests' },
]
export const TIERS = [
  { id: 'walkin', name: 'Walk-in', for: 'A day here', hours: '08:00–18:00', has: ['cafe'], needs: 'Nothing', price: 'Pay as you go' },
  { id: 'member', name: 'Member', for: 'Here most days', hours: '08:00–23:00', has: ['cafe', 'maker', 'evenings', 'rooms'], needs: 'A call', price: 'To come' },
  { id: 'lifetime', name: 'Lifetime', for: 'Space for good', hours: '08:00–23:00', has: ['cafe', 'maker', 'evenings', 'rooms', 'lounge', 'guests'], needs: 'A call; 20 places', price: 'To come' },
]
