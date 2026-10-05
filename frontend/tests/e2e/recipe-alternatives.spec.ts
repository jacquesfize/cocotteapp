import { expect, test } from './fixtures'
import { addNewIngredient } from './recipe-form'

test('an ingredient alternative added in the form can be swapped in on the recipe page', async ({ page }) => {
  const suffix = Date.now()
  const username = `e2e-alternatives-${suffix}`
  const milk = `lait-${suffix}`
  const oatMilk = `lait-avoine-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.locator('#health_data_consent').check()
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  await page.goto('/recipes/new')
  await page.getByLabel('Titre').fill(`Pancakes ${suffix}`)
  await addNewIngredient(page, milk, '250')

  // Ouvre la ligne pour lui ajouter une alternative végane, avec un ingrédient créé à la volée.
  await page.getByRole('button', { name: `Modifier ${milk}` }).click()
  const dialog = page.getByRole('dialog', { name: "Modifier l'ingrédient" })
  await dialog.getByRole('button', { name: 'Ajouter une alternative' }).click()
  await dialog.locator('#row-modal-alt-ingredient-0').fill(oatMilk)
  await page.getByText(`+ Créer « ${oatMilk} »`).click()
  await page.getByRole('button', { name: "Créer l'ingrédient" }).click()
  await expect(page.getByRole('button', { name: "Créer l'ingrédient" })).toBeHidden()
  await dialog.locator('#row-modal-alt-note-0').fill('Marche aussi avec du soja.')
  await dialog.getByRole('button', { name: 'Enregistrer', exact: true }).click()
  await expect(dialog).toBeHidden()
  await expect(page.locator('.ingredient-item')).toContainText('1 alternative')

  await page.getByLabel('Étape 1').fill('Mélanger.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await page.waitForURL(/\/recipes\/\d+$/)

  const line = page.locator('li.ingredient-row').filter({ hasText: milk })
  await expect(line.locator('.swap-chip')).toHaveText('1')
  await line.locator('.swap-chip').click()
  await line.getByRole('button', { name: new RegExp(oatMilk) }).click()
  await expect(line.locator('.ingredient-name')).toHaveText(oatMilk)
  await expect(line).toHaveClass(/swapped/)

  // Revenir à l'original en cliquant sur la ligne barrée.
  await line.locator('.swap-reset').click()
  await expect(line.locator('.ingredient-name')).toHaveText(milk)
  await expect(line).not.toHaveClass(/swapped/)

  // L'alternative est bien enregistrée : elle réapparaît à la réouverture du formulaire.
  await page.getByRole('button', { name: 'Actions' }).click()
  await page.getByRole('link', { name: 'Modifier' }).click()
  await page.waitForURL(/\/recipes\/\d+\/edit$/)
  await expect(page.locator('.ingredient-item')).toContainText('1 alternative')
})
