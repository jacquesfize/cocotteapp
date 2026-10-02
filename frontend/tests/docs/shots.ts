import { fileURLToPath } from 'node:url'
import type { Locator, Page } from '@playwright/test'

// Helpers de capture pour la documentation : attente d'un rendu stable puis enregistrement
// dans docs/assets/screenshots/<name>.png.

export const SCREENSHOT_DIR = fileURLToPath(new URL('../../../docs/assets/screenshots/', import.meta.url))

// SHOTS=register,account-data : ne régénère que ces captures (les autres fichiers ne sont pas
// touchés, ce qui évite de réécrire — et de re-stocker dans Git LFS — des images inchangées).
// Non défini : toutes les captures. Les scénarios tournent quand même en entier.
const ONLY = process.env.SHOTS?.split(',').map((name) => name.trim()).filter(Boolean)
const wanted = (name: string) => !ONLY || ONLY.includes(name)

const OPTIONS = { animations: 'disabled', caret: 'hide' } as const

export async function settle(page: Page) {
  await page.waitForLoadState('networkidle', { timeout: 10_000 }).catch(() => {})
  await page
    .waitForFunction(() => Array.from(document.images).every((img) => img.complete), undefined, { timeout: 10_000 })
    .catch(() => {})
  await page.evaluate(() => document.fonts.ready)
  // Aucun indicateur de chargement ne doit rester visible.
  await page
    .locator('text=Loading...')
    .first()
    .waitFor({ state: 'hidden', timeout: 10_000 })
    .catch(() => {})
  await page.waitForTimeout(300)
}

export async function shotPage(page: Page, name: string, options: { fullPage?: boolean } = {}) {
  if (!wanted(name)) return
  await settle(page)
  await page.screenshot({ ...OPTIONS, path: `${SCREENSHOT_DIR}${name}.png`, fullPage: options.fullPage ?? false })
}

export async function shotElement(locator: Locator, name: string) {
  if (!wanted(name)) return
  await settle(locator.page())
  await locator.screenshot({ ...OPTIONS, path: `${SCREENSHOT_DIR}${name}.png` })
}

/** Capture la zone englobant plusieurs éléments (ex. un bouton et son menu déroulant). */
export async function shotAround(page: Page, locators: Locator[], name: string, padding = 16) {
  if (!wanted(name)) return
  await settle(page)
  const boxes = []
  for (const locator of locators) {
    await locator.scrollIntoViewIfNeeded()
  }
  for (const locator of locators) {
    const box = await locator.boundingBox()
    if (box) boxes.push(box)
  }
  if (!boxes.length) throw new Error(`Nothing to capture for ${name}`)
  // boundingBox() est relatif au viewport : on passe en coordonnées de page pour pouvoir
  // capturer une zone plus haute que l'écran (fullPage + clip).
  const { scrollX, scrollY, pageWidth, pageHeight } = await page.evaluate(() => ({
    scrollX: window.scrollX,
    scrollY: window.scrollY,
    pageWidth: document.documentElement.scrollWidth,
    pageHeight: document.documentElement.scrollHeight,
  }))
  const x = Math.max(0, Math.min(...boxes.map((b) => b.x)) + scrollX - padding)
  const y = Math.max(0, Math.min(...boxes.map((b) => b.y)) + scrollY - padding)
  const right = Math.min(pageWidth, Math.max(...boxes.map((b) => b.x + b.width)) + scrollX + padding)
  const bottom = Math.min(pageHeight, Math.max(...boxes.map((b) => b.y + b.height)) + scrollY + padding)
  await page.screenshot({
    ...OPTIONS,
    path: `${SCREENSHOT_DIR}${name}.png`,
    fullPage: true,
    clip: { x, y, width: right - x, height: bottom - y },
  })
}

export async function loginWithTokens(page: Page, access: string, refresh: string, path = '/') {
  await page.evaluate(
    ({ access, refresh }) => {
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)
    },
    { access, refresh },
  )
  await page.goto(path)
}
