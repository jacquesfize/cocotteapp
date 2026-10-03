import { expect, test, type Page } from '../e2e/fixtures'
import { CAMILLE, isoDate, obtainTokens, seedDemoData, type DemoData } from './demoData'
import { loginWithTokens, settle, shotAround, shotElement, shotPage } from './shots'

// Captures d'écran de la documentation utilisateur (docs/assets/screenshots/).
//   E2E_ADMIN_EMAIL=... E2E_ADMIN_PASSWORD=... npm run docs:screenshots
// Un seul long test par projet (desktop / mobile) : les données de démo sont créées une fois
// au début, puis supprimées par la fixture de nettoyage (tests/e2e/fixtures.ts).

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD

test.beforeEach(async ({ page, context, baseURL }) => {
  // Derrière le proxy Vite du stack Docker de dev, l'API renvoie les images téléversées avec
  // une URL absolue sur l'hôte interne (http://backend:8000/media/...), injoignable depuis le
  // navigateur : on les resert via le proxy /media du frontend.
  await context.route(/^https?:\/\/backend(:\d+)?\/media\//, async (route) => {
    const url = new URL(route.request().url())
    const response = await route.fetch({ url: new URL(url.pathname, baseURL).toString() })
    await route.fulfill({ response })
  })
  await page.addInitScript(() => {
    localStorage.setItem('locale', 'en')
    if (!localStorage.getItem('theme-mode')) localStorage.setItem('theme-mode', 'light')
  })
})

async function loginAsCamille(page: Page, data: DemoData, path = '/') {
  await loginWithTokens(page, data.camilleToken, data.camilleRefresh, path)
}

