import { expect, test } from './fixtures'

test('shows an image, embeds a YouTube video, and downloads a recipe PDF', async ({ page }) => {
  const suffix = Date.now()
  const username = `media-${suffix}`
  const recipeTitle = `Ratatouille ${suffix}`
  const ingredientName = `courgette-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  await page.getByRole('link', { name: 'Nouvelle recette' }).click()
  await page.getByLabel('Titre').fill(recipeTitle)
  await page.getByPlaceholder('Rechercher un ingrédient...').fill(ingredientName)
  await page.getByText(`+ Créer « ${ingredientName} »`).click()
  await page.getByRole('button', { name: "Créer l'ingrédient" }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.locator('input[id^="quantity-"]').fill('200')
  await page.getByLabel('Étape 1').fill('Faire mijoter les légumes.')
  await page.getByLabel("URL de l'image").fill('https://example.com/ratatouille.jpg')
  await page.getByLabel("Licence de l'image").selectOption('public_domain')
  await page
    .getByLabel('Vidéo (lien YouTube)')
    .fill('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
  await page.getByLabel('Source (lien de la recette d\'origine)').fill('https://example.com/recette-originale')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await page.waitForURL(/\/recipes\/\d+$/)

  await expect(page.locator('.recipe-photo-frame img')).toHaveAttribute(
    'src',
    'https://example.com/ratatouille.jpg',
  )
  await expect(page.locator('.video-wrapper iframe')).toHaveAttribute(
    'src',
    'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ',
  )
  await expect(page.getByRole('link', { name: 'Source' })).toHaveAttribute(
    'href',
    'https://example.com/recette-originale',
  )

  // La vidéo doit s'afficher à côté de la photo (même ligne), pas en dessous.
  const photoBox = await page.locator('.recipe-photo-wrapper').boundingBox()
  const videoBox = await page.locator('.video-wrapper').boundingBox()
  if (!photoBox || !videoBox) throw new Error('Expected both the photo and the video to be laid out')
  expect(Math.abs(photoBox.y - videoBox.y)).toBeLessThan(5)
  expect(videoBox.x).toBeGreaterThan(photoBox.x + photoBox.width - 5)

  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Télécharger en PDF' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toMatch(/\.pdf$/)

  // Thematic page: clicking the ingredient jumps to a filtered, shareable recipe list.
  await page.getByRole('link', { name: ingredientName }).click()
  await expect(page).toHaveURL(new RegExp(`/recipes\\?ingredients=${ingredientName}`))
  await expect(page.getByRole('link', { name: recipeTitle, exact: true })).toBeVisible()
})

test('downloads a PDF of the current week from the planner', async ({ page }) => {
  const suffix = Date.now()
  const username = `weekpdf-${suffix}`
  const recipeTitle = `Soupe rapide ${suffix}`
  const ingredientName = `poireau-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  await page.getByRole('link', { name: 'Nouvelle recette' }).click()
  await page.getByLabel('Titre').fill(recipeTitle)
  await page.getByPlaceholder('Rechercher un ingrédient...').fill(ingredientName)
  await page.getByText(`+ Créer « ${ingredientName} »`).click()
  await page.getByRole('button', { name: "Créer l'ingrédient" }).click()
  await expect(page.getByRole('dialog')).toBeHidden()
  await page.locator('input[id^="quantity-"]').fill('100')
  await page.getByLabel('Étape 1').fill('Mixer le tout.')
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await page.waitForURL(/\/recipes\/\d+$/)

  await page.getByRole('link', { name: 'Agenda' }).click()
  const dinnerSlot = page.locator('.agenda-cell[data-meal-type="dinner"]').first()
  await dinnerSlot.getByRole('button', { name: 'Ajouter un repas' }).click()
  await dinnerSlot.getByPlaceholder('Rechercher une recette...').fill(recipeTitle)
  await dinnerSlot.locator('.suggestions').getByText(recipeTitle).click()
  await dinnerSlot.getByRole('button', { name: 'Ajouter' }).click()
  await expect(dinnerSlot.getByText(recipeTitle)).toBeVisible()

  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: 'Télécharger le PDF de la semaine' }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toMatch(/\.pdf$/)
})
