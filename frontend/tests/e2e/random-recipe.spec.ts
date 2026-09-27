import { expect, test } from './fixtures'

test('draws a random recipe, can reroll, and can add it to the planner', async ({ page }) => {
  const suffix = Date.now()
  const username = `random-${suffix}`
  const recipeTitle = `Soupe de saison ${suffix}`
  const ingredientName = `potiron-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  await page.getByRole('link', { name: 'Nouvelle recette' }).click()
  await page.getByLabel('Titre').fill(recipeTitle)
  await page.getByPlaceholder('Rechercher un ingrédient...').fill(ingredientName)
  await page.getByText(`+ Créer « ${ingredientName} »`).click()
  await page.getByRole('button', { name: "Créer l'ingrédient" }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.locator('input[id^="quantity-"]').fill('300')
  await page.getByLabel('Étape 1').fill('Mixer le potiron avec le bouillon.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await page.waitForURL(/\/recipes\/\d+$/)

  await page.goto('/recipes/random')
  await expect(page.locator('h1')).toHaveText('Recette au hasard')
  await expect(page.locator('h2').first()).toBeVisible()

  await page.getByRole('button', { name: 'Une autre' }).click()
  await expect(page.locator('h2').first()).toBeVisible()

  const today = new Date().toISOString().slice(0, 10)
  await page.locator('input[type="date"]').fill(today)
  await page.getByRole('button', { name: 'Ajouter' }).click()
  await expect(page.getByText("Ajoutée à l'agenda.")).toBeVisible()
})
