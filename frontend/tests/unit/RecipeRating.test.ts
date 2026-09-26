import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RecipeRating from '../../src/components/RecipeRating.vue'
import { i18n } from '../../src/i18n'

const { rateRecipe } = vi.hoisted(() => ({
  rateRecipe: vi.fn(),
}))

vi.mock('../../src/api/recipes', () => ({
  rateRecipe,
}))

function mountRating(props: Partial<{ averageRating: number | null; ratingsCount: number; myRating: number | null }> = {}) {
  return mount(RecipeRating, {
    props: {
      recipeId: 1,
      averageRating: null,
      ratingsCount: 0,
      myRating: null,
      ...props,
    },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  rateRecipe.mockReset()
})

describe('RecipeRating', () => {
  it('shows an empty state when the recipe has no ratings', () => {
    const wrapper = mountRating()

    expect(wrapper.text()).toContain('Pas encore noté')
  })

  it('shows the average and count when the recipe has ratings', () => {
    const wrapper = mountRating({ averageRating: 4.5, ratingsCount: 12 })

    expect(wrapper.text()).toContain('4.5')
    expect(wrapper.text()).toContain('12')
  })

  it('never renders a name field, only star buttons', () => {
    const wrapper = mountRating()

    expect(wrapper.find('input').exists()).toBe(false)
    expect(wrapper.findAll('.rating-star')).toHaveLength(5)
  })

  it('posts the clicked value and applies the returned aggregate', async () => {
    rateRecipe.mockResolvedValue({ average_rating: 5, ratings_count: 1, my_rating: 5 })

    const wrapper = mountRating()
    await wrapper.findAll('.rating-star')[4].trigger('click')
    await flushPromises()

    expect(rateRecipe).toHaveBeenCalledWith(1, 5)
    expect(wrapper.emitted('rated')?.[0]).toEqual([{ average_rating: 5, ratings_count: 1, my_rating: 5 }])
  })

  it('shows a dedicated message when throttled', async () => {
    rateRecipe.mockRejectedValue({ response: { status: 429 } })

    const wrapper = mountRating()
    await wrapper.findAll('.rating-star')[0].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain('Trop de votes récents')
  })

  it('shows a generic error message on other failures', async () => {
    rateRecipe.mockRejectedValue({ response: { status: 500 } })

    const wrapper = mountRating()
    await wrapper.findAll('.rating-star')[0].trigger('click')
    await flushPromises()

    expect(wrapper.text()).toContain("Impossible d'enregistrer votre note.")
  })
})
