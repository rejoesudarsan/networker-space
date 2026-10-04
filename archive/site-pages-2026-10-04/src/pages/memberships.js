import { $, renderTiers, renderMatrix, wireBooking, draftNote } from '../shell.js'

$('.section-head').insertAdjacentHTML('beforeend', draftNote('Draft terms: memberships, minimums and booking windows are still being finalised.'))
renderTiers($('.tiers__row'))
renderMatrix($('.matrix table'))
wireBooking()
