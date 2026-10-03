import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi, type MockInstance } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/recipes', () => ({
  getRandomRecipe: vi.fn(),
}))
vi.mock('../../src/api/ingredients', () => ({
  listIngredients: vi.fn().mockResolvedValue({ results: [] }),
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
      stubs: { RouterLink: { template: '<a><slot /></a>' } },
    },
  })
}

// Le tirage attend la fin de l'animation du dé (setTimeout) : on avance le temps à la main.
async function roll(wrapper: VueWrapper, selector = 'button.dice') {
  await wrapper.find(selector).trigger('click')
  await vi.runAllTimersAsync()
  await flushPromises()
}

describe('RandomRecipeView', () => {
  let getContextSpy: MockInstance

  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['setTimeout'] })
    // jsdom n'implémente pas le canvas : le dé reste simplement non dessiné.
    getContextSpy = vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(null)
  })

  afterEach(() => {
    vi.useRealTimers()
    getContextSpy.mockRestore()
  })

  it('shows only the big dice on arrival, without drawing a recipe yet', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(getRandomRecipe).not.toHaveBeenCalled()
    expect(wrapper.find('.dice-stage button.dice.large').attributes('aria-label')).toBe('Lancer le dé')
    expect(wrapper.find('.dice-stage').text()).toContain('Lancez le dé pour tirer une recette au hasard')
    expect(wrapper.find('.recipe-card').exists()).toBe(false)
  })

  it('rolling the dice shows the drawn recipe as a card, with a smaller dice below to reroll', async () => {
    const wrapper = mountView()
    await flushPromises()
    await roll(wrapper)

    expect(getRandomRecipe).toHaveBeenCalledTimes(1)
    expect(wrapper.find('.dice-stage').exists()).toBe(false)
    expect(wrapper.find('.recipe-card.feature h3').text()).toBe('Soupe')
    const small = wrapper.find('.reroll button.dice.small')
    expect(small.attributes('aria-label')).toBe('Une autre')

    vi.mocked(getRandomRecipe).mockResolvedValue({
      id: 2,
      title: 'Gratin',
      diet_type: 'vegetarian',
      total_time_minutes: 45,
      allergens: [],
    } as unknown as Recipe)
    await roll(wrapper, '.reroll button.dice')

    expect(getRandomRecipe).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.recipe-card.feature h3').text()).toBe('Gratin')
  })

  it('renders a restricted recipe (no ingredients/steps in the payload) as a card', async () => {
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
    await roll(wrapper)

    expect(wrapper.find('.recipe-card.feature h3').text()).toBe('Cinnamon rolls')
    expect(wrapper.find('.restricted-icon').exists()).toBe(true)
  })

  it('shows the no-result message and keeps the reroll dice when nothing matches', async () => {
    vi.mocked(getRandomRecipe).mockRejectedValue({ response: { status: 404 } })

    const wrapper = mountView()
    await flushPromises()
    await roll(wrapper)

    expect(wrapper.find('.no-result').text()).toBe('Aucune recette ne correspond à ces critères.')
    expect(wrapper.find('.reroll button.dice').exists()).toBe(true)
  })

  it('reuses the recipe list filters, folded behind the Filtres button', async () => {
    const wrapper = mountView()
    await flushPromises()

    const toggle = wrapper.find('.recipe-filters.collapsible button.toggle')
    expect(toggle.attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('#recipe-filters-panel').classes()).not.toContain('is-open')
    expect(wrapper.find('[data-testid="filters-badge"]').exists()).toBe(false)

    await toggle.trigger('click')

    expect(wrapper.find('#recipe-filters-panel').classes()).toContain('is-open')
    expect(toggle.attributes('aria-expanded')).toBe('true')
  })

  it("pre-fills the allergen exclusion filter from the user's own allergies and intolerances", async () => {
    useAuthStore().user = { allergies: ['peanut'], intolerances: ['lactose'] } as unknown as User

    const wrapper = mountView()
    await flushPromises()
    await roll(wrapper)

    expect(getRandomRecipe).toHaveBeenCalledWith({ exclude_allergens: 'peanut,lactose' })
    expect(wrapper.find('[data-testid="filters-badge"]').text()).toBe('1')
  })

  it('changing a filter only redraws once the dice has been rolled, passing the filters through', async () => {
    useAuthStore().user = { allergies: [], intolerances: [] } as unknown as User

    const wrapper = mountView()
    await flushPromises()

    await wrapper.find('input[name="diet_type"][value="vegan"]').setValue()
    await vi.runAllTimersAsync()
    await flushPromises()
    expect(getRandomRecipe).not.toHaveBeenCalled()

    await roll(wrapper)
    expect(getRandomRecipe).toHaveBeenLastCalledWith({ diet_type: 'vegan' })

    await wrapper.find('[data-testid="in-season-toggle"]').trigger('click')
    await vi.runAllTimersAsync()
    await flushPromises()

    expect(getRandomRecipe).toHaveBeenCalledTimes(2)
    expect(getRandomRecipe).toHaveBeenLastCalledWith({ diet_type: 'vegan', in_season: true })
  })
})
