import { expect, test } from '@playwright/test'

test('the login page links to the forgot-password flow, which always shows the same message', async ({
  page,
}) => {
  const suffix = Date.now()
  const username = `forgot-${suffix}`

  // Register a real account first, so this also covers the "email does exist" path —
  // the UI must not reveal whether the address it sent to is actually registered.
  await page.goto('/register')
  await page.getByLabel("Nom d'utilisateur").fill(username)
  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByLabel('Mot de passe').fill('password123!')
  await page.getByRole('button', { name: 'Créer mon compte' }).click()
  await page.waitForURL(/\/recipes$/)
  await page.evaluate(() => localStorage.clear())

  await page.goto('/login')
  await page.getByRole('link', { name: 'Mot de passe oublié ?' }).click()
  await expect(page).toHaveURL('/forgot-password')

  await page.getByLabel('Email').fill(`${username}@example.com`)
  await page.getByRole('button', { name: 'Envoyer le lien' }).click()
  await expect(page.getByText(/lien de réinitialisation vient de lui être envoyé/)).toBeVisible()

  // Same message for an email that was never registered.
  await page.goto('/forgot-password')
  await page.getByLabel('Email').fill('never-registered@example.com')
  await page.getByRole('button', { name: 'Envoyer le lien' }).click()
  await expect(page.getByText(/lien de réinitialisation vient de lui être envoyé/)).toBeVisible()
})

test('an invalid or expired reset link is rejected with a clear error', async ({ page }) => {
  await page.goto('/reset-password/not-a-real-uid/not-a-real-token')
  await page.getByLabel('Nouveau mot de passe', { exact: true }).fill('a-brand-new-pass')
  await page.getByLabel('Confirmer le nouveau mot de passe').fill('a-brand-new-pass')
  await page.getByRole('button', { name: 'Valider le nouveau mot de passe' }).click()

  await expect(page.getByText('Ce lien de réinitialisation est invalide ou a expiré.')).toBeVisible()
})

test('mismatched new passwords are caught before calling the API', async ({ page }) => {
  await page.goto('/reset-password/some-uid/some-token')
  await page.getByLabel('Nouveau mot de passe', { exact: true }).fill('a-brand-new-pass')
  await page.getByLabel('Confirmer le nouveau mot de passe').fill('does-not-match')
  await page.getByRole('button', { name: 'Valider le nouveau mot de passe' }).click()

  await expect(page.getByText("Les deux mots de passe ne correspondent pas.")).toBeVisible()
})
