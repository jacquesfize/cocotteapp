import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/importer', () => ({
  previewImportFromUrl: vi.fn(),
}))
vi.mock('../../src/api/recipes', () => ({
  listRecipes: vi.fn().mockResolvedValue({ results: [], count: 0, next: null, previous: null }),
}))

import { previewImportFromUrl } from '../../src/api/importer'
import RecipeListView from '../../src/views/RecipeListView.vue'
import { listRecipes } from '../../src/api/recipes'
import { useAuthStore } from '../../src/stores/auth'
import { takePendingImportDraft } from '../../src/utils/pendingImportDraft'
import type { ImportPreview, User } from '../../src/types/models'

function preview(overrides?: Partial<ImportPreview>): ImportPreview {
  return {
    title: 'Falafels',
    servings: 4,
    cook_time_minutes: 20,
    image_url: '',
    source_url: 'https://example.com/falafels',
    steps: [{ order: 1, instruction: 'Mixer.' }],
    ingredients: [
      { raw_line: '200 g de pois chiches', quantity: '200', unit: 'g', name: 'pois chiches', ingredient: null },
      { raw_line: 'sel', quantity: '1', unit: 'piece', name: 'sel', ingredient: null },
    ],
    ...overrides,
  }
}

async function mountList() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/recipes', name: 'recipes', component: RecipeListView },
      { path: '/recipes/new', name: 'recipe-new', component: { template: '<div />' } },
    ],
  })
  router.push('/recipes')
  await router.isReady()

  const wrapper = mount(RecipeListView, { global: { plugins: [i18n, router] } })
  await flushPromises()

  const authStore = useAuthStore()
  authStore.user = { id: 1, username: 'alice' } as unknown as User
  authStore.accessToken = 'test-token'
  await flushPromises()

  return { wrapper, router }
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('RecipeListView import', () => {
  it('previews the URL, stores the draft (including unmatched raw text) and navigates to recipe-new', async () => {
    vi.mocked(previewImportFromUrl).mockResolvedValue(preview())

    const { wrapper, router } = await mountList()
    const pushSpy = vi.spyOn(router, 'push')

    await wrapper.find('button[aria-controls="import-form"]').trigger('click')
    await wrapper.find('#import-url').setValue('https://example.com/falafels')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(previewImportFromUrl).toHaveBeenCalledWith('https://example.com/falafels')
    expect(pushSpy).toHaveBeenCalledWith({ name: 'recipe-new' })

    const draft = takePendingImportDraft()
    expect(draft?.title).toBe('Falafels')
    expect(draft?.ingredients[1]).toEqual({ ingredient: null, quantity: '1', unit: 'piece', raw_line: 'sel' })
  })

  it('shows an error message when the scrape fails', async () => {
    vi.mocked(previewImportFromUrl).mockRejectedValue(new Error('boom'))

    const { wrapper } = await mountList()

    await wrapper.find('button[aria-controls="import-form"]').trigger('click')
    await wrapper.find('#import-url').setValue('https://example.com/unsupported')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(wrapper.text()).toContain("Impossible de récupérer cette recette")
  })
})

describe('RecipeListView filters', () => {
  it('initialises filters and the badge from the URL query, and syncs edits back to it', async () => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/recipes', name: 'recipes', component: RecipeListView }],
    })
    router.push('/recipes?in_season=true&ingredients=Tomate')
    await router.isReady()
    const wrapper = mount(RecipeListView, { global: { plugins: [i18n, router] } })
    await flushPromises()

    expect(wrapper.find('[data-testid="filters-badge"]').text()).toBe('2')

    vi.useFakeTimers()
    await wrapper.find('button.toggle').trigger('click')
    await wrapper.find('#search').setValue('tarte')
    await vi.advanceTimersByTimeAsync(400)
    vi.useRealTimers()
    await flushPromises()

    expect(router.currentRoute.value.query.search).toBe('tarte')
    expect(wrapper.find('[data-testid="filters-badge"]').text()).toBe('3')
  })

  it('hides recipes with the profile allergens by default, and the checkbox turns it off', async () => {
    useAuthStore().user = { allergies: ['peanut'], intolerances: ['lactose'] } as unknown as User
    const router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/recipes', name: 'recipes', component: RecipeListView }],
    })
    router.push('/recipes')
    await router.isReady()
    const wrapper = mount(RecipeListView, { global: { plugins: [i18n, router] } })
    await flushPromises()

    expect(listRecipes).toHaveBeenLastCalledWith({ exclude_allergens: 'peanut,lactose' })

    vi.useFakeTimers()
    await wrapper.find('#hide_allergens').setValue(false)
    await vi.advanceTimersByTimeAsync(400)
    vi.useRealTimers()
    await flushPromises()

    expect(listRecipes).toHaveBeenLastCalledWith({})
  })
})
