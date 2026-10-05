import { expect, type Page } from '@playwright/test'

// Ajoute un ingrédient *inconnu* à la recette en cours de saisie : bouton « Ajouter un ingrédient »
// de la première section, création à la volée de l'ingrédient (seconde modale, par-dessus), puis
// quantité et validation de la modale de la ligne.
export async function addNewIngredient(page: Page, name: string, quantity: string) {
  await page.getByRole('button', { name: 'Ajouter un ingrédient' }).first().click()
  const dialog = page.getByRole('dialog', { name: 'Ajouter un ingrédient' })
  await dialog.getByPlaceholder('Rechercher un ingrédient...').fill(name)
  await page.getByText(`+ Créer « ${name} »`).click()
  await page.getByRole('button', { name: "Créer l'ingrédient" }).click()
  await expect(page.getByRole('button', { name: "Créer l'ingrédient" })).toBeHidden()
  await dialog.getByLabel('Quantité').fill(quantity)
  await dialog.getByRole('button', { name: 'Ajouter', exact: true }).click()
  await expect(dialog).toBeHidden()
}
