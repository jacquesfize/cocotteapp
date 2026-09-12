import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import RecipeCard from '../../src/components/RecipeCard.vue'

function mountCard(recipe) {
  return mount(RecipeCard, {
    props: { recipe },
    global: {
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

describe('RecipeCard', () => {
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
})
