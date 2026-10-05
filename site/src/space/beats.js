// The homepage as one scroll through a day. Progress 0 → 1.
// The house stays on its street the whole way: it opens, and the camera
// visits each floor whole, with every room on it, the floors above lifted
// clear. Fog veils hide the few cuts (into the house, out to night, to the
// memberships).

// Scenes: exterior (the house on its street), floors (the open house; FOCUS 0 basement … 3 second), members,
// call. A beat with `floor` shows that floor's caption.
export const BEATS = [
  { id: 'hero', from: 0, to: 0.14, scene: 'exterior' },
  { id: 'opening', from: 0.14, to: 0.19, scene: 'exterior', open: true },
  { veil: true, from: 0.19, to: 0.22 },
  { id: 'lower', from: 0.22, to: 0.3, scene: 'floors', floor: 'lower' },
  { id: 'move', from: 0.3, to: 0.33, scene: 'floors' },
  { id: 'ground', from: 0.33, to: 0.42, scene: 'floors', floor: 'ground' },
  { id: 'move', from: 0.42, to: 0.45, scene: 'floors' },
  { id: 'first', from: 0.45, to: 0.55, scene: 'floors', floor: 'first' },
  { id: 'move', from: 0.55, to: 0.58, scene: 'floors' },
  { id: 'second', from: 0.58, to: 0.66, scene: 'floors', floor: 'second' },
  { veil: true, from: 0.66, to: 0.69 },
  { id: 'night', from: 0.69, to: 0.79, scene: 'exterior', night: true },
  { veil: true, from: 0.79, to: 0.82 },
  { id: 'members', from: 0.82, to: 0.92, scene: 'members' },
  { veil: true, from: 0.92, to: 0.95 },
  { id: 'call', from: 0.95, to: 1.0001, scene: 'call' },
]

// Which floor the open house is showing, through the floors beats.
export const FOCUS = [[0.22, 0], [0.3, 0], [0.33, 1], [0.42, 1], [0.45, 2], [0.55, 2], [0.58, 3], [0.66, 3]]

// Hour of the illustrative day at each progress point.
export const HOURS = [
  [0, 6], [0.14, 6.5], [0.19, 7.5], [0.22, 9], [0.3, 9.5], [0.33, 10.5], [0.42, 12], [0.45, 15],
  [0.55, 16], [0.58, 18.4], [0.66, 19], [0.69, 21], [0.75, 22], [1, 22],
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
