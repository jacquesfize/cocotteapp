import { expect, test } from './fixtures'
import { addNewIngredient } from './recipe-form'

test('editing a recipe lists every ingredient it was saved with, not just the last one', async ({ page }) => {
  const suffix = Date.now()
  const username = `e2e-edit-${suffix}`
  const recipeTitle = `Velouté ${suffix}`
  const ingredientA = `poireau-${suffix}`
  const ingredientB = `creme-fraiche-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.locator('#health_data_consent').check()
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  await page.goto('/recipes/new')
  await page.getByLabel('Titre').fill(recipeTitle)
  await addNewIngredient(page, ingredientA, '2')
  await addNewIngredient(page, ingredientB, '100')
  await page.getByLabel('Étape 1').fill('Éplucher les légumes.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await page.waitForURL(/\/recipes\/\d+$/)

  await page.getByRole('button', { name: 'Actions' }).click()
  await page.getByRole('link', { name: 'Modifier' }).click()
  await page.waitForURL(/\/recipes\/\d+\/edit$/)

  const items = page.locator('.ingredient-item')
  await expect(items).toHaveCount(2)
  await expect(items.nth(0)).toContainText(ingredientA)
  await expect(items.nth(0)).toContainText('2')
  await expect(items.nth(1)).toContainText(ingredientB)
  await expect(items.nth(1)).toContainText('100')
})
