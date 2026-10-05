// After the compress steps: the buffers and textures the glTFs point at move to
// content-hashed names in dist/models/immutable/, so they can be cached for a
// year (public/_headers); the small .gltf files keep their names and revalidate.
import { readdirSync, readFileSync, writeFileSync, renameSync, mkdirSync, existsSync } from 'node:fs'
import { join, dirname, basename, extname, relative } from 'node:path'
import { createHash } from 'node:crypto'

const out = 'dist/models/immutable'
mkdirSync(out, { recursive: true })
const moved = new Map()
let n = 0
function hashed(file) {
  if (moved.has(file)) return moved.get(file)
  const ext = extname(file)
  const stem = basename(file, ext)
  const h = createHash('sha256').update(readFileSync(file)).digest('hex').slice(0, 10)
  const dest = join(out, `${stem}.${h}${ext}`)
  renameSync(file, dest)
  // The WebP tiers made from a JPEG follow it (scripts/compress-textures.mjs).
  if (ext === '.jpg') {
    for (const tier of ['.webp', '-sm.webp']) {
      const src = file.slice(0, -4) + tier
      if (existsSync(src)) renameSync(src, join(out, `${stem}.${h}${tier}`))
    }
  }
  moved.set(file, dest)
  n++
  return dest
}
for (const dir of ['dist/models/baked', 'dist/models/props']) {
  for (const name of readdirSync(dir).filter((f) => f.endsWith('.gltf'))) {
    const file = join(dir, name)
    const gltf = JSON.parse(readFileSync(file, 'utf8'))
    for (const item of [...(gltf.buffers || []), ...(gltf.images || [])]) {
      if (!item.uri || item.uri.startsWith('data:')) continue
      item.uri = relative(dirname(file), hashed(join(dirname(file), decodeURI(item.uri))))
    }
    writeFileSync(file, JSON.stringify(gltf))
  }
}
console.log(`hashed ${n} model files into ${out}`)
