import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/recipes', () => ({
  createRecipe: vi.fn(),
  getRecipe: vi.fn(),
  updateRecipe: vi.fn(),
  uploadRecipeImage: vi.fn(),
  importRecipeFromCooklang: vi.fn(),
}))
vi.mock('../../src/api/allergens', () => ({ listAllergens: vi.fn().mockResolvedValue([]) }))
vi.mock('../../src/api/ingredients', () => ({
  listIngredients: vi.fn().mockResolvedValue({ results: [], count: 0, next: null, previous: null }),
  createIngredient: vi.fn(),
}))

import { importRecipeFromCooklang } from '../../src/api/recipes'
import RecipeFormView from '../../src/views/RecipeFormView.vue'
import type { Recipe } from '../../src/types/models'

async function mountRecipeForm() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/recipes/new', name: 'recipe-new', component: RecipeFormView },
      { path: '/recipes/:id/edit', name: 'recipe-edit', component: RecipeFormView, props: true },
      { path: '/recipes/:id', name: 'recipe-detail', component: { template: '<div />' } },
    ],
  })
  router.push('/recipes/new')
  await router.isReady()

  return mount(RecipeFormView, {
    global: {
      plugins: [i18n, router],
    },
  })
}

function recipe(overrides?: Partial<Recipe>): Recipe {
  return {
    id: 42,
    title: 'Curry rapide',
    slug: 'curry-rapide',
    description: '',
    author: 'alice',
    author_id: 1,
    servings: 2,
    prep_time_minutes: 0,
    cook_time_minutes: 0,
    total_time_minutes: 0,
    diet_type: 'omnivore',
    source_type: 'cooklang',
    source_url: '',
    video_url: '',
    youtube_id: null,
    image: '',
    image_url: '',
    is_public: true,
    tags: [],
    ingredients: [],
    steps: [],
    created_at: '',
    updated_at: '',
    ...overrides,
  } as unknown as Recipe
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('RecipeFormView - Cooklang import mode', () => {
  it('shows the manual/cooklang mode toggle only when creating a recipe', async () => {
    const wrapper = await mountRecipeForm()
    expect(wrapper.text()).toContain('Saisie manuelle')
    expect(wrapper.text()).toContain('Coller du Cooklang')
  })

  it('switches to the Cooklang form and imports it on submit', async () => {
    vi.mocked(importRecipeFromCooklang).mockResolvedValue(recipe())

    const wrapper = await mountRecipeForm()
    const tabs = wrapper.findAll('button[role="tab"]')
    await tabs[1].trigger('click')

    expect(wrapper.find('#cooklang-text').exists()).toBe(true)

    await wrapper.find('#cooklang-title').setValue('Curry rapide')
    await wrapper.find('#cooklang-servings').setValue(2)
    await wrapper
      .find('#cooklang-text')
      .setValue('Faire revenir @oignon{1%piece} dans @huile_olive{2%cs}.')

    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(importRecipeFromCooklang).toHaveBeenCalledWith({
      title: 'Curry rapide',
      servings: 2,
      raw_cooklang: 'Faire revenir @oignon{1%piece} dans @huile_olive{2%cs}.',
    })
    expect(wrapper.vm.$route.fullPath).toBe('/recipes/42/edit')
  })

  it('shows an error message when the import fails', async () => {
    vi.mocked(importRecipeFromCooklang).mockRejectedValue(new Error('boom'))

    const wrapper = await mountRecipeForm()
    const tabs = wrapper.findAll('button[role="tab"]')
    await tabs[1].trigger('click')

    await wrapper.find('#cooklang-title').setValue('Curry rapide')
    await wrapper.find('#cooklang-text').setValue('Faire revenir @oignon{1%piece}.')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(wrapper.text()).toContain("Échec de l'import du texte Cooklang.")
  })
})
