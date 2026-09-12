import { expect, test } from '@playwright/test'

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
