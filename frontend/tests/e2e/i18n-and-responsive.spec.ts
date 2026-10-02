import { expect, test, type Page } from './fixtures'

async function registerAndLogin(page: Page, username: string) {
  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.locator('#health_data_consent').check()
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)
}

test('shows a bottom tab bar on mobile, inline links on desktop, and an account menu with logout', async ({
  page,
}) => {
  const username = `nav-${Date.now()}`

  await page.setViewportSize({ width: 390, height: 844 })
  await registerAndLogin(page, username)

  const tabbar = page.locator('nav.tabbar')
  await expect(tabbar).toBeVisible()
  await expect(tabbar.getByRole('link', { name: 'Agenda' })).toBeVisible()
  await expect(page.locator('nav.top-links')).toBeHidden()

  await tabbar.getByRole('link', { name: 'Agenda' }).click()
  await expect(page).toHaveURL(/\/planning$/)

  const panel = page.locator('#account-panel')
  await expect(panel).not.toHaveClass(/is-open/)
  await page.locator('.account-button').click()
  await expect(panel).toHaveClass(/is-open/)
  await expect(panel.getByText(username)).toBeVisible()

  await page.mouse.click(5, 5)
  await expect(panel).not.toHaveClass(/is-open/)

  await page.setViewportSize({ width: 1280, height: 800 })
  await expect(page.locator('nav.tabbar')).toBeHidden()
  await expect(page.locator('nav.top-links').getByRole('link', { name: 'Agenda' })).toBeVisible()
})

test('switches language from the header locale button and persists the choice across reloads', async ({ page }) => {
  await page.goto('/login')
  await expect(page.locator('h1')).toHaveText('Connexion')

  await page.getByTestId('locale-button').click()
  await page.locator('.locale-option', { hasText: 'English' }).click()
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
