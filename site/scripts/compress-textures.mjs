// After `vite build`: next to every JPEG texture in dist/models, a WebP at full
// size and a half-size `-sm.webp` for phones. The JPEGs stay as the fallback;
// the loader picks (src/space/scene.js, `textureUrl`). public/ is untouched.
import { readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import sharp from 'sharp'

const dirs = ['dist/models/baked', 'dist/models/props/textures']
const kb = (n) => (n / 1024).toFixed(0).padStart(5) + ' kB'
const sum = { jpg: 0, webp: 0, sm: 0 }
for (const dir of dirs) {
  for (const name of readdirSync(dir).filter((f) => f.endsWith('.jpg'))) {
    const file = join(dir, name)
    const base = file.slice(0, -4)
    const quality = 80
    const { width } = await sharp(file).metadata()
    await sharp(file).webp({ quality }).toFile(base + '.webp')
    await sharp(file).resize(Math.round(width / 2)).webp({ quality }).toFile(base + '-sm.webp')
    const [a, b, c] = [file, base + '.webp', base + '-sm.webp'].map((f) => statSync(f).size)
    sum.jpg += a
    sum.webp += b
    sum.sm += c
    console.log(`${name.padEnd(24)} ${kb(a)} → ${kb(b)} webp, ${kb(c)} phone`)
  }
}
console.log(`textures ${kb(sum.jpg)} jpg → ${kb(sum.webp)} webp, ${kb(sum.sm)} phone`)
