import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import type { APIRequestContext, Page } from '@playwright/test'

// Jeu de données de démonstration pour les captures de la documentation. Tout est créé via
// l'API, au nom d'un compte « Camille » enregistré depuis la page (fetch côté navigateur) pour
// que la fixture de nettoyage de tests/e2e/fixtures.ts l'observe et le supprime à la fin du
// test (la suppression du compte emporte en cascade recettes, planning, listes, partages).

export const DEMO_PASSWORD = 'docs-demo-password-2024'
export const CAMILLE = { username: 'Camille', email: 'camille.docs@example.com' }
export const ALEX = { username: 'Alex', email: 'alex.docs@example.com' }

const ASSET = (relative: string) => fileURLToPath(new URL(relative, import.meta.url))
const AUTH_COVER = ASSET('../../src/assets/auth-cover.jpg')
const SEASONAL = ASSET(
  '../../../backend/apps/recipes/management/commands/seed_data/thematic_pages/produits-de-saison.jpg',
)

interface Crop {
  file: string
  /** Dimensions de l'image source (px) */
  size: [number, number]
  /** Centre et largeur de la zone à cadrer (px source), rapport 3:2 */
  center?: [number, number]
  width?: number
}

type Unit = 'g' | 'kg' | 'ml' | 'l' | 'piece' | 'tbsp' | 'tsp' | 'pinch'

interface DemoRecipe {
  key: string
  title: string
  description: string
  servings: number
  prep: number
  cook: number
  diet: 'omnivore' | 'vegetarian' | 'vegan'
  ingredients: Array<[string, number, Unit]>
  steps: string[]
  image: Crop
}

const COVER_SIZE: [number, number] = [1000, 667]
const SEASONAL_SIZE: [number, number] = [600, 900]

