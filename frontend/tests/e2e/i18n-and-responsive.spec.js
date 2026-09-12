import { expect, test } from '@playwright/test'

test('shows a burger menu on mobile that opens, closes on navigation, and stays hidden on desktop', async ({
  page,
}) => {
  const suffix = Date.now()
  const username = `nav-${suffix}`

  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  const panel = page.locator('#nav-panel')
  await expect(panel).not.toHaveClass(/is-open/)
  await expect(page.getByRole('link', { name: 'Agenda' })).toBeHidden()

  await page.locator('button.burger').click()
  await expect(panel).toHaveClass(/is-open/)
  await expect(page.getByRole('link', { name: 'Agenda' })).toBeVisible()

  await page.getByRole('link', { name: 'Agenda' }).click()
  await expect(page).toHaveURL(/\/planning$/)
  await expect(panel).not.toHaveClass(/is-open/)

  await page.setViewportSize({ width: 1280, height: 800 })
  await expect(page.locator('button.burger')).toBeHidden()
  await expect(page.getByRole('link', { name: 'Agenda' })).toBeVisible()
})

test('switches language and persists the choice across reloads', async ({ page }) => {
  await page.goto('/login')
  await expect(page.locator('h1')).toHaveText('Connexion')

  await page.locator('select.locale-select').selectOption('en')
  await expect(page.locator('h1')).toHaveText('Log in')

  await page.reload()
  await expect(page.locator('h1')).toHaveText('Log in')
})

test('renders the login and register pages without horizontal overflow on a phone viewport', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 })

  await page.goto('/login')
  let hasOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  )
  expect(hasOverflow).toBe(false)

  await page.goto('/register')
  hasOverflow = await page.evaluate(
    () => document.documentElement.scrollWidth > document.documentElement.clientWidth,
  )
  expect(hasOverflow).toBe(false)
})