test('desktop documentation screenshots', async ({ page, context }, testInfo) => {
  test.skip(testInfo.project.name !== 'desktop', 'desktop-only shots')

  await test.step('public pages', async () => {
    await page.goto('/')
    await expect(page.locator('.thematic-avatar').first()).toBeVisible()
    await shotPage(page, 'home-public', { fullPage: true })

    await page.goto('/login')
    await shotPage(page, 'login')
    await page.goto('/register')
    await shotPage(page, 'register')
    await page.goto('/forgot-password')
    await shotPage(page, 'forgot-password')
  })

  const data = await seedDemoData(page)
  const gratinUrl = `/recipes/${data.recipes.gratin}`

  await test.step('home', async () => {
    await loginAsCamille(page, data)
    await expect(page.locator('.week-strip')).toBeVisible()
    await expect(page.getByText('Creamy sweet potato gratin').first()).toBeVisible()
    await shotPage(page, 'home', { fullPage: true })

    // "New recipe" / "Import" sont désormais réunis dans un seul bouton ouvrant un petit menu.
    await page.getByRole('button', { name: 'New recipe' }).click()
    await page.getByRole('button', { name: 'Import from a URL' }).click()
    const dialog = page.getByRole('dialog')
    await dialog.getByLabel('Import from a URL').fill('https://www.example.com/recipes/french-onion-soup')
    await shotElement(dialog, 'recipe-import-url')
    await dialog.getByRole('button', { name: 'Close' }).click()
  })

  await test.step('recipe list', async () => {
    await page.goto('/recipes')
    await expect(page.locator('.recipe-grid')).toBeVisible()
    await shotPage(page, 'recipe-list')

    await page.goto('/recipes?diet_type=vegan&max_prep_time=20&ingredients=Pois%20chiches')
    // Desktop : le panneau de filtres est toujours affiché en colonne latérale.
    await expect(page.locator('#recipe-filters-panel')).toBeVisible()
    await shotElement(page.locator('#recipe-filters-panel'), 'recipe-list-filters')
  })

  await test.step('random recipe', async () => {
    // Le tirage est aléatoire sur toute la base : on le fige sur une recette de démo.
    await page.route(/\/api\/recipes\/random\//, async (route) => {
      const response = await route.fetch({
        url: new URL(`/api/recipes/${data.recipes.ratatouille}/`, route.request().url()).toString(),
      })
      await route.fulfill({ response })
    })
    await page.goto('/recipes/random')
    await page.getByRole('button', { name: 'Roll the dice' }).click()
    await expect(page.getByRole('heading', { name: 'Provençal ratatouille' })).toBeVisible()
    // Laisse le dé se poser (animation de fin de lancer) avant la capture.
    await page.waitForTimeout(400)
    await shotPage(page, 'random-recipe')
    await page.unroute(/\/api\/recipes\/random\//)
  })

  await test.step('recipe detail', async () => {
    await page.goto(gratinUrl)
    await expect(page.getByRole('heading', { name: 'Creamy sweet potato gratin' })).toBeVisible()
    await expect(page.locator('.recipe-photo-frame img')).toBeVisible()
    await shotPage(page, 'recipe-detail')

    await shotElement(page.locator('.ingredients-steps-row'), 'recipe-detail-steps')
    const nutrition = page.locator('.card').filter({ has: page.getByRole('heading', { name: 'Nutrition facts' }) })
    await expect(nutrition).toBeVisible()
    await shotElement(nutrition, 'recipe-detail-nutrition')

    const planCard = page.locator('.card').filter({ has: page.getByRole('heading', { name: 'Add to planner' }) })
    await planCard.getByLabel('Date').fill(isoDate(new Date(data.weekStart.getTime() + 8 * 86_400_000)))
    await planCard.getByLabel('Meal').selectOption('dinner')
    await planCard.getByLabel('Date').blur()
    await expect(planCard.getByTestId('warning-allergy')).toBeVisible()
    await shotElement(planCard, 'recipe-add-to-planning')

    await shotElement(page.locator('.versions-section'), 'recipe-versions')

    const comments = page.locator('.card').filter({ has: page.getByRole('heading', { name: 'Comments' }) })
    await expect(comments.locator('.comment').first()).toBeVisible()
    await shotElement(comments, 'recipe-comments')

    await page.evaluate(() => window.scrollTo(0, 0))
    await page.getByRole('button', { name: 'Actions' }).click()
    const panel = page.locator('#recipe-actions-panel')
    await expect(panel.getByText('Create a variant')).toBeVisible()
    await shotAround(page, [page.locator('.page-header'), panel], 'recipe-actions-menu')

    await panel.getByText('Create a variant').click()
    await page.getByPlaceholder('Variant name (e.g. Gluten-free)').fill('Dairy-free')
    await shotAround(page, [page.locator('.page-header'), page.locator('.fork-form')], 'recipe-fork-dialog')
    await page.locator('.fork-form').getByRole('button', { name: 'Cancel' }).click()
  })

  await test.step('recipe form', async () => {
    await page.goto('/recipes/new')
    await page.getByLabel('Title').fill('Stuffed courgettes')
    await page
      .getByLabel('Description')
      .fill('Round courgettes filled with a garlicky tomato and feta stuffing, baked until tender.')
    await page.getByLabel('Servings').fill('4')
    await page.getByLabel('Prep time (min)').fill('20')
    await page.getByLabel('Cook time (min)').fill('35')
    await page.getByLabel('Diet').selectOption('vegetarian')

    const addIngredient = async (index: number, name: string, quantity: string) => {
      if (index > 0) await page.getByRole('button', { name: 'Add an ingredient' }).click()
      const picker = page.locator(`#ingredient-${index}`)
      await picker.fill(name)
      await page
        .locator('.picker .suggestions-dropdown li', { hasText: new RegExp(`^\\s*${name}\\s*$`) })
        .first()
        .click()
      await page.locator(`#quantity-${index}`).fill(quantity)
    }
    await addIngredient(0, 'Courgette', '600')
    await addIngredient(1, 'Tomate', '200')
    await addIngredient(2, 'Feta', '100')

    const step1 = page.locator('#step-0')
    await step1.fill('Halve the @Courgette and scoop out the flesh. Bake for ~{10%minutes}.')
    await page.getByRole('button', { name: 'Add a step' }).click()
    await page.locator('body').click({ position: { x: 5, y: 5 } })
    await shotPage(page, 'recipe-form', { fullPage: true })

    const step2 = page.locator('#step-1')
    await step2.click()
    await step2.pressSequentially('Fill with the tomato and feta mixture, then top with @Basil', { delay: 20 })
    const stepsCard = page.locator('.card').filter({ has: page.getByRole('heading', { name: 'Steps' }) })
    const suggestions = stepsCard.locator('.suggestions-dropdown')
    await expect(suggestions).toBeVisible()
    await shotAround(page, [stepsCard, suggestions], 'recipe-form-mention', 12)

    await step2.fill('')
    await step2.pressSequentially('Crumble the @smoked_tofu', { delay: 20 })
    const create = stepsCard.locator('.suggestions-dropdown .create')
    await expect(create).toBeVisible()
    await create.dispatchEvent('mousedown')
    const modal = page.getByRole('dialog')
    await expect(modal).toBeVisible()
    await modal.locator('#ingredient-modal-name').blur()
    await shotElement(modal, 'ingredient-create-modal')
    await modal.getByRole('button', { name: 'Cancel' }).first().click()

    await page.goto('/recipes/new')
    await page.getByRole('tab', { name: 'Paste Cooklang' }).click()
    await page.locator('#cooklang-title').fill('Garlic mushrooms on toast')
    await page.locator('#cooklang-servings').fill('2')
    await page
      .locator('#cooklang-text')
      .fill(
        [
          "Slice the @Champignon_de_Paris{250%g} and fry them in @Huile_d'olive{2%tbsp} for ~{8%minutes}.",
          'Add the chopped @Ail{2%piece} and @Persil{1%tbsp}, then season with @Sel{1%pinch}.',
          'Toast the @Pain_complet{2%piece} for ~{3%minutes} and pile the mushrooms on top.',
        ].join('\n'),
      )
    await page.locator('body').click({ position: { x: 5, y: 5 } })
    await shotPage(page, 'recipe-form-cooklang')
  })

  await test.step('planning', async () => {
    await page.goto('/planning')
    // La grille n'affiche qu'un jour à la fois : on sélectionne le premier jour qui a des repas.
    const chips = page.locator('.day-chip')
    const visibleMeal = page.locator('.agenda-cell.is-active-day a').first()
    for (let i = 0; i < 7 && !(await visibleMeal.isVisible()); i++) {
      await chips.nth(i).click()
    }
    await expect(visibleMeal).toBeVisible()
    await shotPage(page, 'planning-week', { fullPage: true })

    // La collation est désactivée par défaut (PLANNING_SNACK_ENABLED) : on illustre l'ajout
    // d'un repas sur une case petit-déjeuner vide plutôt que sur la collation.
    const emptyBreakfastDate = new Date(data.weekStart.getTime() + 86_400_000)
    await chips.nth(1).click()
    const breakfastCell = page.locator(
      `.agenda-cell[data-meal-type="breakfast"][data-date="${isoDate(emptyBreakfastDate)}"]`,
    )
    await breakfastCell.getByRole('button', { name: 'Add a meal' }).click()
    const dialog = page.getByRole('dialog')
    await dialog.getByPlaceholder('Search a recipe...').fill('gratin')
    await expect(dialog.locator('.picker-results li').first()).toBeVisible()
    await shotElement(dialog, 'planning-add-meal')
    await dialog.getByRole('button', { name: 'Cancel' }).click()

    // Alertes nutritionnelles : bascule d'instance elle aussi désactivée par défaut (voir
    // NUTRITION_ALERTS_ENABLED plus haut) — le bouton est alors absent du planner.
    const nutritionButton = page.getByRole('button', { name: 'Nutritional intake' })
    if (await nutritionButton.count()) {
      await nutritionButton.click()
      const nutritionDialog = page.getByRole('dialog')
      await expect(nutritionDialog.locator('.carbon-summary')).toBeVisible()
      await shotElement(nutritionDialog, 'planning-nutrition')
      await nutritionDialog.getByRole('button', { name: 'Close' }).click()
    } else {
      console.warn('NUTRITION_ALERTS_ENABLED is off: planning-nutrition screenshot skipped.')
    }

    await page.getByRole('button', { name: 'Export' }).click()
    const menu = page.locator('.calendar-export .menu')
    await expect(menu.getByText('Add to Google Calendar')).toBeVisible()
    await shotAround(page, [page.locator('.calendar-export'), menu], 'planning-calendar-export')
    await page.getByRole('button', { name: 'Export' }).click()

    await page.getByRole('button', { name: 'Month' }).click()
    await expect(page.locator('.month-entries a').first()).toBeVisible()
    await shotPage(page, 'planning-month', { fullPage: true })
  })

  await test.step('shopping lists', async () => {
    await page.goto('/shopping-lists')
    await expect(page.locator('.list-card').first()).toBeVisible()
    await shotPage(page, 'shopping-lists')

    await page.goto(`/shopping-lists/${data.shoppingListId}`)
    await expect(page.locator('.item-row').first()).toBeVisible()
    await shotPage(page, 'shopping-list-detail')

    await context.setOffline(true)
    await expect(page.locator('.offline-banner')).toBeVisible()
    await shotPage(page, 'offline-banner')
    await context.setOffline(false)
    await expect(page.locator('.offline-banner')).toBeHidden()
  })

  await test.step('account', async () => {
    // Navigation côté client : le formulaire de profil est initialisé depuis l'utilisateur
    // courant, qui doit donc être déjà chargé (après un rechargement complet il l'est en différé).
    await page.goto('/')
    await expect(page.locator('.week-strip')).toBeVisible()
    await page.getByRole('button', { name: 'Account' }).click()
    await page.locator('#account-panel').getByRole('link', { name: 'My account' }).click()
    const card = (title: string) =>
      page.locator('.card').filter({ has: page.getByRole('heading', { name: title, exact: true }) })
    await expect(page.getByTestId('allergies-gluten')).toBeChecked()
    await shotElement(card('Profile'), 'account-profile')
    await shotElement(page.locator('.allergen-fieldset'), 'account-allergens')
    await shotElement(page.getByTestId('appearance-card'), 'account-theme')
    await expect(card('Share my agenda').locator('.share-list li')).toHaveCount(1)
    await shotElement(card('Share my agenda'), 'account-sharing')
    await shotElement(page.getByTestId('consent-card'), 'account-consent')
    await shotAround(page, [card('Export my data'), page.locator('.danger-zone')], 'account-data')
  })

  await test.step('dark mode', async () => {
    await page.goto('/')
    await page.getByTestId('theme-toggle').click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
    await expect(page.locator('.week-strip')).toBeVisible()
    await shotPage(page, 'dark-mode-home')
    await page.getByTestId('theme-toggle').click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light')
  })

  await test.step('admin', async () => {
    if (!ADMIN_EMAIL || !ADMIN_PASSWORD) {
      console.warn('E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD not set: admin screenshots skipped.')
      return
    }
    const tokens = await obtainTokens(page.request, ADMIN_EMAIL!, ADMIN_PASSWORD!)
    if (!tokens) throw new Error('Could not log in as the admin account')
    await loginWithTokens(page, tokens.access, tokens.refresh, '/')
    await expect(page.locator('.thematic-avatar').first()).toBeVisible()

    await page.getByRole('button', { name: 'Account' }).click()
    const panel = page.locator('#account-panel')
    await expect(panel.getByText('Administration')).toBeVisible()
    await shotAround(page, [page.getByRole('button', { name: 'Account' }), panel], 'navbar-account-menu', 12)
    await page.keyboard.press('Escape')

    await page.goto('/admin/users')
    await page.getByLabel('Search').fill('example.com')
    await expect(page.getByRole('cell', { name: CAMILLE.email })).toBeVisible()
    await shotPage(page, 'admin-users')

    await page.goto('/admin/ingredients')
    await expect(page.locator('.admin-table tbody tr').first()).toBeVisible()
    await shotPage(page, 'admin-ingredients')

    await page.getByLabel('Search').fill('Tomate')
    const tomato = page
      .locator('.admin-table tbody tr')
      .filter({ has: page.getByRole('cell', { name: 'Tomate', exact: true }) })
    await tomato.getByRole('button', { name: 'Edit' }).click()
    const modal = page.getByRole('dialog')
    await expect(modal).toBeVisible()
    await modal.locator('#ingredient-modal-name').blur()
    await shotElement(modal, 'admin-ingredient-modal')
    await modal.getByRole('button', { name: 'Cancel' }).first().click()

    await page.goto('/admin/thematic-pages')
    await expect(page.locator('.admin-table tbody tr').first()).toBeVisible()
    await shotPage(page, 'admin-thematic-pages')
    await page.locator('.admin-table tbody tr').first().getByRole('button', { name: 'Edit' }).click()
    const form = page.locator('.card').filter({ has: page.getByRole('heading', { name: 'Edit thematic page' }) })
    await expect(form).toBeVisible()
    await shotElement(form, 'admin-thematic-page-form')
    await form.getByRole('button', { name: 'Cancel' }).click()

    const djangoAdmin = await context.newPage()
    await djangoAdmin.goto('http://localhost:8000/django-admin/login/?next=/django-admin/')
    await djangoAdmin.locator('#id_username').fill(ADMIN_EMAIL!)
    await djangoAdmin.locator('#id_password').fill(ADMIN_PASSWORD!)
    await djangoAdmin.locator('input[type="submit"]').click()
    await expect(djangoAdmin.locator('#content-main')).toBeVisible()
    await shotPage(djangoAdmin, 'django-admin')
    await djangoAdmin.close()
  })
})

