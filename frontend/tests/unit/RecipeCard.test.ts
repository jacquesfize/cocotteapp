import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import RecipeCard from '../../src/components/RecipeCard.vue'
import { useAuthStore } from '../../src/stores/auth'
import { i18n } from '../../src/i18n'
import type { Recipe, User } from '../../src/types/models'

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

  it('shows a compact image credit under the thumbnail in row variant', () => {
    const wrapper = mountCard({
      id: 5,
      title: 'Tarte',
      diet_type: 'omnivore',
      total_time_minutes: 40,
      image_url: 'https://x/tarte.jpg',
      source_url: 'https://cuisine.example/tarte',
    })

    expect(wrapper.find('.thumb-credit').exists()).toBe(true)
    expect(wrapper.find('.thumb-credit').text()).toBe('cuisine.example')
  })

  it('shows a full image credit line in tile variant', () => {
    const wrapper = mount(RecipeCard, {
      props: {
        recipe: {
          id: 6,
          title: 'Tarte',
          diet_type: 'omnivore',
          total_time_minutes: 40,
          image_url: 'https://x/tarte.jpg',
          source_url: 'https://cuisine.example/tarte',
        } as Recipe,
        variant: 'tile',
      },
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })

    expect(wrapper.find('.tile-credit').exists()).toBe(true)
    expect(wrapper.find('.tile-credit').text()).toContain('cuisine.example')
    expect(wrapper.find('.thumb-credit').exists()).toBe(false)
  })

  it('does not show a credit for a self-uploaded image', () => {
    const wrapper = mountCard({
      id: 7,
      title: 'Tarte',
      diet_type: 'omnivore',
      total_time_minutes: 40,
      image: 'https://x/tarte-uploaded.jpg',
      source_url: 'https://cuisine.example/tarte',
    })

    expect(wrapper.find('.thumb-credit').exists()).toBe(false)
  })

  it('shows servings, carbon footprint, tags and the author of someone else\'s recipe', () => {
    const wrapper = mountCard({
      id: 8,
      title: 'Dahl',
      diet_type: 'vegan',
      total_time_minutes: 30,
      servings: 4,
      carbon_footprint_kg_co2e: 0.42,
      author: 'bob',
      author_id: 99,
      tags: [
        { id: 1, name: 'Rapide', kind: 'other' },
        { id: 2, name: 'Indien', kind: 'other' },
        { id: 3, name: 'Épicé', kind: 'other' },
        { id: 4, name: 'Hiver', kind: 'other' },
      ] as Recipe['tags'],
    })

    expect(wrapper.text()).toContain('4 portions')
    expect(wrapper.text()).toContain('0,4 kg CO₂e / portion')
    expect(wrapper.find('.carbon').classes()).toContain('carbon-low')
    expect(wrapper.text()).toContain('par bob')
    expect(wrapper.findAll('.tag').map((t) => t.text())).toEqual(['Rapide', 'Indien', 'Épicé', '+1'])
  })
})

describe('RecipeCard actions', () => {
  function mountManageable(recipe: Partial<Recipe>) {
    const pinia = createPinia()
    setActivePinia(pinia)
    useAuthStore().user = { id: 1, username: 'alice' } as unknown as User
    return mount(RecipeCard, {
      props: { recipe: recipe as Recipe, manageable: true },
      global: { plugins: [i18n, pinia], stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
  }

  it('shows edit/delete for the owner and emits delete', async () => {
    const recipe = { id: 9, title: 'Tarte', diet_type: 'omnivore', total_time_minutes: 20, author_id: 1, author: 'alice' } as Recipe
    const wrapper = mountManageable(recipe)

    expect(wrapper.find('.card-actions').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('par alice')
    await wrapper.find('button.danger-btn').trigger('click')
    expect(wrapper.emitted('delete')?.[0]).toEqual([recipe])
  })

  it('shows "importé par" for an imported recipe, even the owner\'s own', () => {
    const wrapper = mountManageable({
      id: 11,
      title: 'Tarte',
      diet_type: 'omnivore',
      total_time_minutes: 20,
      author_id: 1,
      author: 'alice',
      source_type: 'youtube',
    })
    expect(wrapper.find('.author').text()).toBe('importé par alice')
  })

  it('hides the actions on someone else\'s recipe', () => {
    const wrapper = mountManageable({ id: 10, title: 'Tarte', diet_type: 'omnivore', total_time_minutes: 20, author_id: 2 })
    expect(wrapper.find('.card-actions').exists()).toBe(false)
  })
})
