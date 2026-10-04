import { $, $$, esc, chips, wireBooking, setNavRule, use3D, draftNote } from '../shell.js'
import { floors, rooms } from '../content.js'

const fmtHour = (h) => `${String(Math.floor(h)).padStart(2, '0')}:${String(Math.round((h % 1) * 60)).padStart(2, '0')}`
const floorById = Object.fromEntries(floors.map((f) => [f.id, f]))
const root = document.documentElement
root.style.setProperty('--stops', rooms.length)

// ---------- room cards ----------
$('.stops').innerHTML = rooms
  .map((r, i) => {
    const f = floorById[r.floor]
    return `
  <li class="stop board" style="--paint:${f.paint};--ink:${f.ink}" data-i="${i}">
    <h2 class="stop__name">${esc(r.name)}</h2>
    <p class="stop__floor"><span>${esc(f.floor)}</span> <span lang="kn">${esc(f.floorKn)}</span><span class="stop__count">${i + 1} / ${rooms.length}</span></p>
    <p class="stop__body">${esc(r.body)}</p>
    <p class="stop__access"><span>Open to</span> ${chips(r.access)}</p>
    <p class="stop__was">On the drawing: ${esc(r.was)}</p>
    <img class="stop__plan" src="/plans/${f.plan}.png" alt="Existing floor plan of the ${esc(f.floor.toLowerCase())}" loading="lazy" />
  </li>`
  })
  .join('')

$('.legend').innerHTML = [...floors]
  .sort((a, b) => b.level - a.level)
  .map((f) => `<li style="--paint:${f.paint}"><span class="legend__swatch"></span><b>${esc(f.name)}</b><span>${esc(f.floor)}</span></li>`)
  .join('')
$('.hero--house .board').insertAdjacentHTML('beforeend', draftNote('Room uses shown are proposals.'))
wireBooking()

// ---------- scroll driver ----------
const journey = $('.journey')
const assemble = $('.assemble')
const stopsEls = $$('.stop')
const clockTime = $('.clock__time')
const clockPhase = $('.clock__phase')
const bar = $('.progress span')

// Scroll progress → room index (holding on each room) → hour of day.
const N = rooms.length
const stopAt = (p) => {
  const x = Math.min(N - 1, Math.max(0, p * N - 0.35))
  const i = Math.floor(x)
  return Math.min(N - 1, i + Math.max(0, (x - i - 0.4) / 0.6))
}
const hourAt = (stop, p) => {
  const i = Math.floor(stop)
  const a = rooms[i].time
  const b = i + 1 < N ? rooms[i + 1].time : 23
  const k = i + 1 < N ? stop - i : Math.max(0, (p * N - (N - 1) - 0.35) / 0.65)
  return a + (b - a) * Math.min(1, k)
}

// Sky colour by hour: sign-yellow day, dusk orange, ultramarine night.
const SKY = [
  [8, [235, 162, 28]],
  [15, [232, 148, 30]],
  [17.5, [217, 104, 42]],
  [19, [36, 48, 110]],
  [23, [14, 19, 48]],
]
const skyAt = (h) => {
  for (let i = 0; i < SKY.length - 1; i++) {
    const [a, ca] = SKY[i]
    const [b, cb] = SKY[i + 1]
    if (h <= b) {
      const t = Math.max(0, (h - a) / (b - a))
      return ca.map((c, k) => Math.round(c + (cb[k] - c) * t))
    }
  }
  return SKY.at(-1)[1]
}

const sectionProgress = (el) => {
  const r = el.getBoundingClientRect()
  const span = r.height - innerHeight
  return span > 0 ? Math.min(1, Math.max(0, -r.top / span)) : 0
}

const state = { journey: 0, assemble: 0, hero: 0, stop: 0, hour: 8, hidden: false }
let activeStop = -1
setNavRule(() => assemble.getBoundingClientRect().bottom < 80)

function update() {
  state.hero = Math.min(1, scrollY / innerHeight)
  state.journey = sectionProgress(journey)
  state.assemble = sectionProgress(assemble)
  state.hidden = assemble.getBoundingClientRect().bottom < 0
  state.stop = stopAt(state.journey)
  const hour = state.assemble > 0 ? 23 : hourAt(state.stop, state.journey)
  state.hour = hour

  const [r, g, b] = skyAt(hour)
  root.style.setProperty('--sky', `rgb(${r} ${g} ${b})`)
  root.dataset.phase = hour >= 18.25 ? 'night' : 'day'

  clockTime.textContent = fmtHour(Math.min(23, hour))
  clockPhase.textContent = hour < 18 ? 'Café hours' : hour < 22.9 ? 'Club hours' : 'Last call'
  bar.style.transform = `scaleX(${state.journey})`

  const idx = Math.round(state.stop)
  if (idx !== activeStop) {
    stopsEls.forEach((el, i) => el.classList.toggle('is-active', i === idx))
    activeStop = idx
  }
}

if (use3D) {
  addEventListener('scroll', update, { passive: true })
  addEventListener('resize', update)
  update()
  import('../scene.js').then(({ startScene }) => startScene($('#scene'), state, floors, rooms))
}