export const RECIPES: DemoRecipe[] = [
  {
    key: 'gratin',
    title: 'Creamy sweet potato gratin',
    description: 'Thin slices of sweet potato baked in a garlicky béchamel with Comté — perfect for autumn evenings.',
    servings: 6,
    prep: 20,
    cook: 50,
    diet: 'vegetarian',
    ingredients: [
      ['Patate douce', 900, 'g'],
      ['Lait entier', 400, 'ml'],
      ['Crème fraîche', 150, 'g'],
      ['Farine de blé', 25, 'g'],
      ['Beurre', 25, 'g'],
      ['Comté', 80, 'g'],
      ['Ail', 5, 'g'],
      ['Noix de muscade', 1, 'pinch'],
      ['Sel', 1, 'pinch'],
    ],
    steps: [
      'Preheat the oven to 180 °C and rub the dish with the @Ail.',
      'Melt the @Beurre, stir in the @Farine_de_blé, then whisk in the @Lait_entier and cook for ~{5%minutes} until thick.',
      'Off the heat, add the @Crème_fraîche, @Noix_de_muscade and @Sel.',
      'Layer the thinly sliced @Patate_douce with the sauce and top with grated @Comté.',
      'Bake for ~{50%minutes} until golden and bubbling.',
    ],
    image: { file: AUTH_COVER, size: COVER_SIZE, center: [700, 400], width: 420 },
  },
  {
    key: 'toast',
    title: 'Avocado toast with sesame',
    description: 'A quick, creamy breakfast: smashed avocado on toasted wholemeal bread with lemon and sesame.',
    servings: 2,
    prep: 10,
    cook: 3,
    diet: 'vegan',
    ingredients: [
      ['Pain complet', 4, 'piece'],
      ['Avocat', 2, 'piece'],
      ['Citron', 1, 'piece'],
      ['Graines de sésame', 1, 'tbsp'],
      ['Sel', 1, 'pinch'],
    ],
    steps: [
      'Toast the slices of @Pain_complet for ~{3%minutes}.',
      'Mash the @Avocat with the juice of half a @Citron and a pinch of @Sel.',
      'Spread on the toast and sprinkle with @Graines_de_sésame.',
    ],
    image: { file: AUTH_COVER, size: COVER_SIZE, center: [470, 480], width: 420 },
  },
  {
    key: 'soup',
    title: 'Red lentil & carrot soup',
    description: 'A velvety, warming soup with a hint of ginger and cumin — ready in 30 minutes.',
    servings: 4,
    prep: 10,
    cook: 25,
    diet: 'vegan',
    ingredients: [
      ['Lentilles corail', 200, 'g'],
      ['Carotte', 400, 'g'],
      ['Oignon', 100, 'g'],
      ['Gingembre frais', 10, 'g'],
      ['Cumin', 1, 'tsp'],
      ["Huile d'olive", 1, 'tbsp'],
      ['Citron', 1, 'piece'],
      ['Sel', 1, 'pinch'],
    ],
    steps: [
      "Soften the chopped @Oignon in the @Huile_d'olive for ~{5%minutes}.",
      'Add the sliced @Carotte, grated @Gingembre_frais and @Cumin, then stir for one minute.',
      'Add the rinsed @Lentilles_corail and 1 litre of water. Simmer for ~{20%minutes}.',
      'Blend until smooth, season with @Sel and a squeeze of @Citron.',
    ],
    image: { file: SEASONAL, size: SEASONAL_SIZE, center: [330, 480], width: 380 },
  },
  {
    key: 'ratatouille',
    title: 'Provençal ratatouille',
    description: 'Summer vegetables slowly simmered with olive oil, garlic and herbes de Provence.',
    servings: 4,
    prep: 20,
    cook: 45,
    diet: 'vegan',
    ingredients: [
      ['Aubergine', 300, 'g'],
      ['Courgette', 300, 'g'],
      ['Poivron rouge', 200, 'g'],
      ['Tomate', 400, 'g'],
      ['Oignon', 150, 'g'],
      ['Ail', 10, 'g'],
      ["Huile d'olive", 3, 'tbsp'],
      ['Herbes de Provence', 1, 'tsp'],
      ['Basilic frais', 5, 'g'],
    ],
    steps: [
      'Dice the @Aubergine, @Courgette and @Poivron_rouge into 2 cm cubes.',
      "Brown the @Oignon and @Ail in the @Huile_d'olive for ~{5%minutes}.",
      'Add the vegetables, the chopped @Tomate and the @Herbes_de_Provence.',
      'Cover and simmer gently for ~{40%minutes}, stirring from time to time.',
      'Serve warm, topped with torn @Basilic_frais.',
    ],
    image: { file: AUTH_COVER, size: COVER_SIZE, center: [450, 250], width: 440 },
  },
  {
    key: 'carrots',
    title: 'Roasted carrots with crispy chickpeas',
    description: 'Sweet roasted carrots on a bed of crunchy salad, with cumin-roasted chickpeas and capers.',
    servings: 2,
    prep: 15,
    cook: 30,
    diet: 'vegan',
    ingredients: [
      ['Carotte', 500, 'g'],
      ['Pois chiches', 240, 'g'],
      ['Salade verte', 150, 'g'],
      ['Câpres', 1, 'tbsp'],
      ['Citron', 1, 'piece'],
      ["Huile d'olive", 2, 'tbsp'],
      ['Cumin', 1, 'tsp'],
      ['Sel', 1, 'pinch'],
    ],
    steps: [
      "Toss the whole @Carotte and the drained @Pois_chiches with the @Huile_d'olive, @Cumin and @Sel.",
      'Roast at 200 °C for ~{30%minutes}, shaking the tray halfway.',
      'Serve on the @Salade_verte with the @Câpres and lemon wedges from the @Citron.',
    ],
    image: { file: SEASONAL, size: SEASONAL_SIZE },
  },
  {
    key: 'curry',
    title: 'Sweet potato & chickpea curry',
    description: 'A fragrant one-pot curry with turmeric, ginger and spinach, served with basmati rice.',
    servings: 4,
    prep: 15,
    cook: 30,
    diet: 'vegan',
    ingredients: [
      ['Patate douce', 400, 'g'],
      ['Pois chiches', 240, 'g'],
      ['Tomates concassées', 400, 'g'],
      ['Épinard', 100, 'g'],
      ['Oignon', 100, 'g'],
      ['Ail', 10, 'g'],
      ['Gingembre frais', 10, 'g'],
      ['Curcuma', 1, 'tsp'],
      ['Cumin', 1, 'tsp'],
      ['Riz basmati', 300, 'g'],
      ['Coriandre fraîche', 5, 'g'],
    ],
    steps: [
      'Fry the @Oignon, @Ail and @Gingembre_frais with the @Curcuma and @Cumin for ~{3%minutes}.',
      'Add the diced @Patate_douce, the @Pois_chiches and the @Tomates_concassées. Simmer for ~{25%minutes}.',
      'Meanwhile, cook the @Riz_basmati for ~{12%minutes}.',
      'Stir the @Épinard into the curry until wilted and finish with @Coriandre_fraîche.',
    ],
    image: { file: AUTH_COVER, size: COVER_SIZE, center: [620, 380], width: 440 },
  },
  {
    key: 'bowl',
    title: 'Rainbow buddha bowl',
    description: 'Roasted sweet potato, chickpeas, avocado and crunchy vegetables with a lemon-tahini dressing.',
    servings: 2,
    prep: 20,
    cook: 25,
    diet: 'vegan',
    ingredients: [
      ['Patate douce', 300, 'g'],
      ['Pois chiches', 240, 'g'],
      ['Avocat', 1, 'piece'],
      ['Tomate', 200, 'g'],
      ['Chou rouge', 100, 'g'],
      ['Salade verte', 80, 'g'],
      ['Tahin', 2, 'tbsp'],
      ['Citron', 1, 'piece'],
      ["Huile d'olive", 1, 'tbsp'],
    ],
    steps: [
      "Roast the cubed @Patate_douce with the @Huile_d'olive at 200 °C for ~{25%minutes}.",
      'Whisk the @Tahin with the juice of the @Citron and a little water.',
      'Arrange the @Salade_verte, @Pois_chiches, sliced @Avocat, @Tomate and shredded @Chou_rouge in bowls.',
      'Add the sweet potato and drizzle with the dressing.',
    ],
    image: { file: AUTH_COVER, size: COVER_SIZE },
  },
]

