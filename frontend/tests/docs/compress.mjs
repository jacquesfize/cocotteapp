// Compresse (avec perte, visuellement neutre) les captures de docs/assets/screenshots/ via
// pngquant, lancé par `npm run docs:screenshots` après Playwright. pngquant-bin est récupéré à la
// volée par npx (pas de dépendance ajoutée au projet).
import { spawnSync } from 'node:child_process'
import { readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

const dir = fileURLToPath(new URL('../../../docs/assets/screenshots/', import.meta.url))
const files = readdirSync(dir)
  .filter((name) => name.endsWith('.png'))
  .map((name) => join(dir, name))

const totalSize = () => files.reduce((sum, file) => sum + statSync(file).size, 0)
const mb = (bytes) => `${(bytes / 1024 / 1024).toFixed(1)} MB`

if (!files.length) {
  console.log('No screenshot to compress.')
  process.exit(0)
}

const before = totalSize()
const result = spawnSync(
  'npx',
  [
    '--yes',
    'pngquant-bin',
    '--quality=70-90',
    '--speed',
    '1',
    '--skip-if-larger',
    '--strip',
    '--force',
    '--ext',
    '.png',
    ...files,
  ],
  { stdio: 'inherit' },
)
// 98 / 99 : image laissée telle quelle (compression inutile ou qualité non atteinte).
if (result.error || ![0, 98, 99].includes(result.status)) {
  console.error('pngquant failed', result.error ?? `exit code ${result.status}`)
  process.exit(1)
}
console.log(`Compressed ${files.length} screenshots: ${mb(before)} -> ${mb(totalSize())}`)
