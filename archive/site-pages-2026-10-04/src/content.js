// Everything a non-developer needs to edit lives in this file.
// Items marked PROPOSAL are suggestions to confirm before launch.

export const site = {
  name: 'Networker Space',
  nameKn: 'ನೆಟ್‌ವರ್ಕರ್ ಸ್ಪೇಸ್',
  tagline: 'A private club for people building startups.',
  location: 'HSR Layout, Bengaluru',
  // Paste your Cal.com or Calendly link, e.g. 'https://cal.com/your-team/intro'.
  // Leave empty and every "Book a call" button falls back to the email below.
  bookingUrl: '',
  email: '',
  instagram: '',
  // While true, pages label proposed terms and the sample programme as drafts.
  draft: true,
}

export const hours = {
  day: { label: 'Café', time: '8 am – 6 pm', kn: 'ಬೆಳಿಗ್ಗೆ 8 – ಸಂಜೆ 6', note: 'Walk in, order, work.' },
  night: {
    label: 'Club',
    time: '6 pm – 11 pm',
    kn: 'ಸಂಜೆ 6 – ರಾತ್ರಿ 11',
    // PROPOSAL: confirm which evenings run the programme.
    note: 'Programmed evenings, three nights a week.',
  },
}

// The four floors of the house, in walking order. `plan` must match a file in
// public/plans/ and a model in public/models/ (npm run house).
// `level` is the storey (0 = lower level).
export const floors = [
  { id: 'ground', plan: 'ground', level: 1, paint: '#f4eee1', ink: '#16130f', name: 'The Café', floor: 'Ground floor', floorKn: 'ನೆಲ ಮಹಡಿ' },
  { id: 'basement', plan: 'basement', level: 0, paint: '#0b5e57', ink: '#f4eee1', name: 'The Quiet Floor', floor: 'Lower level', floorKn: 'ನೆಲಮಾಳಿಗೆ' },
  { id: 'first', plan: 'first', level: 2, paint: '#c2361e', ink: '#f4eee1', name: 'Library & Games', floor: 'First floor', floorKn: 'ಮೊದಲ ಮಹಡಿ' },
  { id: 'second', plan: 'second', level: 3, paint: '#eba21c', ink: '#24306e', name: 'The Terrace', floor: 'Second floor', floorKn: 'ತಾರಸಿ' },
]

// The walk, room by room. `time` is the hour (24h) the scroll clock shows.
// `rect` is the room on its floor as [left, top, right, bottom], 0–1 of the
// floor's footprint, seen from above with the street at the bottom.
// `was` is the label printed on the existing drawing.
// PROPOSAL: every room use below.
export const rooms = [
  {
    floor: 'ground', time: 8, rect: [0.01, 0.43, 0.46, 0.6], was: 'Entrance, garden',
    name: 'Garden gate', body: 'Walk in off the street, through the garden. No badge, no front desk queue.',
    access: ['walk-in', 'regular', 'house'],
  },
  {
    floor: 'ground', time: 9, rect: [0.2, 0.12, 0.59, 0.44], was: 'Dining 1, Family 1',
    name: 'The café', body: 'Long tables, good coffee and plenty of sockets. Open to every member from 8 in the morning.',
    access: ['walk-in', 'regular', 'house'],
  },
  {
    floor: 'ground', time: 10.5, rect: [0.58, 0.43, 0.91, 0.81], was: 'Double height, Living 1',
    name: 'The hall', body: 'A double-height room for the café overflow by day and the occasional talk by night.',
    access: ['walk-in', 'regular', 'house'],
  },
  {
    floor: 'basement', time: 11.5, rect: [0.35, 0.42, 0.95, 0.77], was: 'Office',
    name: 'Focus rooms', body: 'One level down, away from the street. Quiet rooms with a door that closes.',
    access: ['regular', 'house'],
  },
  {
    floor: 'basement', time: 12.5, rect: [0.52, 0.0, 0.95, 0.21], was: 'Office / Den',
    name: 'The den', body: 'Phone booths and a small room for the call you cannot take at a café table.',
    access: ['regular', 'house'],
  },
  {
    floor: 'basement', time: 14, rect: [0.69, 0.76, 0.96, 1.0], was: 'Open to sky court',
    name: 'Sky court', body: 'An open-to-sky court for a break between deep-work blocks. Phones stay upstairs.',
    access: ['regular', 'house'],
  },
  {
    floor: 'first', time: 15, rect: [0.5, 0.13, 0.98, 0.35], was: 'Family 2, Library',
    name: 'The library', body: 'Founder books, reading chairs and the hour of thinking before the pitch.',
    access: ['regular', 'house'],
  },
  {
    floor: 'first', time: 16, rect: [0.21, 0.33, 0.77, 0.52], was: 'Dining 2',
    name: 'Boardroom', body: 'A big table for the investor meeting, the team standup or the pitch rehearsal.',
    access: ['regular', 'house'],
  },
  {
    floor: 'first', time: 18.5, rect: [0.62, 0.69, 0.98, 1.0], was: 'Living 2',
    name: 'Game room', body: 'Opens when the laptops close: board games, a console and a cooler.',
    access: ['regular', 'house'],
  },
  {
    floor: 'second', time: 19.5, rect: [0.03, 0.01, 0.33, 1.0], was: 'Terrace',
    name: 'The terrace', body: 'Where the evenings happen: demo nights and fireside talks under the sky, until 11.',
    access: ['walk-in', 'regular', 'house'],
  },
  {
    floor: 'second', time: 21, rect: [0.53, 0.64, 0.96, 1.0], was: 'Bedroom 5',
    name: 'Dinner room', body: 'Founder dinners for twelve. Members’ nights for Regulars, invite-only nights for House.',
    access: ['regular', 'house'],
  },
  {
    floor: 'second', time: 22.5, rect: [0.38, 0.0, 0.72, 0.31], was: 'Bedroom 4',
    name: 'House room', body: 'A private room for House teams and their guests, late into the evening.',
    access: ['house'],
  },
]