/**
 * Une mention Cooklang s'arrête au premier espace : "@Sel." engloberait le point. On ferme
 * donc par des accolades vides ("@Sel{}.") une mention suivie d'une ponctuation.
 */
function closeMentions(step: string): string {
  return step.replace(/(@[^\s@#~{}]+?)([.,;:!?])(?=\s|$)/g, '$1{}$2')
}

export interface DemoData {
  camilleToken: string
  camilleRefresh: string
  recipes: Record<string, number>
  forkId: number
  shoppingListId: number
  weekStart: Date
}

export function isoDate(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function startOfWeek(date = new Date()): Date {
  const d = new Date(date)
  const day = d.getDay()
  d.setDate(d.getDate() + (day === 0 ? -6 : 1 - day))
  d.setHours(0, 0, 0, 0)
  return d
}

function addDays(date: Date, n: number): Date {
  const d = new Date(date)
  d.setDate(d.getDate() + n)
  return d
}

export async function obtainTokens(api: APIRequestContext, email: string, password: string) {
  const response = await api.post('/api/auth/token/', { data: { email, password } })
  if (!response.ok()) return null
  return (await response.json()) as { access: string; refresh: string }
}

/** Supprime un compte de démo resté en base (run précédent interrompu). */
async function deleteIfExists(api: APIRequestContext, email: string) {
  const tokens = await obtainTokens(api, email, DEMO_PASSWORD)
  if (!tokens) return
  await api.delete('/api/auth/me/', { headers: { Authorization: `Bearer ${tokens.access}` } })
}

/** Inscription depuis la page : la fixture de nettoyage observe les réponses du navigateur. */
async function registerInBrowser(page: Page, user: { username: string; email: string }, diet = 'omnivore') {
  const status = await page.evaluate(
    async ({ user, password, diet }) => {
      const response = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...user, password, diet_type: diet, activity_level: 'moderate' }),
      })
      return response.status
    },
    { user, password: DEMO_PASSWORD, diet },
  )
  if (status !== 201) throw new Error(`Registration of ${user.email} failed (${status})`)
}

/** Recadre une photo (3:2) en l'affichant dans une page puis en la capturant en JPEG. */
async function renderCrop(page: Page, crop: Crop): Promise<Buffer> {
  const [srcW, srcH] = crop.size
  const width = crop.width ?? Math.min(srcW, (srcH * 3) / 2)
  const height = (width * 2) / 3
  const [cx, cy] = crop.center ?? [srcW / 2, srcH / 2]
  const outW = 900
  const scale = outW / width
  const left = Math.max(0, Math.min(srcW - width, cx - width / 2)) * scale
  const top = Math.max(0, Math.min(srcH - height, cy - height / 2)) * scale
  const data = readFileSync(crop.file).toString('base64')
  const cropPage = await page.context().newPage()
  try {
    await cropPage.setViewportSize({ width: outW, height: 600 })
    await cropPage.setContent(
      `<body style="margin:0"><div style="width:${outW}px;height:600px;background:url(data:image/jpeg;base64,${data}) no-repeat;background-size:${srcW * scale}px ${srcH * scale}px;background-position:-${left}px -${top}px"></div></body>`,
    )
    await cropPage.waitForTimeout(200)
    return await cropPage.screenshot({ type: 'jpeg', quality: 88 })
  } finally {
    await cropPage.close()
  }
}

