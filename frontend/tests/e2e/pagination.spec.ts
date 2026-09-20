import { expect, test } from '@playwright/test'

test('paginates the recipe list once there are more than one page of results', async ({ page }) => {
  const suffix = Date.now()
  const username = `page-${suffix}`
  const titlePrefix = `Pagination-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  const accessToken = await page.evaluate(() => localStorage.getItem('access_token'))

  // 21 recipes share a unique searchable prefix, isolating this test from any other
  // recipe already sitting in the (shared, never-reset) dev database.
  for (let i = 1; i <= 21; i += 1) {
    const response = await page.request.post('/api/recipes/', {
      headers: { Authorization: `Bearer ${accessToken}` },
      data: {
        title: `${titlePrefix} ${String(i).padStart(2, '0')}`,
        servings: 1,
        prep_time_minutes: 5,
        cook_time_minutes: 5,
      },
    })
    expect(response.ok()).toBe(true)
  }

  await page.goto(`/recipes?search=${titlePrefix}`)

  // Recipes are listed newest first, so the last one created (21) is on page 1
  // and the first one created (01) ends up alone on page 2.
  await expect(page.getByText(`${titlePrefix} 21`)).toBeVisible()
  await expect(page.locator('.recipe-card')).toHaveCount(20)
  await expect(page.getByText('Page 1 / 2')).toBeVisible()
  const previousButton = page.getByRole('button', { name: 'Page précédente' })
  const nextButton = page.getByRole('button', { name: 'Page suivante' })
  await expect(previousButton).toBeDisabled()
  await expect(nextButton).toBeEnabled()

  await nextButton.click()
  await expect(page).toHaveURL(/[?&]page=2/)
  await expect(page.locator('.recipe-card')).toHaveCount(1)
  await expect(page.getByText(`${titlePrefix} 01`)).toBeVisible()
  await expect(page.getByText('Page 2 / 2')).toBeVisible()
  await expect(nextButton).toBeDisabled()
  await expect(previousButton).toBeEnabled()

  await previousButton.click()
  await expect(page).not.toHaveURL(/[?&]page=2/)
  await expect(page.locator('.recipe-card')).toHaveCount(20)

  // Changing a filter resets back to page 1.
  await nextButton.click()
  await expect(page).toHaveURL(/[?&]page=2/)
  await page.getByRole('button', { name: /Filtres/ }).click()
  await page.getByLabel('Régime').selectOption('vegan')
  await expect(page).not.toHaveURL(/[?&]page=2/)
})
