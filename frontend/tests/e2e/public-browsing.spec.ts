import { expect, test } from './fixtures'
import { addNewIngredient } from './recipe-form'

test('anonymous visitors can browse the homepage, the recipe list and a recipe page, but cannot manage it or reach account-only pages', async ({
  page,
}) => {
  const suffix = Date.now()
  const username = `pub-${suffix}`
  const recipeTitle = `Poêlée anonyme ${suffix}`
  const ingredientName = `panais-${suffix}`

  // Create a recipe while logged in, then log out to browse as an anonymous visitor.
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
  await addNewIngredient(page, ingredientName, '150')
  await page.getByLabel('Étape 1').fill('Faire revenir.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await page.waitForURL(/\/recipes\/\d+$/)
  const recipeUrl = page.url()

  await page.evaluate(() => localStorage.clear())

  // Homepage, without login.
  await page.goto('/')
  await expect(page).toHaveURL('/')
  await expect(page.getByRole('button', { name: 'Nouvelle recette' })).toHaveCount(0)
  await expect(page.getByRole('link', { name: 'Connexion' })).toBeVisible()

  // Recipe list, without login: browsable, but the write-only actions are hidden.
  await page.goto('/recipes')
  await expect(page).toHaveURL('/recipes')
  await expect(page.getByRole('link', { name: new RegExp(recipeTitle) })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Nouvelle recette' })).toHaveCount(0)
  await expect(page.getByLabel(/Importer depuis une URL/)).toHaveCount(0)

  // Recipe detail, without login: viewable, but not editable, and no "add to planner" form.
  await page.goto(recipeUrl)
  await expect(page.locator('h1')).toHaveText(recipeTitle)
  await expect(page.getByRole('button', { name: 'Modifier' })).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Supprimer' })).toHaveCount(0)
  await expect(page.getByRole('heading', { name: "Ajouter à l'agenda" })).toHaveCount(0)

  // Random recipe page, without login.
  await page.goto('/recipes/random')
  await expect(page).toHaveURL('/recipes/random')

  // Account-only pages still require login.
  await page.goto('/planning')
  await expect(page).toHaveURL(/\/login\?redirect=\/planning/)
  await page.goto('/shopping-lists')
  await expect(page).toHaveURL(/\/login\?redirect=\/shopping-lists/)
  await page.goto('/recipes/new')
  await expect(page).toHaveURL(/\/login\?redirect=\/recipes\/new/)
})