// PROPOSAL: tier names, inclusions and requirements. Pricing is shared on the call.
export const tiers = [
  {
    id: 'walk-in',
    name: 'Walk-In',
    metal: 'Silver',
    pitch: 'For people who want a seat at the table.',
    includes: [
      'The café, 8 am to 6 pm',
      'Book a table on the day',
      'Open nights on the terrace',
      'Member rates at the café counter',
    ],
    needs: [
      'An intro call with the team',
      'You work on or around a startup',
      'Government ID at your first visit',
      'Month to month, cancel any time',
    ],
  },
  {
    id: 'regular',
    name: 'Regular',
    metal: 'Gold',
    pitch: 'For founders who need to think, meet and unwind.',
    includes: [
      'Everything in Walk-In',
      'Quiet focus rooms on the lower level',
      'Meeting-room hours every month',
      'Game room in the evenings',
      'Members-only nights: dinners, office hours, pitch practice',
      'Book tables up to a week ahead',
    ],
    needs: [
      'An intro call with the team',
      'You are building or working at a startup, or a member refers you',
      'Three-month minimum',
    ],
  },
  {
    id: 'house',
    name: 'House',
    metal: 'Platinum',
    pitch: 'For teams who want the house to be their base.',
    includes: [
      'Everything in Regular',
      'Seats for your team',
      'Bring guests and friends',
      'Every evening, including invite-only sessions',
      'Priority on meeting rooms',
      'Host your own evening on the terrace',
    ],
    needs: [
      'An intro call and a walk-through of the house',
      'Two member referrals, or an invitation from the team',
      'A named team lead; team size agreed on the call',
      'Six-month minimum',
    ],
  },
]

// Rows of the comparison board. Values: true, false, or short text.
export const access = [
  { label: 'Café, 8 am – 6 pm', 'walk-in': true, regular: true, house: true },
  { label: 'Table booking', 'walk-in': 'Same day', regular: 'A week ahead', house: 'A month ahead' },
  { label: 'Quiet focus rooms', 'walk-in': false, regular: true, house: true },
  { label: 'Meeting rooms', 'walk-in': false, regular: 'Monthly hours', house: 'Priority' },
  { label: 'Game room', 'walk-in': false, regular: true, house: true },
  { label: 'Evenings, 6 – 11 pm', 'walk-in': 'Open nights', regular: 'Members’ nights', house: 'Every night' },
  { label: 'Guests', 'walk-in': false, regular: false, house: true },
  { label: 'Team seats', 'walk-in': false, regular: false, house: true },
  { label: 'Host an evening', 'walk-in': false, regular: false, house: true },
]

export const steps = [
  { title: 'Book a call', body: 'Twenty minutes with the team. Tell us what you are building and which membership you have in mind.' },
  { title: 'Visit the house', body: 'Come by for a coffee during café hours and walk the four floors.' },
  { title: 'Join', body: 'We confirm your membership, pricing and start date over email.' },
]

export const pages = [
  { href: '/', label: 'Home' },
  { href: '/house/', label: 'The house' },
  { href: '/memberships/', label: 'Memberships' },
  { href: '/evenings/', label: 'Evenings' },
  { href: '/join/', label: 'Join' },
]

// PROPOSAL: the evening formats and who they are open to. Confirm before launch.
export const evenings = [
  { time: '18:00', name: 'Doors to the club', where: 'Ground floor', body: 'The café turns over to members. Lights down, music up.', access: ['walk-in', 'regular', 'house'] },
  { time: '18:30', name: 'Office hours', where: 'Library', body: 'Founders and operators book twenty-minute slots for advice on hiring, fundraising or product.', access: ['regular', 'house'] },
  { time: '19:00', name: 'Demo night', where: 'The terrace', body: 'Five teams, five minutes each, then questions from the floor.', access: ['walk-in', 'regular', 'house'] },
  { time: '19:30', name: 'Fireside talk', where: 'The hall', body: 'One founder, one host and an honest conversation about the hard parts.', access: ['walk-in', 'regular', 'house'] },
  { time: '20:00', name: 'Game night', where: 'Game room', body: 'Board games, a console and a leaderboard nobody admits to caring about.', access: ['regular', 'house'] },
  { time: '20:30', name: 'Founder dinner', where: 'Dinner room', body: 'Twelve seats, one long table, no pitching at the table.', access: ['regular', 'house'] },
  { time: '21:00', name: 'House night', where: 'House room', body: 'Invite-only evenings for House members, their teams and guests.', access: ['house'] },
  { time: '23:00', name: 'Last call', where: 'Everywhere', body: 'The house closes. The café opens again at 8.', access: ['walk-in', 'regular', 'house'] },
]

export const rhythm = {
  day: {
    title: 'Café by day',
    body: 'From 8 in the morning the ground floor works like a neighbourhood café for members: walk in, order, find a table, get to work. Regulars and House members head downstairs to the quiet floor.',
  },
  night: {
    title: 'Club by night',
    body: 'At 6 the house changes. Three evenings a week there is a programme of talks, demo nights, dinners and games across the terrace, hall and first floor until 11.',
  },
}
