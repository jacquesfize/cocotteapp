import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RecipeSummary from '../../src/components/recipes/RecipeSummary.vue'
import StepTimerButton from '../../src/components/recipes/StepTimerButton.vue'
import { i18n } from '../../src/i18n'
import type { Recipe, RecipeStep } from '../../src/types/models'

vi.mock('../../src/api/recipes', () => ({
  downloadRecipePdf: vi.fn(),
  getRecipeNutrition: vi.fn().mockResolvedValue({ per_serving: null }),
}))

function step(overrides: Pick<RecipeStep, 'id' | 'order' | 'instruction'>): RecipeStep {
  return {
    image: null,
    image_url: '',
    image_license: '',
    image_credit_author: '',
    image_credit_source_url: '',
    image_credit_license_url: '',
    image_credit_note: '',
    ...overrides,
  }
}

function baseRecipe(overrides: Partial<Recipe> = {}): Recipe {
  return {
    id: 1,
    title: 'Recette',
    slug: 'recette',
    description: '',
    author: 'chef',
    author_id: 1,
    servings: 4,
    prep_time_minutes: 10,
    cook_time_minutes: 20,
    total_time_minutes: 30,
    diet_type: 'omnivore',
    source_type: 'manual',
    source_url: '',
    video_url: '',
    youtube_id: null,
    image: '',
    image_url: '',
    is_public: true,
    ingredients: [
      {
        id: 1,
        ingredient: {
          id: 10,
          name: 'sel',
          slug: 'sel',
          category: 'condiment',
          default_unit: 'g',
          available_months: [],
          calories_kcal: 0,
          protein_g: 0,
          carbs_g: 0,
          fat_g: 0,
          fiber_g: 0,
          iron_mg: 0,
          vitamin_b12_ug: 0,
          calcium_mg: 0,
          omega3_g: 0,
          zinc_mg: 0,
        },
        quantity: 1,
        unit: 'pinch',
        group_name: '',
        order: 0,
      },
    ],
    steps: [step({ id: 1, order: 0, instruction: 'Ajouter le @sel puis laisser ~repos{10%minutes} au frigo.' })],
    ...overrides,
  } as Recipe
}

function mountSummary(recipe: Recipe) {
  return mount(RecipeSummary, {
    props: { recipe },
    global: {
      plugins: [i18n, createPinia()],
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
        NutritionCard: true,
      },
    },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
})

describe('RecipeSummary steps', () => {
  it('renders an ingredient mention as a link and a timer as a StepTimerButton', () => {
    const wrapper = mountSummary(baseRecipe())

    const link = wrapper.find('a.ingredient-mention')
    expect(link.exists()).toBe(true)
    expect(link.text()).toBe('sel')
    expect(link.attributes('href')).toMatch(/^#ingredient-row-\d+$/)

    const timerButton = wrapper.findComponent(StepTimerButton)
    expect(timerButton.exists()).toBe(true)
    expect(timerButton.props('seconds')).toBe(600)
    expect(timerButton.props('label')).toBe('repos')

    expect(wrapper.text()).not.toContain('~repos{10%minutes}')
  })

  it('leaves an unrecognized timer unit as plain text', () => {
    const wrapper = mountSummary(
      baseRecipe({ steps: [step({ id: 1, order: 0, instruction: 'Cuire ~{10%pouces}.' })] }),
    )

    expect(wrapper.findComponent(StepTimerButton).exists()).toBe(false)
    expect(wrapper.text()).toContain('~{10%pouces}')
  })

  it('renders a step with no mention or timer as plain text', () => {
    const wrapper = mountSummary(baseRecipe({ steps: [step({ id: 1, order: 0, instruction: 'Servir chaud.' })] }))

    expect(wrapper.text()).toContain('Servir chaud.')
    expect(wrapper.findComponent(StepTimerButton).exists()).toBe(false)
  })
})

describe('RecipeSummary cookware', () => {
  const cookware = [
    { id: 3, name: 'Four', slug: 'four' },
    {
      id: 4,
      name: 'Plat à gratin',
      slug: 'plat-a-gratin',
      image: '/media/cookware/plat.jpg',
      image_license: 'cc_by_sa',
      image_credit_author: 'Pengo',
      image_credit_source_url: 'https://commons.wikimedia.org/wiki/File:X.jpg',
      image_credit_license_url: 'https://creativecommons.org/licenses/by-sa/3.0/',
    },
  ]

  it('lists the cookware, and a click on an item or a #mention opens its photo with credit', async () => {
    const wrapper = mountSummary(
      baseRecipe({
        cookware,
        steps: [step({ id: 1, order: 0, instruction: 'Verser dans le #plat_à_gratin{} et enfourner (#four).' })],
      }),
    )

    expect(wrapper.findAll('.cookware-chip').map((chip) => chip.text())).toEqual(['Four', 'Plat à gratin'])
    const mentions = wrapper.findAll('button.cookware-mention')
    expect(mentions.map((button) => button.text())).toEqual(['plat à gratin', 'four'])
    expect(wrapper.text()).not.toContain('#plat')

    await mentions[0].trigger('click')
    const modal = wrapper.find('[role="dialog"]')
    expect(modal.find('h2').text()).toBe('Plat à gratin')
    expect(modal.find('img').attributes('src')).toBe('/media/cookware/plat.jpg')
    expect(modal.text()).toContain('Photo : Pengo')
    expect(modal.find('a[href="https://creativecommons.org/licenses/by-sa/3.0/"]').exists()).toBe(true)
    expect(modal.text()).toContain('Voir les recettes avec : Plat à gratin')

    await modal.find('.base-modal-close').trigger('click')
    await wrapper.findAll('.cookware-chip')[0].trigger('click')
    expect(wrapper.find('[role="dialog"] h2').text()).toBe('Four')
    expect(wrapper.find('[role="dialog"] img').exists()).toBe(false)
  })

  it('shows no cookware section when the recipe has none, and renders an unknown #mention as text', () => {
    const wrapper = mountSummary(
      baseRecipe({ steps: [step({ id: 1, order: 0, instruction: 'Cuire au #wok, étape #2.' })] }),
    )

    expect(wrapper.find('.cookware-list').exists()).toBe(false)
    expect(wrapper.find('.cookware-mention').exists()).toBe(false)
    expect(wrapper.text()).toContain('Cuire au wok, étape #2.')
  })
})
