import '@fontsource-variable/newsreader/opsz.css'
import '@fontsource-variable/schibsted-grotesk'
import '@fontsource-variable/jetbrains-mono'
import './space.css'
import { BEATS, HOURS, FOG, FOCUS, FLOOR_COPY, TIERS } from './beats.js'

// The booking link (Cal.com or Calendly) for every "Book a call". Until it is
// set, Book a call opens an honest "not available yet" note.
const BOOKING_URL = ''

const $ = (s, el = document) => el.querySelector(s)
const $$ = (s, el = document) => [...el.querySelectorAll(s)]
const smooth = (a, b, x) => {
  const t = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return t * t * (3 - 2 * t)
}
const lerp = (a, b, k) => a + (b - a) * k
const keyed = (table, x) => {
  let i = 0
  while (i < table.length - 2 && x > table[i + 1][0]) i++
  const [a, va] = table[i]
  const [b, vb] = table[i + 1]
  return lerp(va, vb, Math.min(1, Math.max(0, (x - a) / (b - a))))
}
const mixHex = (h1, h2, k) => {
  const a = parseInt(h1.slice(1), 16)
  const b = parseInt(h2.slice(1), 16)
  const c = [16, 8, 0].map((s) => Math.round(lerp((a >> s) & 255, (b >> s) & 255, k)))
  return '#' + c.map((v) => v.toString(16).padStart(2, '0')).join('')
}
const fogAt = (h) => {
  let i = 0
  while (i < FOG.length - 2 && h > FOG[i + 1][0]) i++
  const [a, ca] = FOG[i]
  const [b, cb] = FOG[i + 1]
  return mixHex(ca, cb, smooth(0, 1, (h - a) / (b - a)))
}
const clockText = (h) => `${String(Math.floor(h)).padStart(2, '0')}:${String(Math.floor(((h % 1) * 60) / 30) * 30).padStart(2, '0')} IST`

// Where progress p sits: the beat, how far through it, and the veil.
function locate(p) {
  let veil = 0
  for (const b of BEATS) {
    if (!b.veil) continue
    const w = b.to - b.from
    veil = Math.max(veil, smooth(b.from - w * 0.15, b.from + w * 0.4, p) * (1 - smooth(b.to - w * 0.4, b.to + w * 0.15, p)))
  }
  let beat = BEATS.find((b) => !b.veil && p >= b.from && p < b.to)
  if (!beat) {
    const v = BEATS.find((b) => b.veil && p >= b.from && p < b.to)
    const i = BEATS.indexOf(v)
    beat = p < (v.from + v.to) / 2 ? BEATS[i - 1] : BEATS[i + 1]
  }
  const local = Math.min(1, Math.max(0, (p - beat.from) / (beat.to - beat.from)))
  return { beat, local, veil }
}

// ---------- booking ----------
const dialog = $('.sheet')
let restoreFocus = null
function openSheet(html, label) {
  restoreFocus = document.activeElement
  $('.sheet-body', dialog).innerHTML = html
  dialog.setAttribute('aria-label', label)
  dialog.showModal()
  document.body.classList.add('reading')
  $('.sheet-close', dialog).focus()
}
dialog.addEventListener('close', () => {
  document.body.classList.remove('reading')
  restoreFocus?.focus()
})
$('.sheet-close').addEventListener('click', () => dialog.close())
function book(e) {
  if (BOOKING_URL) return
  e.preventDefault()
  openSheet(
    `<h2>Book a call</h2><p>Call booking is not available yet.</p><p>Please check back soon.</p><button class="link" type="button" data-close>Back to Space →</button>`,
    'Book a call',
  )
  $('[data-close]', dialog).addEventListener('click', () => dialog.close())
}
document.addEventListener('click', (e) => {
  const a = e.target.closest('[data-book]')
  if (a) book(e)
})
if (BOOKING_URL) for (const a of $$('[data-book]')) a.href = BOOKING_URL

// ---------- explore ----------
$('.caption .explore').addEventListener('click', () => {
  const r = FLOOR_COPY[current.beat.floor]
  if (!r) return
  openSheet(
    `<p class="kicker">${r.label}</p><h2>${r.explore.head}</h2>${r.explore.body.map((b) => `<p>${b}</p>`).join('')}
     <p class="actions"><a class="link" href="#book" data-book>Book a call →</a></p>`,
    r.label,
  )
})

let world = null

