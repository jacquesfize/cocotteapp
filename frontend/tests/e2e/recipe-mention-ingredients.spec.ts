import { expect, test } from './fixtures'
import { addNewIngredient } from './recipe-form'

test('mentioning an ingredient not yet in the recipe adds it automatically, and creating a brand new one works too', async ({
  page,
}) => {
  const suffix = Date.now()
  const username = `e2e-mentions-${suffix}`
  const existingElsewhere = `carotte-${suffix}`
  const brandNew = `panais-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.locator('#health_data_consent').check()
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  // Crée l'ingrédient "carotte" dans une AUTRE recette, pour qu'il existe en base sans
  // être dans la liste de la recette qu'on va tester ensuite.
  await page.goto('/recipes/new')
  await page.getByLabel('Titre').fill('Recette temporaire')
  await addNewIngredient(page, existingElsewhere, '1')
  await page.getByLabel('Étape 1').fill('x')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await page.waitForURL(/\/recipes\/\d+$/)

  await page.goto('/recipes/new')
  await page.getByLabel('Titre').fill('Velouté de légumes')
  await addNewIngredient(page, `poireau-${suffix}`, '2')

  const step1 = page.locator('#step-0')

  // Mentionner un ingrédient qui existe déjà en base (mais pas dans cette recette) doit
  // l'ajouter automatiquement à la liste, avec son unité par défaut.
  await step1.fill(`Ajouter le @${existingElsewhere}`)
  await page.locator('.cooklang-input .suggestions-dropdown li').first().waitFor()
  await page.locator('.cooklang-input .suggestions-dropdown li').first().click()

  const items = page.locator('.ingredient-item')
  await expect(items).toHaveCount(2)
  await expect(items.nth(1)).toContainText(existingElsewhere)
  await expect(step1).toHaveValue(new RegExp(`@${existingElsewhere} $`))

  // Mentionner un ingrédient qui n'existe nulle part propose de le créer ; une fois créé
  // via la modale, il est lui aussi ajouté automatiquement à la liste.
  // Le textarea est un composant contrôlé (re-rendu à chaque frappe pour la détection de
  // mention) : taper caractère par caractère (page.keyboard.type) peut aller plus vite que le
  // cycle emit -> parent -> re-bind et corrompre le texte. On ajoute donc la mention en un seul
  // .fill() atomique (un seul évènement "input"), comme pour la première mention plus haut.
  const textWithFirstMention = await step1.inputValue()
  await step1.fill(`${textWithFirstMention} puis @${brandNew}`)
  await page.locator('.cooklang-input .suggestions-dropdown li.create').waitFor()
  await page.locator('.cooklang-input .suggestions-dropdown li.create').click()

  await expect(page.getByRole('dialog')).toBeVisible()
  await expect(page.locator('#ingredient-modal-name')).toHaveValue(brandNew)
  await page.locator('#ingredient-modal-category').selectOption('vegetable')
  await page.getByRole('button', { name: "Créer l'ingrédient" }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  await expect(items).toHaveCount(3)
  await expect(items.nth(2)).toContainText(brandNew)
  await expect(page.locator('.mention-warning')).toHaveCount(0)
})
