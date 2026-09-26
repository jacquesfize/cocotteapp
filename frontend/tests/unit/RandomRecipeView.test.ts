import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/recipes', () => ({
  getRandomRecipe: vi.fn(),
  downloadRecipePdf: vi.fn(),
  getRecipeNutrition: vi.fn().mockResolvedValue({ per_serving: null }),
}))

import { getRandomRecipe } from '../../src/api/recipes'
import RandomRecipeView from '../../src/views/RandomRecipeView.vue'
import type { Recipe } from '../../src/types/models'

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

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

    const wrapper = mount(RandomRecipeView, {
      global: {
        plugins: [i18n],
        stubs: { RouterLink: { template: '<a><slot /></a>' }, AddToPlanForm: true },
      },
    })
    await flushPromises()

    expect(wrapper.find('h2').text()).toBe('Cinnamon rolls')
    expect(wrapper.find('.restricted-notice').exists()).toBe(true)
  })
})
