import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/allergens', () => ({ listAllergens: vi.fn().mockResolvedValue([]) }))
vi.mock('../../src/api/ingredients', () => ({
  listIngredients: vi.fn().mockResolvedValue({ results: [], count: 0, next: null, previous: null }),
  createIngredient: vi.fn(),
}))

import { createIngredient, listIngredients } from '../../src/api/ingredients'
import IngredientEditModal from '../../src/components/recipes/IngredientEditModal.vue'
import IngredientPicker from '../../src/components/recipes/IngredientPicker.vue'
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

// Démonte les composants entre les tests : leurs timers de debounce ne doivent pas fuiter
// dans le test suivant (ils y faisaient appeler listIngredients une fois de trop).
enableAutoUnmount(afterEach)

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
      expect(wrapper.find('ul.suggestions-dropdown').exists()).toBe(true)

      await wrapper.find('li').trigger('mousedown')
      await vi.advanceTimersByTimeAsync(500)
      await flushPromises()

      expect(wrapper.find('ul.suggestions-dropdown').exists()).toBe(false)
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

      expect(wrapper.find('ul.suggestions-dropdown').exists()).toBe(false)
    })

    it('closes on Escape', async () => {
      const wrapper = mount(IngredientPicker, { global: { plugins: [i18n] } })
      await typeAndLoad(wrapper)
      await wrapper.find('input').trigger('keydown', { key: 'Escape' })
      expect(wrapper.find('ul.suggestions-dropdown').exists()).toBe(false)
    })

    it('navigates with arrows and selects with Enter', async () => {
      const wrapper = mount(IngredientPicker, { global: { plugins: [i18n] } })
      await typeAndLoad(wrapper)
      await wrapper.find('input').trigger('keydown', { key: 'ArrowDown' })
      expect(wrapper.find('li.active').text()).toBe('Coriandre')

      await wrapper.find('input').trigger('keydown', { key: 'Enter' })
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([coriandre])
      expect(wrapper.find('ul.suggestions-dropdown').exists()).toBe(false)
    })
  })

  describe('unverified ingredients', () => {
    const own = () => ingredient({ id: 8, name: 'Ail noir', is_verified: false, can_edit: true })

    it('flags unverified suggestions', async () => {
      vi.useFakeTimers()
      vi.mocked(listIngredients).mockResolvedValue({
        results: [ingredient(), own()],
        count: 2,
        next: null,
        previous: null,
      })
      const wrapper = mount(IngredientPicker, { global: { plugins: [i18n] } })
      await wrapper.find('input').setValue('A')
      await vi.advanceTimersByTimeAsync(300)
      await flushPromises()
      vi.useRealTimers()

      const items = wrapper.findAll('ul.suggestions-dropdown li')
      expect(items[0].find('[data-testid="unverified-badge"]').exists()).toBe(false)
      expect(items[1].find('[data-testid="unverified-badge"]').exists()).toBe(true)
    })

    it('lets the creator edit the selected ingredient', async () => {
      const wrapper = mount(IngredientPicker, { props: { modelValue: own() }, global: { plugins: [i18n] } })
      expect(wrapper.find('[data-testid="unverified-badge"]').exists()).toBe(true)

      await wrapper.get('[data-testid="ingredient-picker-edit"]').trigger('click')
      const modal = wrapper.findComponent(IngredientEditModal)
      expect(modal.props('ingredient')).toEqual(own())
      expect(modal.props('deletable')).toBe(true)

      const fixed = { ...own(), name: 'Ail noirci' }
      modal.vm.$emit('updated', fixed)
      await flushPromises()
      expect(wrapper.findComponent(IngredientEditModal).exists()).toBe(false)
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([fixed])
      expect((wrapper.find('input').element as HTMLInputElement).value).toBe('Ail noirci')
    })

    it('clears the selection once the ingredient is deleted', async () => {
      const wrapper = mount(IngredientPicker, { props: { modelValue: own() }, global: { plugins: [i18n] } })
      await wrapper.get('[data-testid="ingredient-picker-edit"]').trigger('click')
      wrapper.findComponent(IngredientEditModal).vm.$emit('deleted', 8)
      await flushPromises()
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([null])
      expect((wrapper.find('input').element as HTMLInputElement).value).toBe('')
    })

    it('shows the badge but no edit button when the API does not allow editing', () => {
      const wrapper = mount(IngredientPicker, {
        props: { modelValue: { ...own(), can_edit: false } },
        global: { plugins: [i18n] },
      })
      expect(wrapper.find('[data-testid="unverified-badge"]').exists()).toBe(true)
      expect(wrapper.find('[data-testid="ingredient-picker-edit"]').exists()).toBe(false)
    })

    it('shows nothing extra for a verified ingredient the user cannot edit', () => {
      const wrapper = mount(IngredientPicker, {
        props: { modelValue: ingredient({ is_verified: true, can_edit: false }) },
        global: { plugins: [i18n] },
      })
      expect(wrapper.find('.picker-meta').exists()).toBe(false)
    })

    it('neither creates nor edits in select-only mode', async () => {
      const wrapper = mount(IngredientPicker, {
        props: { modelValue: own(), selectOnly: true },
        global: { plugins: [i18n] },
      })
      expect(wrapper.find('[data-testid="ingredient-picker-edit"]').exists()).toBe(false)
      await wrapper.find('input').setValue('Nouveau')
      await wrapper.find('input').trigger('input')
      expect(wrapper.find('li.create').exists()).toBe(false)
    })
  })
})
