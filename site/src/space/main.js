import '@fontsource-variable/newsreader/opsz.css'
import '@fontsource-variable/schibsted-grotesk'
import '@fontsource-variable/jetbrains-mono'
import './space.css'
import { BEATS, HOURS, FOG, FOCUS, FLOOR_COPY, TIERS, FEATURES, RAIL, partAt } from './beats.js'

// Where the apply form posts (JSON): a Formspree-style form URL or a
// Cloudflare Worker route, set at build time as VITE_APPLY_URL (.env.local or
// the build environment). Until it is set, the form says it can't send yet.
// Which service and which inbox: site/POLISH.md, Needs your input.
const APPLY_URL = import.meta.env.VITE_APPLY_URL || ''

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
const clockText = (h) => `${String(Math.floor(h)).padStart(2, '0')}:${String(Math.floor(((h % 1) * 60) / 5) * 5).padStart(2, '0')}`

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

// ---------- the sheet ----------
const dialog = $('.sheet')
let restoreFocus = null
function openSheet(html, label, focus = '.sheet-close') {
  // Opened from inside the sheet (a link in an answer): swap the content only.
  if (!dialog.open) restoreFocus = document.activeElement
  $('.sheet-body', dialog).innerHTML = html
  dialog.setAttribute('aria-label', label)
  if (!dialog.open) dialog.showModal()
  document.body.classList.add('reading')
  $(focus, dialog).focus()
}
dialog.addEventListener('close', () => {
  document.body.classList.remove('reading')
  restoreFocus?.focus()
})
$('.sheet-close').addEventListener('click', () => dialog.close())

// ---------- apply ----------
// Every "Book a call" opens a short form; a link from a membership picks it.
const esc = (t) => t.replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])
function apply(tier) {
  const ways = [['member', 'Member'], ['lifetime', 'Lifetime'], ['unsure', 'Not sure yet']]
  openSheet(
    `<p class="kicker">Book a call</p><h2>Tell us about you.</h2>
     <p>We read every one, and write back to set up a call.</p>
     <form class="apply" novalidate>
       <label>Name<input name="name" autocomplete="name" required /></label>
       <label>Email<input name="email" type="email" autocomplete="email" required /></label>
       <label>What are you building?<textarea name="building" rows="2"></textarea></label>
       <fieldset><legend>Which way in?</legend>
         ${ways.map(([v, l]) => `<label class="choice"><input type="radio" name="way" value="${v}"${v === (tier || 'unsure') ? ' checked' : ''} /> ${l}</label>`).join('')}
       </fieldset>
       <label>How did you hear about Space? <span class="optional">(optional)</span><input name="heard" /></label>
       <p class="form-note" role="status" aria-live="polite"></p>
       <button class="link strong" type="submit">Send →</button>
     </form>`,
    'Book a call',
    'input[name="name"]',
  )
  const form = $('.apply', dialog)
  const note = $('.form-note', form)
  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    const bad = [...form.querySelectorAll('[required]')].find((el) => !el.checkValidity())
    if (bad) {
      note.textContent = bad.name === 'email' && bad.value ? 'That email doesn’t look right.' : `Please add your ${bad.name}.`
      bad.setAttribute('aria-invalid', 'true')
      bad.focus()
      return
    }
    if (!APPLY_URL) {
      note.textContent = 'We can’t take this online yet: the form isn’t connected. Please check back soon.'
      return
    }
    const data = Object.fromEntries(new FormData(form))
    const button = $('button[type="submit"]', form)
    button.disabled = true
    note.textContent = 'Sending…'
    try {
      const res = await fetch(APPLY_URL, { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'application/json' }, body: JSON.stringify(data) })
      if (!res.ok) throw new Error(res.status)
      openSheet(
        `<p class="kicker">Sent</p><h2>Thank you, ${esc(data.name.split(' ')[0])}.</h2>
         <p>We’ll write within two days to set up a call.</p>
         <p>Until then, the café opens at 08:00.</p>
         <button class="link" type="button" data-close>Back to Space →</button>`,
        'Sent',
        '[data-close]',
      )
      $('[data-close]', dialog).addEventListener('click', () => dialog.close())
    } catch {
      button.disabled = false
      note.textContent = 'That didn’t send. Please try again in a moment.'
    }
  })
}
document.addEventListener('click', (e) => {
  const a = e.target.closest('[data-book]')
  if (!a) return
  e.preventDefault()
  apply(a.dataset.tier)
})

