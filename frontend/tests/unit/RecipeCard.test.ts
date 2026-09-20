import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import RecipeCard from '../../src/components/RecipeCard.vue'
import { i18n } from '../../src/i18n'
import type { Recipe } from '../../src/types/models'

function mountCard(recipe: Partial<Recipe>) {
  return mount(RecipeCard, {
    props: { recipe: recipe as Recipe },
    global: {
      plugins: [i18n, createPinia()],
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
})

describe('RecipeCard', () => {
  it('shows a placeholder for imageless recipes only in the tile variant', () => {
    const recipe = { id: 1, title: 'Soupe', diet_type: 'vegan', total_time_minutes: 10 } as Recipe
    const mountVariant = (variant?: 'tile') =>
      mount(RecipeCard, {
        props: { recipe, variant },
        global: { plugins: [i18n, createPinia()], stubs: { RouterLink: { template: '<a><slot /></a>' } } },
      })

    expect(mountVariant('tile').find('.thumb-placeholder').exists()).toBe(true)
    expect(mountVariant().find('.thumb-placeholder').exists()).toBe(false)
  })

  it('renders the title, diet type and total time', () => {
    const wrapper = mountCard({
      id: 1,
      title: 'Curry de lentilles',
      diet_type: 'vegan',
      total_time_minutes: 45,
      description: 'Un curry parfumé.',
    })

    expect(wrapper.text()).toContain('Curry de lentilles')
    expect(wrapper.text()).toContain('Végan')
    expect(wrapper.text()).toContain('45 min')
    expect(wrapper.text()).toContain('Un curry parfumé.')
  })

  it('renders without a description', () => {
    const wrapper = mountCard({
      id: 2,
      title: 'Salade',
      diet_type: 'omnivore',
      total_time_minutes: 10,
      description: '',
    })

    expect(wrapper.text()).toContain('Salade')
    expect(wrapper.find('.description').exists()).toBe(false)
  })

  it('shows a thumbnail when the recipe has an image', () => {
    const wrapper = mountCard({
      id: 3,
      title: 'Tarte',
      diet_type: 'omnivore',
      total_time_minutes: 30,
      description: '',
      image_url: 'https://example.com/tarte.jpg',
    })

    expect(wrapper.find('.thumb').exists()).toBe(true)
    expect(wrapper.find('.thumb').attributes('src')).toBe('https://example.com/tarte.jpg')
  })

  it('shows no thumbnail when the recipe has no image', () => {
    const wrapper = mountCard({
      id: 4,
      title: 'Soupe',
      diet_type: 'omnivore',
      total_time_minutes: 15,
      description: '',
    })

    expect(wrapper.find('.thumb').exists()).toBe(false)
  })
})
