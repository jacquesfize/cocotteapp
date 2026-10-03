import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/recipes', () => ({ getRecipe: vi.fn() }))

import { getRecipe } from '../../src/api/recipes'
import RecipeEmbedView from '../../src/views/embed/RecipeEmbedView.vue'
import type { Recipe } from '../../src/types/models'

beforeEach(() => {
  i18n.global.locale.value = 'en'
  vi.clearAllMocks()
})

describe('RecipeEmbedView', () => {
  it('shows a recipe card opening the recipe in the top window', async () => {
    vi.mocked(getRecipe).mockResolvedValue({
      id: 3,
      title: 'Tarte aux pommes',
      servings: 6,
      total_time_minutes: 45,
      image: null,
      image_url: '',
    } as Recipe)
    const wrapper = mount(RecipeEmbedView, { props: { id: 3 }, global: { plugins: [i18n] } })
    await flushPromises()

    const card = wrapper.find('[data-testid="recipe-embed-card"]')
    expect(card.text()).toContain('Tarte aux pommes')
    expect(card.text()).toContain('6 servings')
    expect(card.attributes('href')).toBe('/recipes/3')
    expect(card.attributes('target')).toBe('_top')
  })

  it('says when the recipe is not available', async () => {
    vi.mocked(getRecipe).mockRejectedValue(new Error('404'))
    const wrapper = mount(RecipeEmbedView, { props: { id: 3 }, global: { plugins: [i18n] } })
    await flushPromises()

    expect(wrapper.text()).toContain('This recipe is no longer available.')
  })
})