// ---------- questions ----------
// One list of answers, kept in the reader; the sheet shows a copy.
document.addEventListener('click', (e) => {
  if (!e.target.closest('[data-faq]')) return
  openSheet(`<p class="kicker">Questions</p><h2>Short answers.</h2><div class="faq">${$('#faq').innerHTML}</div>
    <p class="actions"><a class="link" href="#book" data-book>Book a call →</a></p>`, 'Questions')
})

// ---------- explore ----------
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-explore]')
  if (!b) return
  const r = FLOOR_COPY[b.dataset.explore]
  openSheet(
    `<p class="kicker">${r.label}</p><h2>${r.explore.head}</h2>${r.explore.body.map((x) => `<p>${x}</p>`).join('')}
     <p class="actions"><a class="link" href="#book" data-book data-tier="${r.next.tier}">${r.next.text}</a></p>`,
    r.label,
  )
})

let world = null
// Until the first frame, no copy is in view: none of it takes focus.
for (const el of $$('[data-beat]')) el.inert = true

// ---------- the three ways in ----------
// One table: a column per way in, a row per fact, so they compare at a glance;
// then how joining works. Opened from the last chapter.
function waysHtml() {
  const cols = (f) => TIERS.map((t) => `<td>${f(t)}</td>`).join('')
  const row = (label, f, cls = '') => `<tr class="${cls}"><th scope="row">${label}</th>${cols(f)}</tr>`
  const yes = (t, id) => (t.has.includes(id) ? '<span aria-label="Included">✓</span>' : '<span class="no" aria-label="Not included">–</span>')
  return `<p class="kicker">Three ways in</p><h2>Walk in, join, or stay for good.</h2>
    <table class="compare">
    <caption class="sr-only">The three ways in, compared</caption>
    <thead><tr><td></td>${TIERS.map((t) => `<th scope="col">${t.name}</th>`).join('')}</tr></thead>
    <tbody>
      ${row('For', (t) => t.for)}
      ${row('Hours', (t) => t.hours)}
      ${FEATURES.map((f) => row(f.label, (t) => yes(t, f.id), 'feature')).join('')}
      ${row('Needs', (t) => t.needs, 'needs')}
      ${row('Price', (t) => t.price, 'price')}
    </tbody>
    <tfoot><tr><td></td>${cols((t) => (t.id === 'walkin' ? '<span class="no">Just come in</span>' : `<a class="link" href="#book" data-book data-tier="${t.id}">Book a call →</a>`))}</tr></tfoot>
    </table>
    <p class="small">Prices are being set; we’ll go through them on a call.</p>
    <p class="kicker">How joining works</p>
    <ol class="steps">${$$('.reader .steps-src li').map((li) => `<li>${li.innerHTML}</li>`).join('')}</ol>`
}
document.addEventListener('click', (e) => {
  if (e.target.closest('[data-ways]')) openSheet(waysHtml(), 'Three ways in')
})

