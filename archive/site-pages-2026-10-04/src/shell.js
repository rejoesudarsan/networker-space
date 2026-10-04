// Shared by every page: fonts, styles, header/footer behaviour, booking links
// and the renderers used on more than one page.
import '@fontsource/bungee/400.css'
import '@fontsource-variable/anek-latin/wdth.css'
import '@fontsource-variable/anek-kannada/wdth.css'
import './style.css'
import { site, hours, tiers, access, steps } from './content.js'

export const draftNote = (text) => (site.draft ? `<p class="draft-note">${esc(text)}</p>` : '')

export const $ = (sel, root = document) => root.querySelector(sel)
export const $$ = (sel, root = document) => [...root.querySelectorAll(sel)]
export const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c])
export const tierById = Object.fromEntries(tiers.map((t) => [t.id, t]))

export const ICON = {
  yes: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4.5 12.5l5 5 10-11" /></svg>',
  no: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 12h10" /></svg>',
  arrow: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6" /></svg>',
}

export const chips = (ids) => ids.map((id) => `<b class="chip chip--${id}">${esc(tierById[id].name)}</b>`).join('')

// ---------- renderers ----------
export function renderTiers(el, { compact = false } = {}) {
  el.innerHTML = tiers
    .map(
      (t) => `
  <article class="tier board tier--${t.id}${compact ? ' tier--compact' : ''}" aria-labelledby="tier-${t.id}">
    <h3 id="tier-${t.id}" class="tier__name">${esc(t.name)}</h3>
    <p class="tier__metal">${esc(t.metal)} membership</p>
    <p class="tier__pitch">${esc(t.pitch)}</p>
    ${
      compact
        ? `<ul class="list list--get">${t.includes.slice(0, 3).map((x) => `<li>${ICON.yes}<span>${esc(x)}</span></li>`).join('')}</ul>
           <a class="btn btn--ink" href="/memberships/#tier-${t.id}">What it takes</a>`
        : `<div class="tier__cols">
      <div>
        <h4>You get</h4>
        <ul class="list list--get">${t.includes.map((x) => `<li>${ICON.yes}<span>${esc(x)}</span></li>`).join('')}</ul>
      </div>
      <div>
        <h4>It takes</h4>
        <ul class="list list--need">${t.needs.map((x) => `<li>${ICON.arrow}<span>${esc(x)}</span></li>`).join('')}</ul>
      </div>
    </div>
    <a class="btn btn--ink" data-book data-tier="${esc(t.name)}" href="/join/#book">Book a call about ${esc(t.name)}</a>`
    }
  </article>`,
    )
    .join('')
}

export function renderMatrix(table) {
  const cell = (v) =>
    v === true
      ? `<td class="yes">${ICON.yes}<span class="sr">Included</span></td>`
      : v === false
        ? `<td class="no">${ICON.no}<span class="sr">Not included</span></td>`
        : `<td>${esc(v)}</td>`
  $('thead', table).innerHTML = `<tr><th scope="col"><span class="sr">Feature</span></th>${tiers
    .map((t) => `<th scope="col"><span class="chip chip--${t.id}">${esc(t.name)}</span></th>`)
    .join('')}</tr>`
  $('tbody', table).innerHTML = access
    .map((row) => `<tr><th scope="row">${esc(row.label)}</th>${tiers.map((t) => cell(row[t.id])).join('')}</tr>`)
    .join('')
}

export function renderSteps(el) {
  el.innerHTML = steps.map((s) => `<li class="step"><h3>${esc(s.title)}</h3><p>${esc(s.body)}</p></li>`).join('')
}

// ---------- copy slots ----------
for (const el of $$('[data-slot]')) el.textContent = site[el.dataset.slot] ?? ''
for (const el of $$('.foot__hours')) el.textContent = `${hours.day.label} ${hours.day.time} · ${hours.night.label} ${hours.night.time}`
for (const el of $$('[data-hours]')) {
  const h = hours[el.dataset.hours]
  el.innerHTML = `
    <span class="hours__label">${esc(h.label)}</span>
    <span class="hours__time">${esc(h.time)}</span>
    <span class="hours__kn" lang="kn">${esc(h.kn)}</span>`
}

// ---------- current page in the nav ----------
const here = location.pathname.replace(/index\.html$/, '')
for (const a of $$('.nav nav a, .foot__nav a')) {
  if (a.getAttribute('href') === here) a.setAttribute('aria-current', 'page')
}

// ---------- booking ----------
const mailto = (tier) =>
  site.email ? `mailto:${site.email}?subject=${encodeURIComponent(`Intro call${tier ? ` · ${tier}` : ''}`)}` : null
const bookingHref = (tier) => {
  if (!site.bookingUrl) return mailto(tier)
  if (!tier) return site.bookingUrl
  const url = new URL(site.bookingUrl)
  url.searchParams.set('notes', `Interested in ${tier} membership`)
  return url.toString()
}

export function wireBooking(root = document) {
  for (const a of $$('[data-book]', root)) {
    const href = bookingHref(a.dataset.tier)
    if (!href) continue
    a.href = href
    if (!href.startsWith('mailto:')) {
      a.target = '_blank'
      a.rel = 'noopener'
    }
  }
  for (const slot of $$('.book__slot', root)) {
    if (site.bookingUrl) {
      slot.innerHTML = `<a class="btn btn--red btn--big" href="${esc(site.bookingUrl)}" target="_blank" rel="noopener">Pick a time</a>`
    } else if (site.email) {
      slot.innerHTML = `<a class="btn btn--red btn--big" href="${esc(mailto())}">Email ${esc(site.email)}</a>`
    } else {
      slot.innerHTML = `<p class="book__pending">Scheduling opens soon.</p>`
    }
  }
}
if (!site.bookingUrl && import.meta.env.DEV) console.warn('[networker] Set site.bookingUrl in src/content.js to enable booking.')

// ---------- mobile menu ----------
const menuBtn = $('.nav__menu')
menuBtn?.addEventListener('click', () => {
  const open = menuBtn.getAttribute('aria-expanded') !== 'true'
  menuBtn.setAttribute('aria-expanded', String(open))
  menuBtn.textContent = open ? 'Close' : 'Menu'
  $('.nav').classList.toggle('nav--open', open)
})

// ---------- nav backing ----------
// Pages decide when the nav needs a solid backing; by default once you scroll.
export const nav = $('.nav')
export let navSolidWhen = () => scrollY > 24
export const setNavRule = (fn) => (navSolidWhen = fn)
const syncNav = () => nav.classList.toggle('nav--solid', navSolidWhen())
addEventListener('scroll', syncNav, { passive: true })
queueMicrotask(syncNav)

// ---------- capability ----------
export const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)').matches
export const hasGL = (() => {
  try {
    const c = document.createElement('canvas')
    return !!(c.getContext('webgl2') || c.getContext('webgl'))
  } catch {
    return false
  }
})()
export const use3D = hasGL && !reducedMotion
document.documentElement.classList.add(use3D ? 'gl' : 'static')
