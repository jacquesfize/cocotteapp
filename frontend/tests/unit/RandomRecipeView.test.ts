import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/recipes', () => ({
  getRandomRecipe: vi.fn(),
  downloadRecipePdf: vi.fn(),
  getRecipeNutrition: vi.fn().mockResolvedValue({ per_serving: null }),
}))
vi.mock('../../src/api/allergens', () => ({
  listAllergens: vi.fn().mockResolvedValue([
    { slug: 'gluten', name: 'Gluten' },
    { slug: 'peanut', name: 'Arachide' },
    { slug: 'lactose', name: 'Lactose' },
  ]),
}))

import { getRandomRecipe } from '../../src/api/recipes'
import RandomRecipeView from '../../src/views/recipes/RandomRecipeView.vue'
import { useAuthStore } from '../../src/stores/auth'
import type { Recipe, User } from '../../src/types/models'

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
  vi.mocked(getRandomRecipe).mockResolvedValue({
    id: 1,
    title: 'Soupe',
    diet_type: 'omnivore',
    total_time_minutes: 20,
    source_url: '',
    image_url: '',
    allergens: [],
    content_restricted: true,
    carbon_footprint_kg_co2e: 0.1,
  } as unknown as Recipe)
})

function mountView() {
  return mount(RandomRecipeView, {
    global: {
      plugins: [i18n],
      stubs: { RouterLink: { template: '<a><slot /></a>' }, AddToPlanForm: true },
    },
  })
}

describe('RandomRecipeView', () => {
  it('renders a restricted recipe (no ingredients/steps in the payload) with the restricted notice', async () => {
    // Forme renvoyée par l'API pour une recette importée par un autre utilisateur.
    vi.mocked(getRandomRecipe).mockResolvedValue({
      id: 13,
      title: 'Cinnamon rolls',
      diet_type: 'omnivore',
      total_time_minutes: 60,
      source_url: 'https://example.com/rolls',
      image_url: '',
      allergens: [],
      content_restricted: true,
      carbon_footprint_kg_co2e: 0.8,
    } as unknown as Recipe)

    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('h2').text()).toBe('Cinnamon rolls')
    expect(wrapper.find('.restricted-notice').exists()).toBe(true)
  })

  it('keeps the filters panel hidden by default, with no badge', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('#random-filters-panel').isVisible()).toBe(false)
    expect(wrapper.find('button.toggle').attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('[data-testid="filters-badge"]').exists()).toBe(false)
  })

  it('shows the filters panel when the toggle button next to "Une autre" is clicked', async () => {
    const wrapper = mountView()
    await flushPromises()

    const buttons = wrapper.findAll('.header-actions button')
    expect(buttons).toHaveLength(2)
    expect(buttons[1].attributes('aria-controls')).toBe('random-filters-panel')

    await buttons[1].trigger('click')

    expect(wrapper.find('#random-filters-panel').isVisible()).toBe(true)
    expect(wrapper.find('button.toggle').attributes('aria-expanded')).toBe('true')
  })

  it("pre-fills the allergen exclusion filter from the user's own allergies and intolerances", async () => {
    useAuthStore().user = { allergies: ['peanut'], intolerances: ['lactose'] } as unknown as User

    const wrapper = mountView()
    await flushPromises()

    expect(getRandomRecipe).toHaveBeenCalledWith({ exclude_allergens: 'peanut,lactose' })

    await wrapper.find('button.toggle').trigger('click')
    expect(wrapper.find('[data-testid="filters-badge"]').text()).toBe('1')

    const options = wrapper.find('#random-exclude-allergens').findAll('option')
    const selected = options.filter((o) => (o.element as HTMLOptionElement).selected).map((o) => o.element.value)
    expect(selected.sort()).toEqual(['lactose', 'peanut'])
  })

  it('draw() passes exclude_allergens through to getRandomRecipe when filters are set', async () => {
    useAuthStore().user = { allergies: [], intolerances: [] } as unknown as User

    const wrapper = mountView()
    await flushPromises()
    expect(getRandomRecipe).toHaveBeenLastCalledWith({})

    await wrapper.find('button.toggle').trigger('click')
    await wrapper.find('#random-exclude-allergens').setValue(['gluten'])
    await flushPromises()

    expect(getRandomRecipe).toHaveBeenLastCalledWith({ exclude_allergens: 'gluten' })
  })
})
