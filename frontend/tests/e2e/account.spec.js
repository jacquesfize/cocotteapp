import { expect, test } from '@playwright/test'

test('a user can update their profile, export their data and delete their account', async ({ page }) => {
  const suffix = Date.now()
  const username = `acct-${suffix}`
  const newUsername = `acct-renamed-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  await page.locator('.account-button').click()
  await page.getByRole('link', { name: 'Mon compte' }).click()
  await expect(page).toHaveURL('/account')

  // Update the profile.
  await page.getByLabel("Nom d'utilisateur").fill(newUsername)
  await page.getByRole('button', { name: 'Enregistrer' }).click()
  await expect(page.getByText('Profil mis à jour.')).toBeVisible()
  await page.locator('.account-button').click()
  await expect(page.locator('.account-username')).toHaveText(newUsername)
  await page.mouse.click(5, 5)

  // Change password: wrong current password is rejected.
  await page.getByLabel('Mot de passe actuel').fill('wrong-password')
  await page.getByLabel('Nouveau mot de passe', { exact: true }).fill('brand-new-pass')
  await page.getByLabel('Confirmer le nouveau mot de passe').fill('brand-new-pass')
  await page.getByRole('button', { name: 'Changer le mot de passe' }).click()
  await expect(page.getByText(/mot de passe actuel incorrect/)).toBeVisible()

  // Mismatched confirmation is caught before hitting the API.
  await page.getByLabel('Mot de passe actuel').fill('password123!')
  await page.getByLabel('Nouveau mot de passe', { exact: true }).fill('brand-new-pass')
  await page.getByLabel('Confirmer le nouveau mot de passe').fill('does-not-match')
  await page.getByRole('button', { name: 'Changer le mot de passe' }).click()
  await expect(page.getByText("Les deux mots de passe ne correspondent pas.")).toBeVisible()

  // Export the data archive.
  const downloadPromise = page.waitForEvent('download')
  await page.getByRole('button', { name: "Télécharger l'archive" }).click()
  const download = await downloadPromise
  expect(download.suggestedFilename()).toMatch(/\.zip$/)

  // Delete the account: confirm dialog, then logged out and redirected home.
  page.once('dialog', (dialog) => dialog.accept())
  await page.getByRole('button', { name: 'Supprimer mon compte' }).click()
  await expect(page).toHaveURL('/')
  await expect(page.getByRole('link', { name: 'Connexion' })).toBeVisible()
})

test('changing the password logs the user out and the new password works', async ({ page }) => {
  const suffix = Date.now()
  const username = `pwd-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  await page.goto('/account')
  await page.getByLabel('Mot de passe actuel').fill('password123!')
  await page.getByLabel('Nouveau mot de passe', { exact: true }).fill('a-brand-new-pass')
  await page.getByLabel('Confirmer le nouveau mot de passe').fill('a-brand-new-pass')
  await page.getByRole('button', { name: 'Changer le mot de passe' }).click()

  await expect(page).toHaveURL(/\/login/, { timeout: 10000 })

  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Mot de passe').fill('a-brand-new-pass')
  await page.getByRole('button', { name: 'Se connecter' }).click()
  await expect(page).toHaveURL(/\/recipes$/)
})

test('a non-staff user is redirected away from the admin users page', async ({ page }) => {
  const suffix = Date.now()
  const username = `notstaff-${suffix}`

  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)

  await expect(page.getByRole('link', { name: 'Admin' })).toHaveCount(0)

  // Whether the router guard catches it immediately or the API 403s first (a fresh
  // reload races fetchMe()), the user list itself must never become visible.
  await page.goto('/admin/users')
  await expect(page.locator('.admin-table')).toHaveCount(0)
})
