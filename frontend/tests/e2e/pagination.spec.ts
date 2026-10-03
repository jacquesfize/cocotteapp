import { expect, test } from './fixtures'

test('paginates the recipe list once there are more than one page of results', async ({ page }) => {
  const suffix = Date.now()
  const username = `page-${suffix}`
  const titlePrefix = `Pagination-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.locator('#health_data_consent').check()
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  const accessToken = await page.evaluate(() => localStorage.getItem('access_token'))

  // 11 recipes share a unique searchable prefix, isolating this test from any other
  // recipe already sitting in the (shared, never-reset) dev database.
  for (let i = 1; i <= 11; i += 1) {
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

  // Recipes are listed newest first, 10 per page by default, so the last one created (11)
  // is on page 1 and the first one created (01) ends up alone on page 2.
  await expect(page.getByText(`${titlePrefix} 11`)).toBeVisible()
  await expect(page.locator('.recipe-card')).toHaveCount(10)
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
  await expect(page.locator('.recipe-card')).toHaveCount(10)

  // Changing a filter resets back to page 1.
  await nextButton.click()
  await expect(page).toHaveURL(/[?&]page=2/)
  // Desktop : les filtres sont toujours visibles dans la colonne de gauche.
  await page.getByRole('radio', { name: 'Végan' }).check()
  await expect(page).not.toHaveURL(/[?&]page=2/)
})

test('lets the user change the number of recipes per page', async ({ page }) => {
  const suffix = Date.now()
  const username = `page-size-${suffix}`
  const titlePrefix = `PageSize-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.locator('#health_data_consent').check()
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  const accessToken = await page.evaluate(() => localStorage.getItem('access_token'))
  for (let i = 1; i <= 11; i += 1) {
    const response = await page.request.post('/api/recipes/', {
      headers: { Authorization: `Bearer ${accessToken}` },
      data: { title: `${titlePrefix} ${String(i).padStart(2, '0')}`, servings: 1 },
    })
    expect(response.ok()).toBe(true)
  }

  await page.goto(`/recipes?search=${titlePrefix}&page=2`)
  await expect(page.locator('.recipe-card')).toHaveCount(1)

  // Switching to 20 per page goes back to page 1, which now holds every result.
  await page.getByLabel('Recettes par page').selectOption('20')
  await expect(page).toHaveURL(/[?&]page_size=20/)
  await expect(page).not.toHaveURL(/[?&]page=2/)
  await expect(page.locator('.recipe-card')).toHaveCount(11)
  await expect(page.getByText('Page 1 / 2')).toBeHidden()

  // The choice is remembered on the next visit.
  await page.goto(`/recipes?search=${titlePrefix}`)
  await expect(page.locator('.recipe-card')).toHaveCount(11)
  await expect(page).toHaveURL(/[?&]page_size=20/)
})
