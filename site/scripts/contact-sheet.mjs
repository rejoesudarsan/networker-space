import sharp from 'sharp'
const d = '/Users/rejoesudarsan/Dev/networker-space/tmp/'
const names = process.argv[2].split(',')
const W = 720, H = 405, cols = 3
const tiles = []
for (const [i, n] of names.entries()) {
  tiles.push({ input: await sharp(d + 'beat-' + n + '.png').resize(W, H).toBuffer(), left: (i % cols) * W, top: Math.floor(i / cols) * H })
  tiles.push({ input: Buffer.from(`<svg width="140" height="26"><rect width="140" height="26" fill="black"/><text x="6" y="18" font-size="15" fill="white" font-family="monospace">${n}</text></svg>`), left: (i % cols) * W, top: Math.floor(i / cols) * H })
}
await sharp({ create: { width: W * cols, height: H * Math.ceil(names.length / cols), channels: 3, background: '#fff' } }).composite(tiles).jpeg({ quality: 85 }).toFile(d + process.argv[3])