export async function seedDemoData(page: Page): Promise<DemoData> {
  const api = page.request
  await deleteIfExists(api, CAMILLE.email)
  await deleteIfExists(api, ALEX.email)

  // Une page sur l'origine de l'appli est nécessaire pour le fetch d'inscription.
  await page.goto('/recipes/random')
  await registerInBrowser(page, CAMILLE, 'vegetarian')
  await registerInBrowser(page, ALEX)

  const tokens = await obtainTokens(api, CAMILLE.email, DEMO_PASSWORD)
  if (!tokens) throw new Error('Could not log in as the demo user')
  const headers = { Authorization: `Bearer ${tokens.access}` }

  const ok = async <T>(responsePromise: ReturnType<APIRequestContext['get']>, what: string): Promise<T> => {
    const response = await responsePromise
    if (!response.ok()) throw new Error(`${what} failed: ${response.status()} ${await response.text()}`)
    return (await response.json()) as T
  }

  await ok(
    api.patch('/api/auth/me/', {
      headers,
      data: { allergies: ['gluten'], intolerances: ['lactose'], diet_type: 'vegetarian', activity_level: 'moderate' },
    }),
    'Profile update',
  )

  // Ingrédients du seed, résolus par nom exact.
  const ingredientIds = new Map<string, number>()
  const names = new Set(RECIPES.flatMap((recipe) => recipe.ingredients.map(([name]) => name)))
  names.add('Fécule de maïs')
  for (const name of names) {
    const data = await ok<{ results: Array<{ id: number; name: string }> }>(
      api.get('/api/ingredients/', { params: { search: name } }),
      `Ingredient search ${name}`,
    )
    const match = data.results.find((item) => item.name.toLowerCase() === name.toLowerCase())
    if (!match) throw new Error(`Seeded ingredient not found: ${name}`)
    ingredientIds.set(name, match.id)
  }

  const toPayload = (ingredients: DemoRecipe['ingredients']) =>
    ingredients.map(([name, quantity, unit], index) => ({
      ingredient_id: ingredientIds.get(name),
      quantity,
      unit,
      order: index + 1,
    }))

  const imageCache = new Map<DemoRecipe['image'], Buffer>()
  const uploadImage = async (recipeId: number, crop: Crop) => {
    let buffer = imageCache.get(crop)
    if (!buffer) {
      buffer = await renderCrop(page, crop)
      imageCache.set(crop, buffer)
    }
    await ok(
      api.patch(`/api/recipes/${recipeId}/image/`, {
        headers,
        multipart: {
          image: { name: `recipe-${recipeId}.jpg`, mimeType: 'image/jpeg', buffer },
          // Photos de démo générées synthétiquement (voir renderCrop) : domaine public, aucun
          // champ de crédit supplémentaire requis (voir apps/recipes/image_credit.py).
          image_license: 'public_domain',
        },
      }),
      'Image upload',
    )
  }

  // Variante sans gluten du gratin : farine remplacée par de la fécule de maïs.
  const createGlutenFreeFork = async (gratin: DemoRecipe) => {
    const fork = await ok<{ id: number }>(
      api.post(`/api/recipes/${recipes.gratin}/fork/`, { headers, data: { version_label: 'Gluten-free' } }),
      'Fork',
    )
    await ok(
      api.patch(`/api/recipes/${fork.id}/`, {
        headers,
        data: {
          description: 'The same gratin, with a cornflour béchamel so it is safe for gluten-free guests.',
          ingredients: toPayload(
            gratin.ingredients.map(
              ([name, qty, unit]) =>
                (name === 'Farine de blé' ? ['Fécule de maïs', 20, 'g'] : [name, qty, unit]) as [string, number, Unit],
            ),
          ),
          steps: gratin.steps
            .map((step) => step.replace('@Farine_de_blé', '@Fécule_de_maïs'))
            .map((instruction, index) => ({ order: index + 1, instruction: closeMentions(instruction) })),
        },
      }),
      'Fork update',
    )
    await uploadImage(fork.id, gratin.image)
    return fork.id
  }

  const recipes: Record<string, number> = {}
  let forkId = 0
  for (const recipe of RECIPES) {
    const created = await ok<{ id: number }>(
      api.post('/api/recipes/', {
        headers,
        data: {
          title: recipe.title,
          description: recipe.description,
          servings: recipe.servings,
          prep_time_minutes: recipe.prep,
          cook_time_minutes: recipe.cook,
          diet_type: recipe.diet,
          is_public: true,
          ingredients: toPayload(recipe.ingredients),
          steps: recipe.steps.map((instruction, index) => ({
            order: index + 1,
            instruction: closeMentions(instruction),
          })),
        },
      }),
      `Recipe ${recipe.title}`,
    )
    recipes[recipe.key] = created.id
    await uploadImage(created.id, recipe.image)
    // Créée juste après l'original pour que les recettes les plus récentes (carrousel de
    // l'accueil) soient les autres recettes de démo.
    if (recipe.key === 'gratin') forkId = await createGlutenFreeFork(recipe)
  }

  // Commentaires signés d'autres prénoms (postés avec le jeton de Camille : l'API limite
  // fortement les commentaires anonymes, ce qui ferait échouer des exécutions rapprochées).
  for (const [author_name, body] of [
    ['Léa', 'Made this for a family dinner — everyone asked for seconds! I added a little thyme on top.'],
    ['Marc', 'Great with a green salad. It reheats perfectly for lunch the next day.'],
  ]) {
    await ok(api.post(`/api/recipes/${recipes.gratin}/comments/`, { headers, data: { author_name, body } }), 'Comment')
  }

  // Planning de la semaine en cours (lundi → dimanche), plus demain s'il tombe la semaine suivante.
  const weekStart = startOfWeek()
  const plan: Array<[number, 'breakfast' | 'lunch' | 'dinner', string]> = []
  const breakfasts = ['toast', null, 'toast', null, 'toast', null, 'toast']
  const lunches = ['bowl', 'soup', 'carrots', 'ratatouille', 'soup', 'bowl', 'curry']
  const dinners = ['curry', 'ratatouille', 'gratin', 'carrots', 'curry', 'gratin', 'ratatouille']
  for (let day = 0; day < 7; day++) {
    if (breakfasts[day]) plan.push([day, 'breakfast', breakfasts[day]!])
    plan.push([day, 'lunch', lunches[day]])
    plan.push([day, 'dinner', dinners[day]])
  }
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const tomorrowOffset = Math.round((addDays(today, 1).getTime() - weekStart.getTime()) / 86_400_000)
  if (tomorrowOffset >= 7) {
    plan.push([tomorrowOffset, 'lunch', 'soup'], [tomorrowOffset, 'dinner', 'bowl'])
  }

  const entryIds: number[] = []
  for (const [day, meal, key] of plan) {
    const entry = await ok<{ id: number }>(
      api.post('/api/meal-plan-entries/', {
        headers,
        data: { recipe: recipes[key], date: isoDate(addDays(weekStart, day)), meal_type: meal, servings: 2 },
      }),
      'Meal plan entry',
    )
    if (day < 7) entryIds.push(entry.id)
  }

  // Deux listes : une ancienne (plus courte) puis celle de la semaine, cochée en partie.
  await ok(
    api.post('/api/shopping-lists/', {
      headers,
      data: { meal_plan_entry_ids: entryIds.slice(0, 4), name: 'Weekend market' },
    }),
    'Shopping list',
  )
  const list = await ok<{ id: number; items: Array<{ ingredient: { id: number; name: string } }> }>(
    api.post('/api/shopping-lists/', {
      headers,
      data: { meal_plan_entry_ids: entryIds, name: 'Groceries for the week' },
    }),
    'Shopping list',
  )
  const owned = ['Sel', "Huile d'olive", 'Cumin', 'Ail', 'Curcuma']
    .map((name) => ingredientIds.get(name))
    .filter((id): id is number => id !== undefined)
  await ok(
    api.post(`/api/shopping-lists/${list.id}/mark_owned/`, { headers, data: { ingredient_ids: owned } }),
    'Mark owned',
  )

  // Agenda partagé (lecture seule) avec Alex.
  await ok(api.post('/api/planning-shares/', { headers, data: { email: ALEX.email, permission: 'read' } }), 'Share')

  return {
    camilleToken: tokens.access,
    camilleRefresh: tokens.refresh,
    recipes,
    forkId,
    shoppingListId: list.id,
    weekStart,
  }
}