// ---------- memberships ----------
const tiersEl = $('.tiers')
TIERS.forEach((t, i) => {
  const el = document.createElement('article')
  el.className = 'tier'
  el.innerHTML = `<h3>${t.name}</h3><ul>${t.has.map((h) => `<li>${h}</li>`).join('')}<li>Needs —</li></ul><a class="link" href="#book" data-book>Book a call →</a>`
  el.addEventListener('pointerenter', () => setFocus(i))
  el.addEventListener('focusin', () => setFocus(i))
  tiersEl.append(el)
})
const nav = $('.tier-nav')
TIERS.forEach((t, i) => {
  const b = document.createElement('button')
  b.type = 'button'
  b.className = 'link'
  b.textContent = t.name
  b.addEventListener('click', () => setFocus(i))
  nav.append(b)
})
function setFocus(i) {
  if (world) world.state.tierFocus = i
  $$('.tier').forEach((el, j) => el.classList.toggle('focus', j === i))
  $('.tier-help').textContent = TIERS[i].focus
  $$('.tier-nav button').forEach((b, j) => b.setAttribute('aria-pressed', j === i))
}

// ---------- start ----------
const reduced = matchMedia('(prefers-reduced-motion: reduce)')
let current = locate(0)
const at = +(location.hash.match(/t=([\d.]+)/) || [])[1]
let goal = at >= 0 && at <= 1 ? at : 0
let p = goal
// A link such as #t=0.5 jumps there, also after load.
addEventListener('hashchange', () => {
  const v = +(location.hash.match(/t=([\d.]+)/) || [])[1]
  if (v >= 0 && v <= 1) goal = p = v
})

function webgl() {
  try {
    const c = document.createElement('canvas')
    return !!(c.getContext('webgl2') || c.getContext('webgl'))
  } catch {
    return false
  }
}

// Without motion: the reader, no WebGL. Chosen from the loader or the
// failure note, or automatic when the browser has no WebGL at all.
function still() {
  document.body.classList.add('still')
  stopped = true
}
let stopped = false
for (const b of $$('.still')) b.addEventListener('click', still)

async function start() {
  if (!webgl() || location.search.includes('still')) {
    still()
    return
  }
  countBytes()
  const { createScene } = await import('./scene.js')
  world = await createScene($('.stage'))
  // For measuring (site/PERF.md): the world in dev, or with ?debug.
  if (import.meta.env.DEV || location.search.includes('debug')) window.__world = world
  world.state.still = reduced.matches
  if (matchMedia('(max-width: 720px)').matches) setFocus(1)
  reduced.addEventListener('change', (e) => (world.state.still = e.matches))
  loop()
  // The fog lifts only once the house is drawn.
  await world.firstFrame
  document.body.classList.add('ready')
  performance.mark('house-shown')
}

