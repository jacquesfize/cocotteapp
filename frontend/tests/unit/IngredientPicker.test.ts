import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/ingredients', () => ({
  listIngredients: vi.fn().mockResolvedValue({ results: [], count: 0, next: null, previous: null }),
  createIngredient: vi.fn(),
}))

import { createIngredient, listIngredients } from '../../src/api/ingredients'
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
    await wrapper.find('li.create').trigger('mousedown')

    expect(wrapper.findComponent(IngredientEditModal).exists()).toBe(true)
    expect(createIngredient).not.toHaveBeenCalled()
  })

  it('selects the ingredient and closes the modal once created', async () => {
    const wrapper = mount(IngredientPicker, { global: { plugins: [i18n] } })

    await wrapper.find('input').setValue('Coriandre')
    await wrapper.find('li.create').trigger('mousedown')

    await wrapper.findComponent(IngredientEditModal).vm.$emit('created', ingredient())

    expect(wrapper.findComponent(IngredientEditModal).exists()).toBe(false)
    expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([ingredient()])
  })

  describe('suggestions list', () => {
    const coriandre = ingredient()

    async function typeAndLoad(wrapper: ReturnType<typeof mount>, text = 'Cor') {
      vi.mocked(listIngredients).mockResolvedValue({ results: [coriandre], count: 1, next: null, previous: null })
      await wrapper.find('input').setValue(text)
      await vi.advanceTimersByTimeAsync(300)
      await flushPromises()
    }

    beforeEach(() => {
      vi.useFakeTimers()
    })
    afterEach(() => {
      vi.useRealTimers()
    })

    it('closes after selection and does not search again for the selected name', async () => {
      const wrapper = mount(IngredientPicker, { global: { plugins: [i18n] } })
      await typeAndLoad(wrapper)
      expect(wrapper.find('ul.suggestions').exists()).toBe(true)

      await wrapper.find('li').trigger('mousedown')
      await vi.advanceTimersByTimeAsync(500)
      await flushPromises()

      expect(wrapper.find('ul.suggestions').exists()).toBe(false)
      expect((wrapper.find('input').element as HTMLInputElement).value).toBe('Coriandre')
      expect(listIngredients).toHaveBeenCalledTimes(1)
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([coriandre])
    })

    it('does not reopen on refocus or blur without new typing', async () => {
      const wrapper = mount(IngredientPicker, { global: { plugins: [i18n] } })
      await typeAndLoad(wrapper)
      await wrapper.find('li').trigger('mousedown')

      await wrapper.find('input').trigger('blur')
      await vi.advanceTimersByTimeAsync(300)
      await wrapper.find('input').trigger('focus')
      await flushPromises()

      expect(wrapper.find('ul.suggestions').exists()).toBe(false)
    })

    it('closes on Escape', async () => {
      const wrapper = mount(IngredientPicker, { global: { plugins: [i18n] } })
      await typeAndLoad(wrapper)
      await wrapper.find('input').trigger('keydown', { key: 'Escape' })
      expect(wrapper.find('ul.suggestions').exists()).toBe(false)
    })

    it('navigates with arrows and selects with Enter', async () => {
      const wrapper = mount(IngredientPicker, { global: { plugins: [i18n] } })
      await typeAndLoad(wrapper)
      await wrapper.find('input').trigger('keydown', { key: 'ArrowDown' })
      expect(wrapper.find('li.active').text()).toBe('Coriandre')

      await wrapper.find('input').trigger('keydown', { key: 'Enter' })
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([coriandre])
      expect(wrapper.find('ul.suggestions').exists()).toBe(false)
    })
  })
})
