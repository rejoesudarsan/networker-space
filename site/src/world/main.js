import '@fontsource-variable/newsreader/opsz.css'
import '@fontsource-variable/schibsted-grotesk'
import '@fontsource-variable/jetbrains-mono'
import './world.css'
import { PEOPLE, partAt } from './program.js'

// The booking link (Cal.com or Calendly) for every "Book a call" button.
// Add it here; until then the buttons stay on the page without a destination.
const BOOKING_URL = ''
if (BOOKING_URL) for (const a of document.querySelectorAll('[data-book]')) a.href = BOOKING_URL

const PART_NAMES = { dawn: 'Dawn', day: 'Morning', afternoon: 'Afternoon', evening: 'Evening', night: 'Night' }
const $ = (s) => document.querySelector(s)
const fmt = (h) => {
  const m = Math.floor((h % 1) * 60 / 5) * 5
  return `${String(Math.floor(h)).padStart(2, '0')}:${String(m).padStart(2, '0')}`
}

function webgl() {
  try {
    const c = document.createElement('canvas')
    return !!(c.getContext('webgl2') || c.getContext('webgl'))
  } catch {
    return false
  }
}

// ---------- Bengaluru's real time, beside the house's ----------
function tickNow() {
  $('.now').textContent = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' }).format(new Date())
}
tickNow()
setInterval(tickNow, 15000)

// ---------- who's inside ----------
const options = $('.who-options')
for (const p of PEOPLE) {
  const b = document.createElement('button')
  b.type = 'button'
  b.textContent = p.name
  b.dataset.id = p.id
  b.setAttribute('aria-pressed', p.id === 'all')
  options.append(b)
}

const chapters = [...document.querySelectorAll('.chapter')]
const reduced = matchMedia('(prefers-reduced-motion: reduce)')

async function start() {
  if (!webgl()) {
    document.body.classList.add('flat')
    return
  }
  const { createWorld } = await import('./world.js')
  const world = await createWorld($('.stage'))
  world.setReducedMotion(reduced.matches)
  reduced.addEventListener('change', (e) => world.setReducedMotion(e.matches))
  document.body.classList.add('ready')

  options.addEventListener('click', (e) => {
    const b = e.target.closest('button')
    if (!b) return
    world.state.persona = b.dataset.id
    for (const o of options.children) o.setAttribute('aria-pressed', o === b)
  })

  // ---------- virtual scroll: the page never moves, the day does ----------
  let goal = 0
  let p = 0
  const nudge = (d) => (goal = Math.min(1, Math.max(0, goal + d)))
  addEventListener('wheel', (e) => {
    e.preventDefault()
    nudge((e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY) * 0.0002)
  }, { passive: false })
  let touchY = null
  addEventListener('touchstart', (e) => (touchY = e.touches[0].clientY), { passive: true })
  addEventListener('touchmove', (e) => {
    if (touchY == null) return
    const y = e.touches[0].clientY
    nudge((touchY - y) / (innerHeight * 5))
    touchY = y
  }, { passive: true })
  addEventListener('keydown', (e) => {
    if (e.target.closest('input, textarea')) return
    const step = { ArrowDown: 0.03, ArrowUp: -0.03, PageDown: 0.12, PageUp: -0.12, ' ': e.shiftKey ? -0.12 : 0.12 }[e.key]
    if (step) {
      e.preventDefault()
      nudge(step)
    } else if (e.key === 'Home') goal = 0
    else if (e.key === 'End') goal = 1
  })
  for (const b of document.querySelectorAll('.rail button')) b.addEventListener('click', () => (goal = +b.dataset.to))
  addEventListener('pointermove', (e) => {
    world.state.mx = (e.clientX / innerWidth) * 2 - 1
    world.state.my = (e.clientY / innerHeight) * 2 - 1
  })

  // ---------- room labels: "Courtyard → Pitch circle" ----------
  const tagLayer = $('.tags')
  const tags = new Map()
  const SCRAMBLE = 'abcdefghijklmnopqrstuvwxyz'
  function scramble(el, text) {
    let frame = 0
    const run = () => {
      frame++
      el.textContent = text.split('').map((ch, i) => (ch === ' ' || i < frame * 1.5 ? ch : SCRAMBLE[(Math.random() * 26) | 0])).join('')
      if (frame * 1.5 < text.length) requestAnimationFrame(run)
    }
    reduced.matches ? (el.textContent = text) : run()
  }
  function drawTags(open) {
    const seen = new Set()
    const list = world.labels().filter((l) => open > 0.6 && l.near < 1.6).sort((a, b) => a.y - b.y)
    for (const l of list) {
      seen.add(l.id)
      let t = tags.get(l.id)
      if (!t) {
        t = document.createElement('div')
        t.className = 'tag'
        t.innerHTML = '<i></i><span class="tag-room"></span><span class="tag-use"></span>'
        t.querySelector('.tag-room').textContent = l.room
        tagLayer.append(t)
        tags.set(l.id, t)
        requestAnimationFrame(() => t.classList.add('on'))
      }
      if (t.dataset.use !== l.use) {
        t.dataset.use = l.use
        scramble(t.querySelector('.tag-use'), l.use)
      }
      t.style.transform = `translate3d(${l.x.toFixed(1)}px, ${l.y.toFixed(1)}px, 0)`
    }
    for (const [id, t] of tags) {
      if (seen.has(id)) continue
      tags.delete(id)
      t.classList.remove('on')
      setTimeout(() => t.remove(), 500)
    }
  }

  // ---------- the loop ----------
  let last = performance.now()
  let current = -1
  let wasNight = null
  const fill = $('.rail-fill')
  function loop(now) {
    const dt = Math.min(0.05, (now - last) / 1000)
    last = now
    p = reduced.matches ? goal : p + (goal - p) * (1 - Math.exp(-dt * 3.2))
    if (Math.abs(goal - p) < 0.00005) p = goal
    world.state.p = p

    const h = world.state.hour
    $('.clock-time').textContent = fmt(h)
    $('.clock-part').textContent = PART_NAMES[partAt(h)]
    fill.style.transform = `scaleY(${p})`

    const idx = chapters.findIndex((c) => p >= +c.dataset.from && p < +c.dataset.to)
    if (idx !== current) {
      chapters.forEach((c, i) => c.classList.toggle('on', i === idx))
      current = idx
    }
    document.body.classList.toggle('picking', p > 0.12 && p < 0.9)
    const night = world.state.night > 0.5
    if (night !== wasNight) {
      document.body.classList.toggle('night', night)
      wasNight = night
    }
    drawTags(world.state.open)
    document.body.style.setProperty('--sky', world.skyHex())
    requestAnimationFrame(loop)
  }
  requestAnimationFrame(loop)
}

start().catch((err) => {
  console.error(err)
  document.body.classList.add('flat')
})
