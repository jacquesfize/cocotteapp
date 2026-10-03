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
vi.mock('../../src/api/importer', () => ({ suggestFreeImages: vi.fn() }))
vi.mock('../../src/api/allergens', () => ({ listAllergens: vi.fn().mockResolvedValue([]) }))
vi.mock('../../src/api/ingredients', () => ({
  listIngredients: vi.fn().mockResolvedValue({ results: [], count: 0, next: null, previous: null }),
  createIngredient: vi.fn(),
}))

import { suggestFreeImages } from '../../src/api/importer'
import { createRecipe, importRecipeFromCooklang } from '../../src/api/recipes'
import { setPendingImportDraft } from '../../src/utils/pendingImportDraft'
import RecipeFormView from '../../src/views/recipes/RecipeFormView.vue'
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

  it('leaves title and servings to the Cooklang metadata when left empty', async () => {
    vi.mocked(importRecipeFromCooklang).mockResolvedValue(recipe())
    const text = '---\ntitle: Tiramisu\nservings: 6\n---\nRør @mascarpone{500%g}.'

    const wrapper = await mountRecipeForm()
    await wrapper.findAll('button[role="tab"]')[1].trigger('click')
    await wrapper.find('#cooklang-text').setValue(text)
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(importRecipeFromCooklang).toHaveBeenCalledWith({ raw_cooklang: text })
  })

  it('explains a 400 (unreadable text or missing title)', async () => {
    vi.mocked(importRecipeFromCooklang).mockRejectedValue({ response: { status: 400 } })

    const wrapper = await mountRecipeForm()
    await wrapper.findAll('button[role="tab"]')[1].trigger('click')
    await wrapper.find('#cooklang-text').setValue('Ajouter @sel.')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(wrapper.text()).toContain('Texte Cooklang illisible')
  })
})

function importDraft() {
  setPendingImportDraft({
    title: 'Tarte aux poireaux',
    servings: 4,
    cook_time_minutes: 30,
    source_url: 'https://cuisine.example/tarte',
    steps: [{ order: 1, instruction: 'Émincer les poireaux.' }],
    ingredients: [
      { ingredient: { id: 7, name: 'poireau' } as never, quantity: '2', unit: 'piece', raw_line: '2 poireaux' },
    ],
  })
}

describe('RecipeFormView - imported recipe copyright', () => {
  it('never pre-fills the source website photo', async () => {
    importDraft()
    const wrapper = await mountRecipeForm()
    await flushPromises()

    expect((wrapper.find('input[type="url"]').element as HTMLInputElement).value).toBe('')
    expect((wrapper.find('#source_url').element as HTMLInputElement).value).toBe('https://cuisine.example/tarte')
  })

  it('shows the copyright notice once the make-public box is checked', async () => {
    importDraft()
    const wrapper = await mountRecipeForm()
    await flushPromises()

    expect(wrapper.find('.copyright-notice').exists()).toBe(false)
    await wrapper.find('.checkbox-field input').setValue(true)

    const notice = wrapper.find('.copyright-notice')
    expect(notice.exists()).toBe(true)
    expect(notice.text()).toContain('ne sont pas protégés par le droit d\'auteur')
  })

  it('refuses to make the recipe public while a step is still the imported text', async () => {
    importDraft()
    const wrapper = await mountRecipeForm()
    await flushPromises()

    await wrapper.find('.checkbox-field input').setValue(true)
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createRecipe).not.toHaveBeenCalled()
    expect(wrapper.find('.error').text()).toContain('Réécrivez-les')
  })

  it('saves a rewritten imported recipe as public', async () => {
    importDraft()
    vi.mocked(createRecipe).mockResolvedValue(recipe({ steps: [] }))
    const wrapper = await mountRecipeForm()
    await flushPromises()

    await wrapper.find('.checkbox-field input').setValue(true)
    await wrapper.findComponent({ name: 'CooklangStepInput' }).vm.$emit('update:modelValue', 'Couper les poireaux en rondelles.')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createRecipe).toHaveBeenCalledWith(
      expect.objectContaining({
        content_publicly_licensed: true,
        steps: [expect.objectContaining({ instruction: 'Couper les poireaux en rondelles.' })],
      }),
    )
  })

  it('fills the image and its credit from a free image suggestion', async () => {
    vi.mocked(suggestFreeImages).mockResolvedValue([
      {
        url: 'https://upload.wikimedia.org/tarte.jpg',
        thumbnail: 'https://api.openverse.org/thumb/1/',
        title: 'Tarte',
        image_license: 'cc_by',
        image_credit_author: 'Alice',
        image_credit_source_url: 'https://commons.wikimedia.org/wiki/File:Tarte.jpg',
        image_credit_license_url: 'https://creativecommons.org/licenses/by/4.0/',
      },
    ])
    importDraft()
    const wrapper = await mountRecipeForm()
    await flushPromises()

    await wrapper.find('.free-images-button').trigger('click')
    await flushPromises()
    expect(suggestFreeImages).toHaveBeenCalledWith('Tarte aux poireaux')

    await wrapper.find('.free-image').trigger('click')
    await flushPromises()

    expect(wrapper.find('.free-image').exists()).toBe(false)
    expect((wrapper.find('input[type="url"]').element as HTMLInputElement).value).toBe(
      'https://upload.wikimedia.org/tarte.jpg',
    )
    expect((wrapper.find('select[id^="iuwc-license"]').element as HTMLSelectElement).value).toBe('cc_by')
  })
})
