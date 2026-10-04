// What the house becomes, by the hour and by who is in it.
// Rooms sit at real positions on the drawn floors (floor-local units, 1 = 8 ft).

export const ROOMS = {
  cafe: { floor: 'ground', x: 1.15, z: 2.2, name: 'Living room' },
  family: { floor: 'ground', x: -0.9, z: -1.6, name: 'Family room' },
  dining: { floor: 'ground', x: -0.45, z: -3.0, name: 'Dining room' },
  garden: { floor: 'ground', x: 0.5, z: 4.1, name: 'Front lawn' },
  entrance: { floor: 'ground', x: -2.0, z: 0.7, name: 'Entrance court' },
  gallery: { floor: 'basement', x: 0.97, z: -2.75, name: 'Gallery' },
  office: { floor: 'basement', x: 0.55, z: 0.8, name: 'Office' },
  court: { floor: 'first', x: 1.6, z: 1.15, name: 'Courtyard' },
  library: { floor: 'first', x: 0.2, z: -1.45, name: 'Library' },
  long: { floor: 'first', x: -0.25, z: -0.6, name: 'Long room' },
  hall: { floor: 'first', x: 1.5, z: 3.1, name: 'Hall' },
  terrace: { floor: 'second', x: -1.55, z: -0.6, name: 'Terrace' },
  upper: { floor: 'second', x: 0.8, z: 2.0, name: 'Upper room' },
}

export const PEOPLE = [
  { id: 'all', name: 'Everyone' },
  { id: 'founders', name: 'Founders' },
  { id: 'artists', name: 'Artists' },
  { id: 'musicians', name: 'Musicians' },
  { id: 'dancers', name: 'Dancers' },
  { id: 'players', name: 'Players' },
]

export const PARTS = [
  { id: 'dawn', until: 8.5 },
  { id: 'day', until: 12 },
  { id: 'afternoon', until: 17 },
  { id: 'evening', until: 20 },
  { id: 'night', until: 99 },
]
export const partAt = (h) => PARTS.find((p) => h < p.until).id

// [room, what it becomes, how people gather, how many]
// Gatherings: table, desk, talk, circle, dance, row, stage.
export const PROGRAM = {
  all: {
    dawn: [['terrace', 'Yoga', 'row', 5], ['cafe', 'Café opening', 'talk', 2]],
    day: [['cafe', 'Café', 'table', 4], ['family', 'Café', 'table', 4], ['court', 'Laptops under the olive', 'table', 4], ['office', 'Office', 'desk', 5], ['library', 'Quiet reading', 'desk', 3]],
    afternoon: [['gallery', 'Studio', 'desk', 4], ['long', 'Pitch practice', 'stage', 7], ['office', 'Office', 'desk', 5], ['court', 'Coffee meetings', 'talk', 3], ['upper', 'Workshop', 'table', 4], ['cafe', 'Café', 'table', 3]],
    evening: [['terrace', 'Sundowner', 'talk', 6], ['garden', 'Garden drinks', 'talk', 4], ['court', 'Open mic', 'stage', 8], ['gallery', 'Show opening', 'talk', 5], ['entrance', 'Arrivals', 'talk', 4]],
    night: [['dining', 'Long dinner', 'table', 8], ['hall', 'Dance floor', 'dance', 9], ['court', 'Jam', 'circle', 7], ['terrace', 'Late talk', 'talk', 5], ['family', 'Board games', 'table', 4]],
  },
  founders: {
    dawn: [['terrace', 'Run club stretch', 'row', 5]],
    day: [['cafe', 'Founder breakfasts', 'table', 4], ['office', 'Heads-down', 'desk', 5], ['court', 'Co-working', 'table', 4], ['library', 'Deep work', 'desk', 3], ['gallery', 'Team room', 'desk', 4]],
    afternoon: [['court', 'Pitch circle', 'circle', 7], ['long', 'Demo practice', 'stage', 7], ['office', 'Office', 'desk', 5], ['upper', 'Hiring chats', 'table', 4], ['gallery', 'Team room', 'desk', 4]],
    evening: [['terrace', 'Investor sundowner', 'talk', 6], ['hall', 'Demo night', 'stage', 9], ['garden', 'Garden drinks', 'talk', 4]],
    night: [['dining', 'Founders’ dinner', 'table', 8], ['family', 'Late build', 'desk', 3], ['terrace', 'Late talk', 'talk', 4]],
  },
  artists: {
    dawn: [['terrace', 'Morning sketching', 'row', 4]],
    day: [['gallery', 'Open studio', 'desk', 4], ['court', 'Life drawing', 'circle', 6], ['cafe', 'Café', 'table', 3], ['upper', 'Printmaking', 'table', 4]],
    afternoon: [['gallery', 'Studio', 'desk', 4], ['court', 'Clay table', 'table', 4], ['hall', 'Crit', 'talk', 5], ['library', 'Zine making', 'desk', 3]],
    evening: [['gallery', 'Show opening', 'talk', 6], ['court', 'Live painting', 'circle', 6], ['garden', 'Garden drinks', 'talk', 4], ['terrace', 'Sundowner', 'talk', 5]],
    night: [['dining', 'Artists’ supper', 'table', 8], ['terrace', 'Projection night', 'stage', 7]],
  },
  musicians: {
    dawn: [['terrace', 'Riyaz', 'row', 4]],
    day: [['upper', 'Practice room', 'circle', 4], ['cafe', 'Café', 'table', 3], ['library', 'Listening hour', 'desk', 3]],
    afternoon: [['gallery', 'Recording', 'circle', 4], ['court', 'Rehearsal', 'circle', 6], ['upper', 'Practice room', 'circle', 4]],
    evening: [['court', 'Courtyard concert', 'stage', 9], ['terrace', 'Sundown set', 'circle', 5], ['garden', 'Garden drinks', 'talk', 4]],
    night: [['hall', 'Jam', 'circle', 8], ['dining', 'Musicians’ dinner', 'table', 6], ['terrace', 'Late set', 'stage', 7]],
  },
  dancers: {
    dawn: [['terrace', 'Warm-up', 'row', 6]],
    day: [['hall', 'Class', 'row', 6], ['court', 'Stretching', 'row', 4], ['cafe', 'Café', 'table', 3]],
    afternoon: [['hall', 'Choreography', 'dance', 7], ['gallery', 'Rehearsal', 'dance', 5], ['court', 'Coffee break', 'talk', 3]],
    evening: [['court', 'Dance floor', 'dance', 9], ['terrace', 'Salsa', 'dance', 6], ['garden', 'Garden drinks', 'talk', 4]],
    night: [['hall', 'Dance floor', 'dance', 10], ['terrace', 'Late dancing', 'dance', 6], ['dining', 'Supper', 'table', 6]],
  },
  players: {
    dawn: [['terrace', 'Stretch', 'row', 4]],
    day: [['family', 'Chess', 'table', 2], ['cafe', 'Café', 'table', 3], ['court', 'Carrom', 'table', 4]],
    afternoon: [['gallery', 'Table tennis', 'talk', 4], ['family', 'Board games', 'table', 4], ['court', 'Carrom', 'table', 4]],
    evening: [['terrace', 'Game night', 'table', 6], ['garden', 'Nets', 'talk', 5], ['long', 'Quiz', 'stage', 8]],
    night: [['family', 'Poker', 'table', 5], ['hall', 'Video games', 'talk', 6], ['dining', 'Players’ dinner', 'table', 6], ['court', 'Carrom finals', 'circle', 7]],
  },
}
