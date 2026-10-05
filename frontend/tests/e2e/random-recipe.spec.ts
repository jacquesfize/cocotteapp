import { expect, test } from './fixtures'
import { addNewIngredient } from './recipe-form'

test('rolls the dice to draw a random recipe, then rerolls', async ({ page }) => {
  const suffix = Date.now()
  const username = `random-${suffix}`
  const recipeTitle = `Soupe de saison ${suffix}`
  const ingredientName = `potiron-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.locator('#health_data_consent').check()
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  await page.getByRole('button', { name: 'Nouvelle recette' }).click()
  await page.getByRole('link', { name: 'Créer manuellement' }).click()
  await page.getByLabel('Titre').fill(recipeTitle)
  await addNewIngredient(page, ingredientName, '300')
  await page.getByLabel('Étape 1').fill('Mixer le potiron avec le bouillon.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await page.waitForURL(/\/recipes\/\d+$/)

  await page.goto('/recipes/random')
  await expect(page.locator('h1')).toHaveText('Recette au hasard')
  await expect(page.locator('.recipe-card')).toHaveCount(0)

  await page.getByRole('button', { name: 'Lancer le dé' }).click()
  await expect(page.locator('.recipe-card.feature h3')).toBeVisible()

  await page.getByRole('button', { name: 'Une autre' }).click()
  await expect(page.locator('.recipe-card.feature h3')).toBeVisible()
})
