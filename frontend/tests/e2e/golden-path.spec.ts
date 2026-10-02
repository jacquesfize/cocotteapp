import { expect, test } from './fixtures'

test('register, create a recipe, plan it and generate a shopping list', async ({ page }) => {
  const suffix = Date.now()
  const username = `e2e-${suffix}`
  const recipeTitle = `Curry de lentilles ${suffix}`
  const ingredientName = `lentilles-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.locator('#health_data_consent').check()
  await page.getByRole('button', { name: 'Créer mon compte' }).click()

  await expect(page).toHaveURL(/\/recipes$/)

  // L'import depuis une URL reste replié par défaut (gain de place sur mobile) et
  // s'ouvre au clic sur le bouton "Importer" à côté de "Nouvelle recette".
  const importToggle = page.locator('.page-header').getByRole('button', { name: 'Importer' })
  await expect(page.getByLabel(/Importer depuis une URL/)).toHaveCount(0)
  await importToggle.click()
  await expect(page.getByLabel(/Importer depuis une URL/)).toBeVisible()
  await importToggle.click()
  await expect(page.getByLabel(/Importer depuis une URL/)).toHaveCount(0)

  await page.getByRole('link', { name: 'Nouvelle recette' }).click()
  await page.getByLabel('Titre').fill(recipeTitle)
  await page.getByPlaceholder('Rechercher un ingrédient...').fill(ingredientName)
  await page.getByText(`+ Créer « ${ingredientName} »`).click()
  await page.getByRole('button', { name: "Créer l'ingrédient" }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.locator('input[id^="quantity-"]').fill('250')
  await page.getByLabel('Étape 1').fill('Faire revenir les épices puis ajouter les lentilles.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()

  await expect(page).toHaveURL(/\/recipes\/\d+$/)
  await expect(page.locator('h1')).toHaveText(recipeTitle)
  await expect(page.getByText(ingredientName)).toBeVisible()

  await page.getByRole('link', { name: 'Agenda' }).click()
  await expect(page.locator('.agenda-week')).toBeVisible()

  const dinnerSlot = page.locator('.agenda-cell[data-meal-type="dinner"]').first()
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
