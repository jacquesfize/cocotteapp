import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/recipes', () => ({
  getRecipe: vi.fn(),
  deleteRecipe: vi.fn(),
  forkRecipe: vi.fn(),
  downloadRecipePdf: vi.fn(),
  getRecipeNutrition: vi.fn().mockResolvedValue({ per_serving: null }),
}))

import { forkRecipe, getRecipe } from '../../src/api/recipes'
import { useAuthStore } from '../../src/stores/auth'
import RecipeDetailView from '../../src/views/RecipeDetailView.vue'
import type { Recipe, User } from '../../src/types/models'

function baseRecipe(overrides: Partial<Recipe> = {}): Recipe {
  return {
    id: 1,
    title: 'Curry de légumes',
    slug: 'curry-de-legumes',
    description: '',
    author: 'chef',
    author_id: 42,
    servings: 4,
    prep_time_minutes: 10,
    cook_time_minutes: 20,
    total_time_minutes: 30,
    diet_type: 'omnivore',
    source_type: 'manual',
    source_url: '',
    video_url: '',
    youtube_id: null,
    image: '',
    image_url: '',
    is_public: true,
    tags: [],
    ingredients: [],
    steps: [],
    root_recipe: null,
    version_label: '',
    versions: [],
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
    ...overrides,
  } as Recipe
}

async function mountDetail(id: number | string = 1) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/recipes/:id', name: 'recipe-detail', component: RecipeDetailView, props: true },
      { path: '/recipes/:id/edit', name: 'recipe-edit', component: { template: '<div />' } },
      { path: '/recipes', name: 'recipes', component: { template: '<div />' } },
    ],
  })
  router.push(`/recipes/${id}`)
  await router.isReady()

  const wrapper = mount(RecipeDetailView, {
    props: { id },
    global: {
      plugins: [i18n, router],
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
        AddToPlanForm: true,
      },
    },
  })
  await flushPromises()
  return { wrapper, router }
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('RecipeDetailView versioning', () => {
  it('shows the create-variant button to any authenticated user, not just the author', async () => {
    const authStore = useAuthStore()
    authStore.user = { id: 99, username: 'someoneelse' } as unknown as User
    authStore.accessToken = 'test-token'

    vi.mocked(getRecipe).mockResolvedValue(baseRecipe())

    const { wrapper } = await mountDetail()

    const forkButton = wrapper.findAll('button').find((b) => b.text().includes('Créer une variante'))
    expect(forkButton?.exists()).toBe(true)
    expect(wrapper.find('button.danger').exists()).toBe(false)
  })

  it('forks the recipe and navigates to the edit route for the new version', async () => {
    const authStore = useAuthStore()
    authStore.user = { id: 99, username: 'someoneelse' } as unknown as User
    authStore.accessToken = 'test-token'

    vi.mocked(getRecipe).mockResolvedValue(baseRecipe())
    vi.mocked(forkRecipe).mockResolvedValue(baseRecipe({ id: 55, version_label: 'Sans gluten' }))

    const { wrapper, router } = await mountDetail()

    const forkButton = wrapper.findAll('button').find((b) => b.text().includes('Créer une variante'))
    await forkButton?.trigger('click')

    const input = wrapper.find('input[type="text"]')
    await input.setValue('Sans gluten')

    const confirmButton = wrapper.findAll('button').find((b) => b.text() === 'Valider')
    await confirmButton?.trigger('click')
    await flushPromises()

    expect(forkRecipe).toHaveBeenCalledWith(1, 'Sans gluten')
    expect(router.currentRoute.value.fullPath).toBe('/recipes/55/edit')
  })

  it('lists other versions of the recipe when present', async () => {
    vi.mocked(getRecipe).mockResolvedValue(
      baseRecipe({
        versions: [
          { id: 2, slug: 'curry-epice', title: 'Curry épicé', version_label: 'Épicée', author: 'bob' },
          { id: 3, slug: 'curry-de-legumes', title: 'Curry de légumes', version_label: '', author: 'chef' },
        ],
      }),
    )

    const { wrapper } = await mountDetail()

    expect(wrapper.text()).toContain('Autres versions de cette recette')
    expect(wrapper.text()).toContain('Épicée')
    expect(wrapper.text()).toContain('bob')
    expect(wrapper.text()).toContain('Originale')
  })

  it('does not show a versions section when there are no other versions', async () => {
    vi.mocked(getRecipe).mockResolvedValue(baseRecipe({ versions: [] }))

    const { wrapper } = await mountDetail()

    expect(wrapper.text()).not.toContain('Autres versions de cette recette')
  })
})
