// The homepage as one scroll through a day (reference/astra-design/README.md,
// used as a reference for pacing only). Progress 0 → 1. Scenes change only
// inside a veil of fog, so no cut is ever seen.

// Scene ids: prologue (objects falling at dawn), exterior (the house on its
// street), room (one floor as an open-topped diorama), members, call.
export const BEATS = [
  { id: 'falling', from: 0, to: 0.05, scene: 'prologue', line: 'Make room for what comes next.' },
  { id: 'dawn', from: 0.05, to: 0.11, scene: 'exterior' },
  { id: 'opening', from: 0.11, to: 0.17, scene: 'exterior', open: true },
  { veil: true, from: 0.17, to: 0.2 },
  { id: 'lower', from: 0.2, to: 0.29, scene: 'room', room: 'lower' },
  { veil: true, from: 0.29, to: 0.31 },
  { id: 'cafe', from: 0.31, to: 0.4, scene: 'room', room: 'cafe' },
  { veil: true, from: 0.4, to: 0.42 },
  { id: 'court', from: 0.42, to: 0.53, scene: 'room', room: 'court' },
  { veil: true, from: 0.53, to: 0.56 },
  { id: 'terrace', from: 0.56, to: 0.65, scene: 'room', room: 'terrace' },
  { veil: true, from: 0.65, to: 0.68 },
  { id: 'night', from: 0.68, to: 0.78, scene: 'exterior', night: true },
  { veil: true, from: 0.78, to: 0.81 },
  { id: 'members', from: 0.81, to: 0.92, scene: 'members' },
  { veil: true, from: 0.92, to: 0.95 },
  { id: 'call', from: 0.95, to: 1.0001, scene: 'call' },
]

// Hour of the illustrative day at each progress point.
export const HOURS = [
  [0, 6], [0.11, 6.5], [0.17, 7.5], [0.2, 9], [0.29, 9.5], [0.31, 10], [0.4, 13],
  [0.42, 16], [0.53, 17.5], [0.56, 18.5], [0.65, 19], [0.68, 20], [0.75, 22], [1, 22],
]

// Fog by hour (board 08 / the Astra system board).
export const FOG = [
  [6, '#d1bfc2'], [10, '#bdb0b2'], [16, '#cec0c0'], [18.5, '#786c7d'], [20, '#33354a'], [22, '#1c2d4c'],
]

// Each diorama: the floor, the plan rectangle it is cut to (floor-local
// units; side and back edges on wall centrelines so those walls show as cut
// sections, the edge facing the camera just inside its wall so that wall is
// gone), the camera's azimuth / elevation in degrees, and the copy.
export const ROOMS = {
  lower: {
    floor: 'basement', rect: [-0.62, -0.52, 2.05, 1.93], az: 18, el: 46,
    label: 'Lower level', title: 'Work, with room to think.', line: 'Quiet rooms. Courts open to the sky.',
    explore: {
      head: 'Work, with room to think.',
      body: [
        'A quieter part of the house for focused work and small conversations. Work rooms sit beside courts that bring light below street level.',
        'Find the kind of space that suits your day. Membership shapes your access.',
      ],
    },
  },
  cafe: {
    floor: 'ground', rect: [0.56, 1.3, 2.46, 3.16], az: 14, el: 40,
    label: 'Ground floor', title: 'Coffee. A table. An unhurried start.', line: 'Walk-in café · 08:00–18:00',
    explore: {
      head: 'An unhurried start.',
      body: [
        'Coffee, a table and the possibility of a good conversation. By day, Space runs as a walk-in café, from 08:00 to 18:00.',
        'Stay close to the garden, meet someone new or take a little time for yourself. Talk to us about table booking and membership.',
      ],
    },
  },
  court: {
    floor: 'first', rect: [0.76, 0.12, 2.56, 1.74], az: -14, el: 46,
    label: 'First floor', title: 'Read. Talk. Let an idea take its time.', line: 'Courtyard · Library · Shared tables',
    explore: {
      head: 'A little distance from the day.',
      body: [
        'Read in the library. Find a quiet corner. Let a conversation unfold beside the courtyard.',
        'Space is a private club for startup people in HSR Layout, Bengaluru. A house for work, shared interests and time together.',
        'Membership shapes your access.',
      ],
    },
  },
  terrace: {
    floor: 'second', rect: [-2.36, -3.5, -0.78, 3.42], az: -58, el: 40,
    label: 'Second floor', title: 'The day opens into evening.', line: 'Terrace conversations. Room to linger.',
    explore: {
      head: 'The day opens into evening.',
      body: [
        'Take the conversation upstairs. Terracotta underfoot, a long bench and the evening air make room for a different pace.',
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
