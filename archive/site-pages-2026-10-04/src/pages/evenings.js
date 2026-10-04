import { $, esc, chips, wireBooking, draftNote } from '../shell.js'
import { evenings, rhythm, hours } from '../content.js'

$('.programme__intro').textContent = rhythm.night.body
$('.programme__hours').textContent = `${hours.night.label} · ${hours.night.time}`
$('.programme__rows').innerHTML = evenings
  .map(
    (e) => `
  <li class="slot">
    <span class="slot__time">${esc(e.time)}</span>
    <div class="slot__what">
      <h3>${esc(e.name)}</h3>
      <p>${esc(e.body)}</p>
    </div>
    <span class="slot__where">${esc(e.where)}</span>
    <span class="slot__who">${chips(e.access)}</span>
  </li>`,
  )
  .join('')
$('.programme__title').insertAdjacentHTML('afterend', draftNote('Sample programme. Formats, times and nights are still being planned.'))
wireBooking()
