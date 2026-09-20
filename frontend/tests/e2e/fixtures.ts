import { expect, request as playwrightRequest, test as base, type APIRequestContext } from '@playwright/test'

// Les tests e2e tournent contre un vrai backend et une vraie base (jamais réinitialisée) :
// tout ce qu'un test crée doit donc être supprimé à sa fin. Cette fixture (automatique, pour
// tous les tests qui importent `test` d'ici) observe les réponses du navigateur, retient ce
// qui a été créé, puis le supprime via l'API.
//
// - Comptes : suppression via `DELETE /api/auth/me/`, qui emporte en cascade recettes,
//   planning, listes de courses, partages. Le mot de passe peut avoir changé pendant le test
//   (changement ou réinitialisation) : on essaie tous ceux qu'on a vus passer.
// - Ingrédients créés à la volée : ils survivent au compte (les recettes les protègent), et
//   seul le staff peut supprimer un ingrédient. Il faut donc un compte staff, fourni par
//   E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD ; sans lui, on prévient et ils restent en base.
//   Seuls les ingrédients créés par le test lui-même sont supprimés, jamais ceux du seed.

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD

let warnedAboutAdmin = false

async function login(api: APIRequestContext, email: string, password: string): Promise<string | null> {
  const response = await api.post('/api/auth/token/', { data: { email, password } })
  if (!response.ok()) return null
  return (await response.json()).access as string
}

async function deleteAccount(api: APIRequestContext, email: string, passwords: Set<string>) {
  for (const password of passwords) {
    const token = await login(api, email, password)
    if (!token) continue
    await api.delete('/api/auth/me/', { headers: { Authorization: `Bearer ${token}` } })
    return
  }
  // Aucun mot de passe ne fonctionne : compte déjà supprimé par le test lui-même (cas normal).
}

async function deleteIngredients(api: APIRequestContext, ids: number[]) {
  if (!ids.length) return
  if (!ADMIN_EMAIL || !ADMIN_PASSWORD) {
    if (!warnedAboutAdmin) {
      warnedAboutAdmin = true
      console.warn(
        'E2E_ADMIN_EMAIL / E2E_ADMIN_PASSWORD non définis : les ingrédients créés par les tests ne sont pas supprimés.',
      )
    }
    return
  }
  const token = await login(api, ADMIN_EMAIL, ADMIN_PASSWORD)
  if (!token) {
    console.warn('Connexion du compte staff e2e impossible : ingrédients de test non supprimés.')
    return
  }
  for (const id of ids) {
    await api.delete(`/api/ingredients/${id}/`, { headers: { Authorization: `Bearer ${token}` } })
  }
}

export const test = base.extend<{ cleanup: void }>({
  cleanup: [
    async ({ context, baseURL }, use) => {
      const emails = new Set<string>()
      const passwords = new Set<string>()
      const ingredientIds: number[] = []

      context.on('response', async (response) => {
        const request = response.request()
        if (request.method() !== 'POST' || !response.ok()) return
        const path = new URL(response.url()).pathname
        try {
          if (path === '/api/auth/register/') {
            const body = request.postDataJSON()
            emails.add(body.email)
            passwords.add(body.password)
          } else if (path === '/api/auth/me/change-password/' || path === '/api/auth/password-reset/confirm/') {
            passwords.add(request.postDataJSON().new_password)
          } else if (path === '/api/ingredients/') {
            ingredientIds.push((await response.json()).id)
          }
        } catch {
          // Corps illisible (page fermée entre-temps) : rien à retenir.
        }
      })

      await use()

      const api = await playwrightRequest.newContext({ baseURL })
      try {
        for (const email of emails) await deleteAccount(api, email, passwords)
        await deleteIngredients(api, ingredientIds)
      } finally {
        await api.dispose()
      }
    },
    { auto: true },
  ],
})

export { expect }
