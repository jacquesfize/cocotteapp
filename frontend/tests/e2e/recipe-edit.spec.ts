import { expect, test } from '@playwright/test'

test('editing a recipe pre-fills every ingredient picker, not just the last one', async ({ page }) => {
  const suffix = Date.now()
  const username = `e2e-edit-${suffix}`
  const recipeTitle = `Velouté ${suffix}`
  const ingredientA = `poireau-${suffix}`
  const ingredientB = `creme-fraiche-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  await page.goto('/recipes/new')
  await page.getByLabel('Titre').fill(recipeTitle)
  await page.getByPlaceholder('Rechercher un ingrédient...').fill(ingredientA)
  await page.getByText(`+ Créer « ${ingredientA} »`).click()
  await page.getByRole('button', { name: "Créer l'ingrédient" }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.locator('input[type="number"][step="0.01"]').fill('2')
  await page.getByRole('button', { name: 'Ajouter un ingrédient' }).click()
  await page.getByPlaceholder('Rechercher un ingrédient...').nth(1).fill(ingredientB)
  await page.getByText(`+ Créer « ${ingredientB} »`).click()
  await page.getByRole('button', { name: "Créer l'ingrédient" }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.locator('input[type="number"][step="0.01"]').nth(1).fill('100')
  await page.getByLabel('Étape 1').fill('Éplucher les légumes.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await page.waitForURL(/\/recipes\/\d+$/)

  await page.getByRole('button', { name: 'Actions' }).click()
  await page.getByRole('link', { name: 'Modifier' }).click()
  await page.waitForURL(/\/recipes\/\d+\/edit$/)

  const ingredientInputs = page.getByPlaceholder('Rechercher un ingrédient...')
  await expect(ingredientInputs.nth(0)).toHaveValue(ingredientA)
  await expect(ingredientInputs.nth(1)).toHaveValue(ingredientB)
})
