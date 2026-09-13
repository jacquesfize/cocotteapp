import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/ingredients', () => ({
  listIngredients: vi.fn().mockResolvedValue({ results: [], count: 0, next: null, previous: null }),
  createIngredient: vi.fn(),
}))

import { createIngredient } from '../../src/api/ingredients'
import IngredientEditModal from '../../src/components/IngredientEditModal.vue'
import IngredientPicker from '../../src/components/IngredientPicker.vue'
import type { Ingredient } from '../../src/types/models'

function ingredient(overrides?: Partial<Ingredient>): Ingredient {
  return {
    id: 7,
    name: 'Coriandre',
    slug: 'coriandre',
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
    carbon_kg_co2e_per_kg: 0,
    ...overrides,
  } as Ingredient
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  vi.clearAllMocks()
})

describe('IngredientPicker', () => {
  it('opens the ingredient creation modal instead of creating directly on "create" click', async () => {
    const wrapper = mount(IngredientPicker, { global: { plugins: [i18n] } })

    await wrapper.find('input').setValue('Coriandre')
    await wrapper.find('input').trigger('focus')
    await wrapper.find('li.create').trigger('mousedown')

    expect(wrapper.findComponent(IngredientEditModal).exists()).toBe(true)
    expect(createIngredient).not.toHaveBeenCalled()
  })

  it('selects the ingredient and closes the modal once created', async () => {
    const wrapper = mount(IngredientPicker, { global: { plugins: [i18n] } })

    await wrapper.find('input').setValue('Coriandre')
    await wrapper.find('input').trigger('focus')
    await wrapper.find('li.create').trigger('mousedown')

    await wrapper.findComponent(IngredientEditModal).vm.$emit('created', ingredient())

    expect(wrapper.findComponent(IngredientEditModal).exists()).toBe(false)
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([ingredient()])
  })
})
