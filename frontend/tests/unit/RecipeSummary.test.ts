import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RecipeSummary from '../../src/components/RecipeSummary.vue'
import StepTimerButton from '../../src/components/StepTimerButton.vue'
import { i18n } from '../../src/i18n'
import type { Recipe } from '../../src/types/models'

vi.mock('../../src/api/recipes', () => ({
  downloadRecipePdf: vi.fn(),
  getRecipeNutrition: vi.fn().mockResolvedValue({ per_serving: null }),
}))

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
    steps: [{ id: 1, order: 0, instruction: 'Ajouter le @sel puis laisser ~repos{10%minutes} au frigo.' }],
    ...overrides,
  } as Recipe
}

function mountSummary(recipe: Recipe) {
  return mount(RecipeSummary, {
    props: { recipe },
    global: {
      plugins: [i18n],
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
    expect(link.attributes('href')).toBe('#ingredient-10')

    const timerButton = wrapper.findComponent(StepTimerButton)
    expect(timerButton.exists()).toBe(true)
    expect(timerButton.props('seconds')).toBe(600)
    expect(timerButton.props('label')).toBe('repos')

    expect(wrapper.text()).not.toContain('~repos{10%minutes}')
  })

  it('leaves an unrecognized timer unit as plain text', () => {
    const wrapper = mountSummary(
      baseRecipe({ steps: [{ id: 1, order: 0, instruction: 'Cuire ~{10%pouces}.' }] }),
    )

    expect(wrapper.findComponent(StepTimerButton).exists()).toBe(false)
    expect(wrapper.text()).toContain('~{10%pouces}')
  })

  it('renders a step with no mention or timer as plain text', () => {
    const wrapper = mountSummary(baseRecipe({ steps: [{ id: 1, order: 0, instruction: 'Servir chaud.' }] }))

    expect(wrapper.text()).toContain('Servir chaud.')
    expect(wrapper.findComponent(StepTimerButton).exists()).toBe(false)
  })
})