test('mobile documentation screenshots', async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== 'mobile', 'mobile-only shots')
  const data = await seedDemoData(page)

  await loginAsCamille(page, data)
  await expect(page.locator('.week-strip')).toBeVisible()
  await expect(page.locator('.tabbar')).toBeVisible()
  await shotPage(page, 'mobile-home')

  await page.goto(`/recipes/${data.recipes.ratatouille}`)
  await expect(page.locator('.recipe-photo-frame img')).toBeVisible()
  await shotPage(page, 'mobile-recipe-detail')

  await test.step('cook mode', async () => {
    await page.getByRole('button', { name: 'Cook mode' }).click()
    const cookMode = page.locator('.cook-mode')
    await expect(cookMode).toBeVisible()
    await shotElement(cookMode, 'mobile-cookmode-step')

    await cookMode.locator('.cook-mode-nav.next').click()
    await page.waitForTimeout(500) // let the out-in step transition settle
    await cookMode.locator('.timer-chip').first().click()
    await expect(cookMode.locator('.cook-mode-timer-dock')).toBeVisible()
    await shotElement(cookMode, 'mobile-cookmode-timer-dock')

    await cookMode.locator('.ingredient-mention').first().click()
    await expect(cookMode.locator('.ingredient-popover')).toBeVisible()
    await shotElement(cookMode, 'mobile-cookmode-ingredient-popover')

    await cookMode.getByRole('button', { name: 'Show ingredients' }).click()
    await expect(cookMode.locator('.cook-mode-ingredients')).toHaveClass(/open/)
    await shotElement(cookMode, 'mobile-cookmode-ingredients')

    await page.keyboard.press('Escape')
    await page.keyboard.press('Escape')
    await expect(cookMode).toBeHidden()
  })

  await page.goto(`/shopping-lists/${data.shoppingListId}`)
  await expect(page.locator('.item-row').first()).toBeVisible()
  await settle(page)
  await shotPage(page, 'mobile-shopping-list')
})
