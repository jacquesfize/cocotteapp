import { expect, test, type Page } from './fixtures'

async function registerAndBuildShoppingList(page: Page, suffix: number) {
  const username = `e2e-offline-${suffix}`
  const recipeTitle = `Curry hors ligne ${suffix}`
  const ingredientName = `epinards-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.locator('#health_data_consent').check()
  await page.getByRole('button', { name: 'Créer mon compte' }).click()

  await expect(page).toHaveURL(/\/recipes$/)

  await page.getByRole('link', { name: 'Nouvelle recette' }).click()
  await page.getByLabel('Titre').fill(recipeTitle)
  await page.getByPlaceholder('Rechercher un ingrédient...').fill(ingredientName)
  await page.getByText(`+ Créer « ${ingredientName} »`).click()
  await page.getByRole('button', { name: "Créer l'ingrédient" }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.locator('input[id^="quantity-"]').fill('200')
  await page.getByLabel('Étape 1').fill('Faire revenir les épinards.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()

  await expect(page).toHaveURL(/\/recipes\/\d+$/)
  const recipeUrl = page.url()

  await page.getByRole('link', { name: 'Agenda' }).click()
  const dinnerSlot = page.locator('.agenda-cell[data-meal-type="dinner"]').first()
  await dinnerSlot.getByRole('button', { name: 'Ajouter un repas' }).click()
  await dinnerSlot.getByPlaceholder('Rechercher une recette...').fill(recipeTitle)
  await dinnerSlot.locator('.suggestions').getByText(recipeTitle).click()
  await dinnerSlot.getByRole('button', { name: 'Ajouter' }).click()
  await expect(dinnerSlot.getByText(recipeTitle)).toBeVisible()

  await page.getByRole('button', { name: /Générer la liste de courses/ }).click()
  await expect(page).toHaveURL(/\/shopping-lists\/\d+$/)
  await expect(page.getByText(ingredientName)).toBeVisible()
  const shoppingListUrl = page.url()

  return { recipeTitle, recipeUrl, shoppingListUrl, ingredientName }
}

test.describe('PWA offline support', () => {
  // La PWA peut être désactivée (`disable: true` de VitePWA dans vite.config.ts) : dans ce cas
  // aucun service worker n'est enregistré et ces scénarios n'ont pas de sens.
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    const hasServiceWorker = await page.evaluate(async () => {
      for (let attempt = 0; attempt < 10; attempt++) {
        if ((await navigator.serviceWorker.getRegistrations()).length > 0) return true
        await new Promise((resolve) => setTimeout(resolve, 300))
      }
      return false
    })
    test.skip(!hasServiceWorker, 'PWA désactivée (VitePWA disable: true) : aucun service worker enregistré')
  })

  test('cached recipe and shopping list stay viewable when offline', async ({ page, context }) => {
    const suffix = Date.now()
    const { recipeTitle, ingredientName } = await registerAndBuildShoppingList(page, suffix)

    // Visite la page de liste des listes de courses (pas encore vue jusqu'ici) pour que
    // sa réponse GET soit aussi mise en cache avant la coupure réseau.
    await page.getByRole('link', { name: 'Courses' }).click()
    await expect(page.locator('.list-card').first()).toBeVisible()
    await page.getByRole('link', { name: 'Recettes' }).click()

    // Laisse le service worker s'activer et mettre en cache les réponses déjà visitées
    // (recette, agenda, liste de courses) avant de couper le réseau.
    await page.evaluate(() => navigator.serviceWorker.ready)
    await page.waitForTimeout(500)

    // Note : la coupure réseau de Playwright (CDP) empêche Chromium de délivrer une
    // requête de *navigation* (rechargement complet de page) au service worker — c'est
    // une limitation connue du navigateur, pas de l'implémentation. Dans la vraie appli,
    // la SPA reste chargée en mémoire tant que l'onglet est ouvert : on simule donc le
    // scénario réel, une navigation *côté client* (Vue Router) vers des pages déjà
    // visitées, sans jamais recharger la page pendant que l'on est hors ligne.
    await context.setOffline(true)
    try {
      await expect(page.getByText('Vous êtes hors ligne')).toBeVisible()

      await page.getByRole('link', { name: 'Recettes' }).click()
      await page.getByText(recipeTitle).click()
      await expect(page.locator('h1')).toHaveText(recipeTitle)

      await page.getByRole('link', { name: 'Courses' }).click()
      await page.locator('.list-card a').first().click()
      await expect(page.getByText(ingredientName)).toBeVisible()
    } finally {
      await context.setOffline(false)
    }
  })

  test('marking an item owned while offline queues the write and syncs on reconnect', async ({
    page,
    context,
  }) => {
    const suffix = Date.now() + 1
    const { shoppingListUrl, ingredientName } = await registerAndBuildShoppingList(page, suffix)

    await page.evaluate(() => navigator.serviceWorker.ready)
    await page.goto(shoppingListUrl)
    await expect(page.getByText(ingredientName)).toBeVisible()

    await context.setOffline(true)
    try {
      const itemCheckbox = page.locator('.item-row', { hasText: ingredientName }).locator('input[type="checkbox"]')
      await itemCheckbox.check()

      // Optimiste : la case reste cochée tout de suite, avec l'indicateur "en attente de sync".
      await expect(itemCheckbox).toBeChecked()
      await expect(
        page.locator('.item-row', { hasText: ingredientName }).locator('.pending-sync'),
      ).toBeVisible()
    } finally {
      await context.setOffline(false)
    }

    // Le retour en ligne déclenche automatiquement le vidage de la file d'attente.
    await expect(
      page.locator('.item-row', { hasText: ingredientName }).locator('.pending-sync'),
    ).toBeHidden({ timeout: 10000 })
    await expect(
      page.locator('.item-row', { hasText: ingredientName }).locator('input[type="checkbox"]'),
    ).toBeChecked()

    // Un rechargement confirme que l'état "possédé" a bien été persisté côté serveur.
    await page.reload()
    await expect(
      page.locator('.item-row', { hasText: ingredientName }).locator('input[type="checkbox"]'),
    ).toBeChecked()
  })
})
