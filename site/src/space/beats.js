// The homepage as one scroll through a day. Progress 0 → 1.
// Two camera angles only: the street (board 01), and one cutaway angle for the
// open house, rising floor to floor. It opens on the house with the brief; the
// first scroll goes in. Night returns to the street, where the evening, the
// memberships, how joining works and the call sit in the fog beside the lit house. Fog veils hide
// the two cuts (into the house, out to night).

// Scenes: exterior (the house on its street), floors (the open house; FOCUS 0
// basement … 3 second). A beat with `floor` shows that floor's caption.
export const BEATS = [
  { id: 'hero', from: 0, to: 0.08, scene: 'exterior' },
  { veil: true, from: 0.08, to: 0.11 },
  { id: 'lower', from: 0.11, to: 0.21, scene: 'floors', floor: 'lower' },
  { id: 'move', from: 0.21, to: 0.24, scene: 'floors' },
  { id: 'ground', from: 0.24, to: 0.35, scene: 'floors', floor: 'ground' },
  { id: 'move', from: 0.35, to: 0.38, scene: 'floors' },
  { id: 'first', from: 0.38, to: 0.49, scene: 'floors', floor: 'first' },
  { id: 'move', from: 0.49, to: 0.52, scene: 'floors' },
  { id: 'second', from: 0.52, to: 0.62, scene: 'floors', floor: 'second' },
  { veil: true, from: 0.62, to: 0.65 },
  { id: 'night', from: 0.65, to: 0.75, scene: 'exterior', night: true },
  { id: 'members', from: 0.75, to: 0.86, scene: 'exterior', night: true },
  { id: 'join', from: 0.86, to: 0.93, scene: 'exterior', night: true },
  { id: 'call', from: 0.93, to: 1.0001, scene: 'exterior', night: true },
]

// Which floor the open house is showing, through the floors beats.
export const FOCUS = [[0.11, 0], [0.21, 0], [0.24, 1], [0.35, 1], [0.38, 2], [0.49, 2], [0.52, 3], [0.62, 3]]

// Hour of the illustrative day at each progress point.
export const HOURS = [
  [0, 6], [0.08, 7], [0.11, 9], [0.21, 9.5], [0.24, 10.5], [0.35, 12], [0.38, 15],
  [0.49, 16], [0.52, 18.4], [0.62, 19], [0.65, 21], [0.75, 22], [1, 22],
]

// Fog by hour (board 08). The evening tone is kept dark enough that light
// text reads on it; mid-greys would fail both dark and light text.
export const FOG = [
  [6, '#d1bfc2'], [10, '#c9bcbd'], [16, '#d2c5c3'], [17.6, '#8f7f88'], [18.4, '#564b5e'], [20, '#2c3048'], [22, '#1c2d4c'],
]

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
