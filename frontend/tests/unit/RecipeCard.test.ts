import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import RecipeCard from '../../src/components/recipes/RecipeCard.vue'
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

  it('feature variant puts the photo (or a placeholder) on top and keeps the detailed meta below', () => {
    const recipe = {
      id: 1,
      title: 'Soupe',
      diet_type: 'vegan',
      total_time_minutes: 10,
      servings: 4,
      tags: [{ id: 1, name: 'Hiver' }],
    } as Recipe
    const wrapper = mount(RecipeCard, {
      props: { recipe, variant: 'feature' },
      global: { plugins: [i18n, createPinia()], stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })

    expect(wrapper.classes()).toContain('feature')
    expect(wrapper.classes()).not.toContain('tile')
    expect(wrapper.find('.thumb-placeholder').exists()).toBe(true)
    expect(wrapper.find('.scrim').exists()).toBe(false)
    expect(wrapper.find('.meta .diet-badge').text()).toBe('Végan')
    expect(wrapper.find('.tags').text()).toContain('Hiver')
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

    expect(wrapper.find('.thumb-wrapper img').exists()).toBe(true)
    expect(wrapper.find('.thumb-wrapper img').attributes('src')).toBe('https://example.com/tarte.jpg')
  })

  it('explains the lock icon of a restricted recipe with a tooltip and an accessible label', () => {
    const wrapper = mountCard({
      id: 10,
      title: 'Tarte',
      diet_type: 'omnivore',
      total_time_minutes: 40,
      content_restricted: true,
    })

    const icon = wrapper.find('.restricted-icon')
    expect(icon.attributes('role')).toBe('img')
    expect(icon.attributes('title')).toContain("droits d'auteur")
    expect(icon.attributes('aria-label')).toBe(icon.attributes('title'))
  })

  it('shows no thumbnail when the recipe has no image', () => {
    const wrapper = mountCard({
      id: 4,
      title: 'Soupe',
      diet_type: 'omnivore',
      total_time_minutes: 15,
      description: '',
    })

    expect(wrapper.find('.thumb-wrapper').exists()).toBe(false)
  })

  it('shows the image credit as an icon button with the full credit in row variant', () => {
    const wrapper = mountCard({
      id: 5,
      title: 'Tarte',
      diet_type: 'omnivore',
      total_time_minutes: 40,
      image_url: 'https://x/tarte.jpg',
      source_url: 'https://cuisine.example/tarte',
    })

    const button = wrapper.find('.thumb-wrapper .credit-info-btn')
    expect(button.exists()).toBe(true)
    expect(button.attributes('aria-label')).toContain('cuisine.example')
    // Texte complet (non tronqué) dans la bulle, reliée au bouton.
    const popover = wrapper.find('.thumb-wrapper .credit-popover')
    expect(popover.text()).toBe('image via cuisine.example')
    expect(button.attributes('aria-describedby')).toBe(popover.attributes('id'))
    expect(wrapper.find('.thumb-wrapper .image-credit-line').exists()).toBe(false)
  })

  it('toggles the credit popover open on click', async () => {
    const wrapper = mountCard({
      id: 9,
      title: 'Tarte',
      diet_type: 'omnivore',
      total_time_minutes: 40,
      image_url: 'https://x/tarte.jpg',
      source_url: 'https://cuisine.example/tarte',
    })

    const button = wrapper.find('.credit-info-btn')
    expect(button.attributes('aria-expanded')).toBe('false')
    await button.trigger('click')
    expect(button.attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('.credit-info').classes()).toContain('open')
  })

  it('shows an on-image credit icon in the top corner in tile variant', () => {
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

    const info = wrapper.find('.thumb-wrapper .credit-info')
    expect(info.exists()).toBe(true)
    expect(info.classes()).toEqual(expect.arrayContaining(['top', 'right']))
    expect(info.find('.credit-popover').text()).toContain('cuisine.example')
    expect(wrapper.find('.thumb-wrapper .image-credit-line').exists()).toBe(false)
  })

  it('shows a neutral placeholder for a self-uploaded image with no other credit info', () => {
    const wrapper = mountCard({
      id: 7,
      title: 'Tarte',
      diet_type: 'omnivore',
      total_time_minutes: 40,
      image: 'https://x/tarte-uploaded.jpg',
      source_url: 'https://cuisine.example/tarte',
    })

    const credit = wrapper.find('.thumb-wrapper .credit-popover')
    expect(credit.exists()).toBe(true)
    expect(credit.text()).not.toContain('cuisine.example')
    expect(credit.text()).toBe('Crédit non précisé')
  })

  it('shows servings, carbon footprint, tags and the author of someone else\'s recipe', () => {
    const wrapper = mountCard({
      id: 8,
      title: 'Dahl',
      diet_type: 'vegan',
      total_time_minutes: 30,
      servings: 4,
      // Total de la recette (4 portions) : la carte doit afficher la valeur par portion.
      carbon_footprint_kg_co2e: 1.68,
      carbon_footprint_per_serving_kg_co2e: 0.42,
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
    expect(wrapper.text()).toContain('0,42 kg CO₂e / portion')
    expect(wrapper.text()).not.toContain('1,68')
    expect(wrapper.find('.carbon').classes()).toContain('carbon-low')
    expect(wrapper.text()).toContain('par bob')
    expect(wrapper.findAll('.tag').map((t) => t.text())).toEqual(['Rapide', 'Indien', 'Épicé', '+1'])
  })
})

describe('RecipeCard missing data', () => {
  it('hides the time and carbon items instead of showing "0 min" / "0 kg CO₂e"', () => {
    const wrapper = mountCard({
      id: 9,
      title: 'Importée',
      diet_type: 'vegan',
      total_time_minutes: 0,
      servings: 2,
      carbon_footprint_kg_co2e: 0,
      carbon_footprint_per_serving_kg_co2e: 0,
    })

    expect(wrapper.text()).not.toContain('0 min')
    expect(wrapper.text()).not.toContain('CO₂e')
    expect(wrapper.find('.carbon').exists()).toBe(false)
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
    await wrapper.find('button.actions-toggle').trigger('click')
    await wrapper.find('button.actions-link-danger').trigger('click')
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
