import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import HomeCarousel from '../../src/components/HomeCarousel.vue'
import { i18n } from '../../src/i18n'
import type { Recipe } from '../../src/types/models'

const recipes = [
  { id: 1, title: 'Curry', diet_type: 'vegan', total_time_minutes: 45, image: 'http://x/a.jpg' },
  { id: 2, title: 'Soupe', diet_type: 'omnivore', total_time_minutes: 20 },
] as Recipe[]

beforeEach(() => {
  i18n.global.locale.value = 'fr'
})

describe('HomeCarousel', () => {
  it('renders one slide and one dot per recipe, with a fallback when there is no image', () => {
    const wrapper = mount(HomeCarousel, {
      props: { recipes },
      global: { plugins: [i18n], stubs: { RouterLink: { template: '<a class="carousel-slide"><slot /></a>' } } },
    })

    expect(wrapper.findAll('.carousel-slide')).toHaveLength(2)
    expect(wrapper.findAll('.dot')).toHaveLength(2)
    expect(wrapper.findAll('img')).toHaveLength(1)
    expect(wrapper.text()).toContain('Curry')
    expect(wrapper.text()).toContain('Voir la recette')
    expect(wrapper.findAll('.dot')[0].attributes('aria-selected')).toBe('true')
  })

  it('shows an image credit for a recipe imported with an external image', () => {
    const wrapper = mount(HomeCarousel, {
      props: {
        recipes: [
          {
            id: 3,
            title: 'Tarte',
            diet_type: 'vegan',
            total_time_minutes: 30,
            image_url: 'http://x/tarte.jpg',
            source_url: 'https://cuisine.example/tarte',
          } as Recipe,
        ],
      },
      global: { plugins: [i18n], stubs: { RouterLink: { template: '<a class="carousel-slide"><slot /></a>' } } },
    })

    expect(wrapper.find('.credit-badge').exists()).toBe(true)
    expect(wrapper.find('.credit-badge').text()).toContain('cuisine.example')
  })
})