// Loading: the bytes of the house as they arrive, counted off the network
// (models and the light), against the sizes the server has announced so far.
function countBytes() {
  const bar = $('.loading-bar')
  const text = $('.loading-bytes')
  let got = 0
  let known = 0
  const show = () => {
    if (document.body.classList.contains('ready')) return
    text.textContent = `${(got / 1048576).toFixed(1)} MB`
    bar.style.transform = `scaleX(${known ? Math.min(1, got / known) : 0})`
  }
  const raw = window.fetch
  window.fetch = async (...args) => {
    const res = await raw(...args)
    const url = String(args[0]?.url || args[0])
    if (!/\/(models|world)\//.test(url) || !res.body) return res
    const size = +res.headers.get('content-length') || 0
    known += size
    const reader = res.body.getReader()
    const body = new ReadableStream({
      async pull(c) {
        const { done, value } = await reader.read()
        if (done) return c.close()
        got += value.byteLength
        // No announced size (a compressed response): count what came.
        if (!size) known += value.byteLength
        show()
        c.enqueue(value)
      },
    })
    return new Response(body, { status: res.status, statusText: res.statusText, headers: res.headers })
  }
}

// The page never scrolls; the day does.
const nudge = (d) => {
  if (document.body.classList.contains('reading')) return
  goal = Math.min(1, Math.max(0, goal + d))
}
addEventListener('wheel', (e) => {
  e.preventDefault()
  nudge((e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY) * 0.00016)
}, { passive: false })
let touchY = null
addEventListener('touchstart', (e) => (touchY = e.touches[0].clientY), { passive: true })
addEventListener('touchmove', (e) => {
  if (touchY == null) return
  const y = e.touches[0].clientY
  nudge((touchY - y) / (innerHeight * 6))
  touchY = y
}, { passive: true })
addEventListener('keydown', (e) => {
  if (e.target.closest('input, textarea, dialog')) return
  const step = { ArrowDown: 0.02, ArrowUp: -0.02, PageDown: 0.08, PageUp: -0.08, ' ': e.shiftKey ? -0.08 : 0.08 }[e.key]
  if (step) {
    e.preventDefault()
    nudge(step)
  } else if (e.key === 'Home') goal = 0
  else if (e.key === 'End') goal = 1
})
addEventListener('pointermove', (e) => {
  if (!world) return
  world.state.mx = (e.clientX / innerWidth) * 2 - 1
  world.state.my = (e.clientY / innerHeight) * 2 - 1
})

let last = performance.now()
let shownKey = ''
let held = 0
function loop(now = performance.now()) {
  const dt = Math.min(0.05, (now - last) / 1000)
  last = now
  p = reduced.matches ? goal : p + (goal - p) * (1 - Math.exp(-dt * 3))
  if (Math.abs(goal - p) < 0.00005) p = goal
  current = locate(p)
  const { beat, local } = current
  // A part of the house still on its way stays behind the veil.
  const waiting = (beat.scene === 'floors' && p < 0.33 && world.pending('basement')) || ((beat.scene === 'members' || beat.scene === 'call') && world.pending('props'))
  held = waiting ? 1 : Math.max(0, held - dt * 1.5)
  const veil = Math.max(current.veil, held)
  const h = keyed(HOURS, p)
  const fog = fogAt(h)
  const s = world.state
  s.scene = beat.scene
  s.focus = keyed(FOCUS, Math.min(0.66, Math.max(0.22, p)))
  s.local = local
  s.veil = veil
  s.fog = fog
  s.glow = lerp(0.55, 0, smooth(8, 11, h)) + 0.25 * smooth(17, 18.5, h) * (1 - smooth(19, 20.5, h))
  s.open = beat.open ? smooth(0, 0.8, local) : 0
  s.night = beat.night || beat.scene === 'members' || beat.scene === 'call' ? 1 : smooth(18, 20, h) * 0.8

  // Light text once the fog is dark (by its luminance, not the hour).
  const fl = [1, 3, 5].map((i) => parseInt(fog.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  const dark = 0.2126 * fl[0] + 0.7152 * fl[1] + 0.0722 * fl[2] < 0.22
  document.body.classList.toggle('dark', dark)
  // The first frame is the house alone (board 07); the brief comes with the first scroll.
  document.body.classList.toggle('pristine', beat.id === 'hero' && local < 0.08)
  // With copy up, the house steps right (on a phone, up) to leave it the fog.
  s.brief = beat.id === 'hero' ? smooth(0.04, 0.12, local) : beat.id === 'opening' ? 1 : 0
  document.documentElement.style.setProperty('--fog', fog)
  $('.clock').textContent = clockText(h)
  $('.hint').textContent = beat.id === 'call' ? 'Stay a while' : 'Scroll'

  // Which piece of copy is up.
  const key = veil > 0.6 ? 'veil' : beat.id
  if (key !== shownKey) {
    shownKey = key
    for (const el of $$('[data-beat]')) el.classList.toggle('on', el.dataset.beat.split(' ').includes(key))
    const r = FLOOR_COPY[beat.floor]
    const cap = $('.caption')
    cap.classList.toggle('on', !!r && key !== 'veil')
    if (r) {
      $('.caption .label', cap).textContent = r.label
      $('.caption .title', cap).textContent = r.title
      $('.caption .line', cap).textContent = r.line
    }
  }
  // Copy that sits beside objects follows them on screen.
  const phone = innerWidth <= 720
  if (beat.scene === 'members' && !phone) {
    const pts = world.tierScreens()
    $$('.tier').forEach((el, i) => {
      el.style.transform = `translate(${Math.round(pts[i].x)}px, ${Math.round(pts[i].y)}px) translateX(-50%)`
    })
  }
  if (beat.id === 'opening' && !phone) {
    const pts = world.markerScreens()
    $$('.marker').forEach((el, i) => {
      // Number at the left inset, line running in to the house's edge.
      const x0 = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--inset')) || 32
      el.style.transform = `translate(${x0 + 60}px, ${Math.round(pts[i].y)}px)`
      el.style.setProperty('--len', Math.max(20, pts[i].x - x0 - 100) + 'px')
    })
  }
  if (beat.scene === 'call' && !phone) {
    const c = world.callScreen()
    $('.call-copy').style.transform = `translate(${Math.round(c.x)}px, ${Math.round(c.y)}px) translateY(-50%)`
  }
  if (!stopped) requestAnimationFrame(loop)
}

start().catch((err) => {
  console.error(err)
  document.body.classList.add('failed')
})
$('.retry').addEventListener('click', () => location.reload())
