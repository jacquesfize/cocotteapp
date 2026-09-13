import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/recipes', () => ({
  listRecipes: vi.fn(),
}))
vi.mock('../../src/api/thematicPages', () => ({
  listThematicPages: vi.fn(),
}))

import { listRecipes } from '../../src/api/recipes'
import { listThematicPages } from '../../src/api/thematicPages'
import HomeView from '../../src/views/HomeView.vue'
import type { Recipe } from '../../src/types/models'

function mountHome() {
  return mount(HomeView, {
    global: {
      plugins: [i18n],
      stubs: {
        RouterLink: { props: ['to'], template: '<a :data-to="JSON.stringify(to)"><slot /></a>' },
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
  vi.clearAllMocks()
})

describe('HomeView', () => {
  it('shows only the 6 latest recipes and the thematic pages as links to filtered lists', async () => {
    vi.mocked(listRecipes).mockResolvedValue({
      results: Array.from({ length: 8 }, (_, i) => recipe(i + 1)),
      count: 8,
      next: null,
      previous: null,
    })
    vi.mocked(listThematicPages).mockResolvedValue([
      {
        id: 1,
        title: 'Produits de saison',
        slug: 'produits-de-saison',
        icon: '🌱',
        description: 'En ce moment.',
        filters: { in_season: 'true' },
        order: 0,
      },
    ])

    const wrapper = mountHome()
    await flushPromises()

    expect(wrapper.findAll('.stub-recipe-card')).toHaveLength(6)
    expect(wrapper.text()).toContain('Produits de saison')

    const thematicLink = wrapper.findAll('a').find((a) => a.text().includes('Produits de saison'))
    expect(JSON.parse(thematicLink?.attributes('data-to') ?? '{}')).toEqual({
      name: 'recipes',
      query: { in_season: 'true' },
    })
  })

  it('shows a message when there are no recipes or thematic pages yet', async () => {
    vi.mocked(listRecipes).mockResolvedValue({ results: [], count: 0, next: null, previous: null })
    vi.mocked(listThematicPages).mockResolvedValue([])

    const wrapper = mountHome()
    await flushPromises()

    expect(wrapper.find('.stub-recipe-card').exists()).toBe(false)
    expect(wrapper.find('.thematic-card').exists()).toBe(false)
    expect(wrapper.text()).toContain("Aucune recette pour l'instant.")
  })
})
