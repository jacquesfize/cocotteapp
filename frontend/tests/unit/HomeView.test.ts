import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/recipes', () => ({
  listRecipes: vi.fn(),
}))
vi.mock('../../src/api/thematicPages', () => ({
  listThematicPages: vi.fn(),
}))

import { listRecipes } from '../../src/api/recipes'
import { listThematicPages } from '../../src/api/thematicPages'
import BaseModal from '../../src/components/BaseModal.vue'
import HomeView from '../../src/views/HomeView.vue'
import { useAuthStore } from '../../src/stores/auth'
import type { Recipe } from '../../src/types/models'

async function mountHome() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', name: 'home', component: HomeView },
      { path: '/recipes', name: 'recipes', component: { template: '<div />' } },
      { path: '/recipes/random', name: 'recipe-random', component: { template: '<div />' } },
      { path: '/recipes/new', name: 'recipe-new', component: { template: '<div />' } },
    ],
  })
  router.push('/')
  await router.isReady()

  return mount(HomeView, {
    global: {
      plugins: [i18n, router],
      stubs: {
        RouterLink: { props: ['to'], template: '<a :data-to="JSON.stringify(to)"><slot /></a>' },
        HomeWeekStrip: { template: '<div class="stub-week-strip" />' },
        RecipeCard: { props: ['recipe'], template: '<div class="stub-recipe-card">{{ recipe.title }}</div>' },
      },
    },
  })
}

function recipe(id: number): Recipe {
  return {
    id,
    title: `Recette ${id}`,
    diet_type: 'omnivore',
    total_time_minutes: 20,
    description: '',
  } as Recipe
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('HomeView', () => {
  it('shows the hero recipe, a dot per latest recipe, and thematic pages as links to filtered lists', async () => {
    vi.mocked(listRecipes).mockImplementation(async (params) => ({
      results: params?.in_season ? [] : Array.from({ length: 8 }, (_, i) => recipe(i + 1)),
      count: 8,
      next: null,
      previous: null,
    }))
    vi.mocked(listThematicPages).mockResolvedValue([
      {
        id: 1,
        title: 'Produits de saison',
        slug: 'produits-de-saison',
        icon: '🌱',
        image: null,
        description: 'En ce moment.',
        filters: { in_season: 'true' },
        order: 0,
      },
    ])

    const wrapper = await mountHome()
    await flushPromises()

    // Only the first 5 of the 8 returned recipes are reachable from the hero/dots.
    expect(wrapper.find('.hero-title').text()).toBe('Recette 1')
    expect(wrapper.findAll('.hero-dot')).toHaveLength(5)
    expect(wrapper.text()).toContain('Produits de saison')

    const thematicLink = wrapper.findAll('a').find((a) => a.text().includes('Produits de saison'))
    expect(JSON.parse(thematicLink?.attributes('data-to') ?? '{}')).toEqual({
      name: 'recipes',
      query: { in_season: 'true' },
    })
  })

  it('switches the hero to the picked recipe when a dot is clicked', async () => {
    vi.mocked(listRecipes).mockImplementation(async (params) => ({
      results: params?.in_season ? [] : [recipe(1), recipe(2), recipe(3)],
      count: 3,
      next: null,
      previous: null,
    }))
    vi.mocked(listThematicPages).mockResolvedValue([])

    const wrapper = await mountHome()
    await flushPromises()

    expect(wrapper.find('.hero-title').text()).toBe('Recette 1')

    await wrapper.findAll('.hero-dot')[2].trigger('click')

    expect(wrapper.find('.hero-title').text()).toBe('Recette 3')
    expect(wrapper.findAll('.hero-dot')[2].classes()).toContain('active')
  })

  it('auto-advances the hero through the latest recipes on a timer', async () => {
    vi.useFakeTimers()
    try {
      vi.mocked(listRecipes).mockImplementation(async (params) => ({
        results: params?.in_season ? [] : [recipe(1), recipe(2), recipe(3)],
        count: 3,
        next: null,
        previous: null,
      }))
      vi.mocked(listThematicPages).mockResolvedValue([])

      const wrapper = await mountHome()
      await flushPromises()

      expect(wrapper.find('.hero-title').text()).toBe('Recette 1')

      await vi.advanceTimersByTimeAsync(6000)
      expect(wrapper.find('.hero-title').text()).toBe('Recette 2')

      await vi.advanceTimersByTimeAsync(6000)
      expect(wrapper.find('.hero-title').text()).toBe('Recette 3')

      // Wraps back around to the first recipe.
      await vi.advanceTimersByTimeAsync(6000)
      expect(wrapper.find('.hero-title').text()).toBe('Recette 1')
    } finally {
      vi.useRealTimers()
    }
  })

  it('shows a message when there are no recipes or thematic pages yet', async () => {
    vi.mocked(listRecipes).mockResolvedValue({ results: [], count: 0, next: null, previous: null })
    vi.mocked(listThematicPages).mockResolvedValue([])

    const wrapper = await mountHome()
    await flushPromises()

    expect(wrapper.find('.hero-title').exists()).toBe(false)
    expect(wrapper.find('.thematic-avatar').exists()).toBe(false)
    expect(wrapper.text()).toContain("Aucune recette pour l'instant.")
    expect(wrapper.text()).not.toContain('De saison en ce moment')
  })

  it('shows an in-season row without repeating recipes already reachable from the hero/dots', async () => {
    vi.mocked(listRecipes).mockImplementation(async (params) => ({
      results: params?.in_season ? [recipe(1), recipe(9)] : [recipe(1), recipe(2)],
      count: 2,
      next: null,
      previous: null,
    }))
    vi.mocked(listThematicPages).mockResolvedValue([])

    const wrapper = await mountHome()
    await flushPromises()

    expect(wrapper.text()).toContain('De saison en ce moment')
    expect(wrapper.find('.hero-title').text()).toBe('Recette 1')
    expect(wrapper.findAll('.hero-dot')).toHaveLength(2)
    expect(wrapper.findAll('.stub-recipe-card').map((c) => c.text())).toEqual(['Recette 9'])
  })

  it('shows an error message when recipes cannot be loaded', async () => {
    vi.mocked(listRecipes).mockRejectedValue(new Error('boom'))
    vi.mocked(listThematicPages).mockResolvedValue([])

    const wrapper = await mountHome()
    await flushPromises()

    expect(wrapper.text()).toContain('Impossible de charger les recettes.')
  })

  it('opens the import-from-URL modal when the week strip asks to', async () => {
    vi.mocked(listRecipes).mockResolvedValue({ results: [], count: 0, next: null, previous: null })
    vi.mocked(listThematicPages).mockResolvedValue([])
    useAuthStore().accessToken = 'test-token'

    const wrapper = await mountHome()
    await flushPromises()

    expect(wrapper.findComponent(BaseModal).exists()).toBe(false)

    const weekStripStub = wrapper.findComponent('.stub-week-strip')
    expect(weekStripStub.exists()).toBe(true)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    await (weekStripStub as any).vm.$emit('open-import')
    await wrapper.vm.$nextTick()

    expect(wrapper.findComponent(BaseModal).exists()).toBe(true)
  })
})
