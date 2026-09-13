import { expect, test } from '@playwright/test'

test('register, create a recipe, plan it and generate a shopping list', async ({ page }) => {
  const suffix = Date.now()
  const username = `e2e-${suffix}`
  const recipeTitle = `Curry de lentilles ${suffix}`
  const ingredientName = `lentilles-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()

  await expect(page).toHaveURL(/\/recipes$/)

  await page.getByRole('link', { name: 'Nouvelle recette' }).click()
  await page.getByLabel('Titre').fill(recipeTitle)
  await page.getByPlaceholder('Rechercher un ingrédient...').fill(ingredientName)
  await page.getByText(`+ Créer « ${ingredientName} »`).click()
  await page.locator('input[type="number"][step="0.01"]').fill('250')
  await page.getByLabel('Étape 1').fill('Faire revenir les épices puis ajouter les lentilles.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()

  await expect(page).toHaveURL(/\/recipes\/\d+$/)
  await expect(page.locator('h1')).toHaveText(recipeTitle)
  await expect(page.getByText(ingredientName)).toBeVisible()

  await page.getByRole('link', { name: 'Agenda' }).click()
  await expect(page.locator('.day-col').first()).toBeVisible()

  const dinnerSlot = page.locator('.day-col').first().locator('.meal-slot').filter({ hasText: 'Dîner' })
  await dinnerSlot.getByRole('button', { name: 'Ajouter un repas' }).click()
  await dinnerSlot.getByPlaceholder('Rechercher une recette...').fill(recipeTitle)
  await dinnerSlot.locator('.suggestions').getByText(recipeTitle).click()
  await dinnerSlot.getByRole('button', { name: 'Ajouter' }).click()

  await expect(dinnerSlot.getByText(recipeTitle)).toBeVisible()
  await page.getByRole('button', { name: /Générer la liste de courses/ }).click()

  await expect(page).toHaveURL(/\/shopping-lists\/\d+$/)
  await expect(page.getByText(ingredientName)).toBeVisible()

  const itemCheckbox = page.locator('.item-row input[type="checkbox"]').first()
  await itemCheckbox.check()
  await expect(page.locator('.owned')).toBeVisible()
})