// ---------- the clock and the rail ----------
// Bengaluru's real time, beside the house's.
function tickNow() {
  $('.now').textContent = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Kolkata', hour: '2-digit', minute: '2-digit' }).format(new Date())
}
tickNow()
setInterval(tickNow, 15000)
for (const [label, to, name] of RAIL) {
  const b = document.createElement('button')
  b.type = 'button'
  b.textContent = label
  b.setAttribute('aria-label', name)
  b.addEventListener('click', () => nudge(to - goal))
  $('.rail').append(b)
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
  const reader = $('.reader')
  reader.tabIndex = -1
  reader.focus()
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
  reduced.addEventListener('change', (e) => (world.state.still = e.matches))
  loop()
  // The fog lifts only once the house is drawn.
  await world.firstFrame
  document.body.classList.add('ready')
  $('.loading').inert = true
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
let lastInput = 0
let lastDir = 1
const nudge = (d) => {
  if (document.body.classList.contains('reading')) return
  goal = Math.min(1, Math.max(0, goal + d))
  lastInput = performance.now()
  if (d) lastDir = Math.sign(d)
}
// Where each beat reads settled: its copy up, the veil behind it.
// The first beat's stop is its start, so the first step goes in.
const STOPS = BEATS.filter((b) => !b.veil && b.id !== 'move').map((b) => (b.from ? b.from + Math.min(0.02, (b.to - b.from) * 0.3) : 0))
const step = (dir) => {
  const next = dir > 0 ? STOPS.find((x) => x > goal + 0.002) : [...STOPS].reverse().find((x) => x < goal - 0.002)
  if (next != null) nudge(next - goal)
}
addEventListener('wheel', (e) => {
  e.preventDefault()
  // One fling must not carry through a beat: a cap per event.
  const d = (e.deltaMode === 1 ? e.deltaY * 16 : e.deltaY) * 0.00016
  nudge(Math.max(-0.025, Math.min(0.025, d)))
}, { passive: false })
let touchY = null
addEventListener('touchstart', (e) => (touchY = e.touches[0].clientY), { passive: true })
addEventListener('touchmove', (e) => {
  if (touchY == null) return
  const y = e.touches[0].clientY
  // A full-height swipe carries an eighth of the day: about one beat.
  nudge((touchY - y) / (innerHeight * 8))
  touchY = y
}, { passive: true })
addEventListener('keydown', (e) => {
  if (e.target.closest('input, textarea, dialog')) return
  // Arrows walk through a beat; Space and the page keys go beat to beat.
  const small = { ArrowDown: 0.015, ArrowUp: -0.015 }[e.key]
  const page = { PageDown: 1, PageUp: -1, ' ': e.shiftKey ? -1 : 1 }[e.key]
  if (small || page) e.preventDefault()
  if (small) nudge(small)
  else if (page) step(page)
  else if (e.key === 'Home') nudge(-goal)
  else if (e.key === 'End') nudge(1 - goal)
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
  // Left resting in a veil, the day carries on through it, the way it was going.
  if (now - lastInput > 700 && Math.abs(goal - p) < 0.002) {
    const v = BEATS.find((b) => b.veil && goal > b.from && goal < b.to)
    if (v) {
      goal = lastDir > 0 ? STOPS.find((x) => x > v.to) ?? v.to : [...STOPS].reverse().find((x) => x < v.from) ?? v.from
      lastInput = now
    }
  }
  p = reduced.matches ? goal : p + (goal - p) * (1 - Math.exp(-dt * 3))
  if (Math.abs(goal - p) < 0.00005) p = goal
  current = locate(p)
  const { beat, local } = current
  // A part of the house still on its way stays behind the veil.
  const focus = keyed(FOCUS, Math.min(0.7, Math.max(0.13, p)))
  const waiting = beat.scene === 'floors' && focus < 0.99 && world.pending('basement')
  held = waiting ? 1 : Math.max(0, held - dt * 1.5)
  const veil = Math.max(current.veil, held)
  const h = keyed(HOURS, p)
  const fog = fogAt(h)
  const s = world.state
  s.scene = beat.scene
  s.focus = focus
  s.local = local
  s.veil = veil
  s.fog = fog
  s.glow = lerp(0.55, 0, smooth(8, 11, h)) + 0.25 * smooth(17, 18.5, h) * (1 - smooth(19, 20.5, h))
  s.open = beat.open ? smooth(0, 0.8, local) : 0
  s.night = beat.night ? 1 : smooth(18, 20, h) * 0.8

  // Light text once the fog is dark (by its luminance, not the hour).
  const fl = [1, 3, 5].map((i) => parseInt(fog.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  const dark = 0.2126 * fl[0] + 0.7152 * fl[1] + 0.0722 * fl[2] < 0.22
  document.body.classList.toggle('night', dark)
  document.documentElement.style.setProperty('--fog', fog)
  $('.clock-time').textContent = clockText(h)
  $('.clock-part').textContent = partAt(h)
  $('.rail-fill').style.transform = `scaleY(${p})`

  // Which piece of copy is up.
  const key = veil > 0.6 ? 'veil' : beat.id
  if (key !== shownKey) {
    shownKey = key
    // Copy not in view is out of the tab order and the reading order too.
    for (const el of $$('[data-beat]')) el.inert = !el.classList.toggle('on', el.dataset.beat === key)
  }
  if (!stopped) requestAnimationFrame(loop)
}

start().catch((err) => {
  console.error(err)
  document.body.classList.add('failed')
})
$('.retry').addEventListener('click', () => location.reload())
