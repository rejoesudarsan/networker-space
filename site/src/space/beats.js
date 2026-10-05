// The homepage as one scroll through a day. Progress 0 → 1.
// Two camera angles only: the street (board 01), and one cutaway angle for the
// open house, rising floor to floor. It opens on the house with the brief; the
// first scroll goes in. Night returns to the street, where the evening, the
// memberships and the call sit in the fog beside the lit house. Fog veils hide
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
  { id: 'members', from: 0.75, to: 0.89, scene: 'exterior', night: true },
  { id: 'call', from: 0.89, to: 1.0001, scene: 'exterior', night: true },
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

// One caption per floor: what it is and what is on it (the Blender fit-out
// in blender/details/), plus the Explore copy from CONTENT.md.
export const FLOOR_COPY = {
  lower: {
    label: 'Lower level',
    title: 'Work, with room to think.',
    line: 'Quiet work rooms · A games and meeting room · Courts open to the sky',
    explore: {
      head: 'Work, with room to think.',
      body: [
        'A quieter part of the house for focused work and small conversations. Work rooms sit beside courts that bring light below street level.',
        'Find the kind of space that suits your day. Membership shapes your access.',
      ],
    },
  },
  ground: {
    label: 'Ground floor',
    title: 'Coffee. A table. An unhurried start.',
    line: 'Walk-in café, 08:00–18:00 · Coffee bar · The garden',
    explore: {
      head: 'An unhurried start.',
      body: [
        'Coffee, a table and the possibility of a good conversation. By day, Space runs as a walk-in café, from 08:00 to 18:00.',
        'Stay close to the garden, meet someone new or take a little time for yourself. Talk to us about table booking and membership.',
      ],
    },
  },
  first: {
    label: 'First floor',
    title: 'Read. Talk. Bring the room together.',
    line: 'The courtyard · Library · Event room · Game room',
    explore: {
      head: 'A little distance from the day, and a room for the evening.',
      body: [
        'Read in the library. Find a quiet corner. Let a conversation unfold beside the courtyard.',
        'Off the courtyard, a room with a low stage, a screen and tiered teak seats for talks, demo nights and small gigs. Next door, carrom and board games.',
        'Membership shapes your access.',
      ],
    },
  },
  second: {
    label: 'Second floor',
    title: 'The day opens into evening.',
    line: 'The terrace · Quiet rooms · A phone booth',
    explore: {
      head: 'The day opens into evening.',
      body: [
        'Take the conversation upstairs. Terracotta underfoot, a long bench and the evening air make room for a different pace.',
        'Quiet rooms for focused work sit beside the terrace.',
        "The club's evening rhythm runs from 18:00 to 23:00. Access depends on membership; talk to us about what is right for you.",
      ],
    },
  },
}

export const TIERS = [
  { id: 'visit', name: 'Visit', has: ['Walk-in access', 'Table booking'], focus: 'For the odd morning and a table when you need one.' },
  { id: 'regular', name: 'Regular', has: ['Quiet spaces', 'Game rooms'], focus: 'For a more regular rhythm.' },
  { id: 'house', name: 'House', has: ['Broader access', 'Team + guests'], focus: 'For bringing your team and your guests.' },
]
