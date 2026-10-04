// Export panoramas created with Codex's built-in image generator; no API key needed.
// Source PNGs live in assets/env. To replace an asset, generate a new source there
// and run npm run env -- --force. This script exports images, not AI generation.
import { mkdir, access, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const ids = ['cafe', 'studio', 'courtyard', 'terrace', 'night'];
const force = process.argv.includes('--force');
const destination = new URL('../public/world/env/', import.meta.url);
await mkdir(destination, { recursive: true });

for (const id of ids) {
  const output = fileURLToPath(new URL(`${id}.jpg`, destination));
  let exists = false;
  try { await access(output); exists = true; }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  if (!exists || force) {
    const input = fileURLToPath(new URL(`../assets/env/${id}.png`, import.meta.url));
    await sharp(input).resize(2048, 1024, { fit: 'fill' }).jpeg({ quality: 82 }).toFile(output);
  }
  const metadata = await sharp(output).metadata();
  await sharp(output).raw().toBuffer(); // Decode the full image, not only its header.
  if (metadata.format !== 'jpeg' || metadata.width !== 2048 || metadata.height !== 1024) {
    throw new Error(`Invalid panorama: ${output}`);
  }
  const { size } = await stat(output);
  console.log(`${id}: ${exists && !force ? 'verified existing' : 'exported'} ${metadata.width}x${metadata.height}, ${size} bytes — ${output}`);
}
