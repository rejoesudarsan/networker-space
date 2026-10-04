import { $, esc, renderTiers, wireBooking, use3D } from '../shell.js'
import { floors, rooms, rhythm, hours } from '../content.js'

$('[data-rhythm="day"]').innerHTML = `<h3>${esc(rhythm.day.title)}</h3><p class="rhythm__time">${esc(hours.day.time)}</p><p>${esc(rhythm.day.body)}</p>`
$('[data-rhythm="night"]').innerHTML = `<h3>${esc(rhythm.night.title)}</h3><p class="rhythm__time">${esc(hours.night.time)}</p><p>${esc(rhythm.night.body)}</p>
  <a class="btn btn--yellow" href="/evenings/">See the evenings</a>`

const roomsOn = (id) => rooms.filter((r) => r.floor === id).map((r) => r.name)
$('.floors').innerHTML = [...floors]
  .sort((a, b) => b.level - a.level)
  .map(
    (f) => `
  <li class="floor-row" style="--paint:${f.paint};--ink:${f.ink}">
    <b class="floor-row__name">${esc(f.name)}</b>
    <span class="floor-row__level">${esc(f.floor)} <span lang="kn">${esc(f.floorKn)}</span></span>
    <span class="floor-row__rooms">${roomsOn(f.id).map(esc).join(' · ')}</span>
  </li>`,
  )
  .join('')

renderTiers($('.tiers__row'), { compact: true })
wireBooking()

// The hero shows the connected house from above; the walk lives on /house/.
if (use3D) {
  const state = { journey: 0, assemble: 0, hero: 0, stop: 0, hour: 8, hidden: false }
  const hero = $('.hero')
  const sync = () => (state.hidden = hero.getBoundingClientRect().bottom < 0)
  addEventListener('scroll', sync, { passive: true })
  sync()
  import('../scene.js').then(({ startScene }) => startScene($('#scene'), state, floors, rooms))
}
