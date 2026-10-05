import { expect, test } from './fixtures'
import { addNewIngredient } from './recipe-form'

test('homepage shows the intro and the recipe just created', async ({ page }) => {
  const suffix = Date.now()
  const username = `home-${suffix}`
  const recipeTitle = `Poêlée de saison ${suffix}`
  const ingredientName = `panais-${suffix}`

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
  await page.getByLabel('Étape 1').fill('Faire revenir à la poêle.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await page.waitForURL(/\/recipes\/\d+$/)

  await page.getByRole('link', { name: 'Accueil' }).click()
  await expect(page).toHaveURL('/')

  await expect(page.getByRole('button', { name: 'Nouvelle recette' })).toBeVisible()
  await expect(page.getByRole('link', { name: new RegExp(recipeTitle) })).toBeVisible()

  await page.getByRole('link', { name: new RegExp(recipeTitle) }).click()
  await expect(page.locator('h1')).toHaveText(recipeTitle)
})
