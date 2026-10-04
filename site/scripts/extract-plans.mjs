// Rasterises plans/HSR-plans-Model.pdf (needs poppler's pdftoppm) and crops
// each floor into public/plans/<floor>.png for use as WebGL textures.
import { execFileSync } from 'node:child_process'
import { mkdtempSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import sharp from 'sharp'

const PDF = new URL('../../plans/HSR-plans-Model.pdf', import.meta.url).pathname
const OUT = new URL('../public/plans/', import.meta.url).pathname
const DPI = 300

// Regions as fractions of the page (x0, y0, x1, y1), each wide enough to
// hold one plan; whitespace is trimmed afterwards.
const FLOORS = {
  basement: [0.10, 0.08, 0.47, 0.445],
  ground: [0.53, 0.06, 0.96, 0.535],
  first: [0.04, 0.55, 0.47, 0.925],
  second: [0.61, 0.60, 0.96, 0.925],
}

const dir = mkdtempSync(join(process.env.TMPDIR || tmpdir(), 'plans-'))
execFileSync('pdftoppm', ['-r', String(DPI), '-png', '-singlefile', PDF, join(dir, 'page')])
const page = join(dir, 'page.png')
const { width, height } = await sharp(page).metadata()

for (const [name, [x0, y0, x1, y1]] of Object.entries(FLOORS)) {
  const region = {
    left: Math.round(x0 * width),
    top: Math.round(y0 * height),
    width: Math.round((x1 - x0) * width),
    height: Math.round((y1 - y0) * height),
  }
  const cropped = await sharp(page).extract(region).toBuffer()
  const trimmed = await sharp(cropped).trim({ threshold: 20 }).toBuffer()
  const out = sharp(trimmed)
    .extend({ top: 24, bottom: 24, left: 24, right: 24, background: '#ffffff' })
    .resize({ width: 2048, height: 2048, fit: 'inside' })
    .flatten({ background: '#ffffff' })
  const info = await out.png({ compressionLevel: 9, palette: true, colors: 32 }).toFile(join(OUT, `${name}.png`))
  console.log(name, info.width, 'x', info.height)
}
