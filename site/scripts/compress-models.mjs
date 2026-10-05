// After `vite build`: meshopt-compress the glTFs the page loads, in dist/ only.
// public/models/baked/ stays as the bake writes it. Textures are untouched.
import { readdirSync, statSync, rmSync } from 'node:fs'
import { join, dirname } from 'node:path'
import { NodeIO, Logger } from '@gltf-transform/core'
import { ALL_EXTENSIONS } from '@gltf-transform/extensions'
import { dedup, quantize, reorder, meshopt } from '@gltf-transform/functions'
import { MeshoptEncoder } from 'meshoptimizer'

await MeshoptEncoder.ready
const io = new NodeIO().setLogger(new Logger(Logger.Verbosity.ERROR)).registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.encoder': MeshoptEncoder })

function nest(doc) {
  const scene = doc.getRoot().getDefaultScene()
  for (const node of scene.listChildren()) {
    const top = doc.createNode(node.getName()).setTranslation(node.getTranslation()).setRotation(node.getRotation()).setScale(node.getScale())
    node.setName(node.getName() + '-mesh').setTranslation([0, 0, 0]).setRotation([0, 0, 0, 1]).setScale([1, 1, 1])
    scene.removeChild(node)
    top.addChild(node)
    scene.addChild(top)
  }
}

const dirs = ['dist/models/baked', 'dist/models/props']
const size = (f) => statSync(f).size
let before = 0
let after = 0
for (const dir of dirs) {
  for (const name of readdirSync(dir).filter((f) => f.endsWith('.gltf'))) {
    const file = join(dir, name)
    const doc = await io.read(file)
    const bins = doc.getRoot().listBuffers().map((b) => join(dirname(file), b.getURI()))
    const b0 = size(file) + bins.reduce((a, f) => a + size(f), 0)
    await doc.transform(
      dedup(),
      reorder({ encoder: MeshoptEncoder }),
      // Quantizing puts a dequantizing scale and offset on the mesh's node; the
      // scene places each prop by resetting its top node (scene.js, loadProps),
      // so the props get a parent that keeps the layout and leaves that to the child.
      ...(dir.endsWith('props') ? [nest] : []),
      // The baked atlases need exact UVs: keep texcoords at 16 bits.
      quantize({ quantizePosition: 14, quantizeTexcoord: 16, quantizeNormal: 10 }),
      meshopt({ encoder: MeshoptEncoder, level: 'medium' }),
    )
    for (const f of bins) rmSync(f)
    await io.write(file, doc)
    const out = doc.getRoot().listBuffers().map((b) => join(dirname(file), b.getURI()))
    const b1 = size(file) + out.reduce((a, f) => a + size(f), 0)
    before += b0
    after += b1
    console.log(`${name.padEnd(28)} ${(b0 / 1024).toFixed(0).padStart(6)} kB → ${(b1 / 1024).toFixed(0).padStart(6)} kB`)
  }
}
console.log(`geometry ${(before / 1048576).toFixed(1)} MB → ${(after / 1048576).toFixed(1)} MB`)
