import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../src/api/ingredients', () => ({
  listIngredients: vi.fn(),
  createIngredient: vi.fn(),
}))

import { listIngredients } from '../../src/api/ingredients'
import CooklangStepInput from '../../src/components/CooklangStepInput.vue'
import IngredientEditModal from '../../src/components/IngredientEditModal.vue'
import { i18n } from '../../src/i18n'
import type { Ingredient } from '../../src/types/models'

function ingredient(overrides: Partial<Ingredient>): Ingredient {
  return {
    id: 1,
    name: 'poireau',
    slug: 'poireau',
    category: 'vegetable',
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
  }
}

function mountInput(modelValue = '', ingredientNames = ['poireau', 'huile olive']) {
  return mount(CooklangStepInput, {
    props: { modelValue, ingredientNames },
    global: { plugins: [i18n] },
  })
}

async function typeInto(wrapper: ReturnType<typeof mountInput>, value: string) {
  const textarea = wrapper.get('textarea')
  await textarea.setValue(value)
  await wrapper.setProps({ modelValue: value })
}

beforeEach(() => {
  vi.useFakeTimers()
  vi.mocked(listIngredients).mockResolvedValue({ results: [], count: 0, next: null, previous: null })
})

afterEach(() => {
  vi.useRealTimers()
})

describe('CooklangStepInput', () => {
  it('searches the ingredient database (debounced) for what follows "@"', async () => {
    vi.mocked(listIngredients).mockResolvedValue({
      results: [ingredient({ id: 1, name: 'poireau' })],
      count: 1,
      next: null,
      previous: null,
    })

    const wrapper = mountInput()
    await typeInto(wrapper, 'Faire revenir le @poi')

    await vi.advanceTimersByTimeAsync(300)
    await wrapper.vm.$nextTick()

    expect(listIngredients).toHaveBeenCalledWith({ search: 'poi' })
    const items = wrapper.findAll('.suggestions li')
    expect(items[0].text()).toBe('poireau')
  })

  it('hides suggestions once a space is typed after the "@" word', async () => {
    const wrapper = mountInput()
    await typeInto(wrapper, 'Faire revenir le @poireau ')
    await vi.advanceTimersByTimeAsync(300)

    expect(wrapper.find('.suggestions').exists()).toBe(false)
  })

  it('inserts the underscore-joined token when a multi-word suggestion is picked', async () => {
    vi.mocked(listIngredients).mockResolvedValue({
      results: [ingredient({ id: 2, name: 'huile olive' })],
      count: 1,
      next: null,
      previous: null,
    })

    const wrapper = mountInput('', [])
    await typeInto(wrapper, 'Ajouter @huile')
    await vi.advanceTimersByTimeAsync(300)
    await wrapper.vm.$nextTick()

    await wrapper.get('.suggestions li').trigger('mousedown')

    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toBe('Ajouter @huile_olive ')
  })

  it('adds the ingredient to the recipe when picking a DB match not already in the list', async () => {
    const found = ingredient({ id: 3, name: 'beurre' })
    vi.mocked(listIngredients).mockResolvedValue({ results: [found], count: 1, next: null, previous: null })

    const wrapper = mountInput('', ['poireau'])
    await typeInto(wrapper, 'Ajouter du @beurre')
    await vi.advanceTimersByTimeAsync(300)
    await wrapper.vm.$nextTick()

    await wrapper.get('.suggestions li').trigger('mousedown')

    expect(wrapper.emitted('add-ingredient')?.[0]).toEqual([found])
  })

  it('does not re-add an ingredient that is already in the recipe', async () => {
    const found = ingredient({ id: 4, name: 'poireau' })
    vi.mocked(listIngredients).mockResolvedValue({ results: [found], count: 1, next: null, previous: null })

    const wrapper = mountInput('', ['poireau'])
    await typeInto(wrapper, 'Ajouter du @poireau')
    await vi.advanceTimersByTimeAsync(300)
    await wrapper.vm.$nextTick()

    await wrapper.get('.suggestions li').trigger('mousedown')

    expect(wrapper.emitted('add-ingredient')).toBeUndefined()
  })

  it('offers to create a new ingredient when nothing matches, and opens the modal', async () => {
    vi.mocked(listIngredients).mockResolvedValue({ results: [], count: 0, next: null, previous: null })

    const wrapper = mountInput('', [])
    await typeInto(wrapper, 'Ajouter du @poireau')
    await vi.advanceTimersByTimeAsync(300)
    await wrapper.vm.$nextTick()

    const createOption = wrapper.get('.suggestions li.create')
    expect(createOption.text()).toContain('poireau')

    await createOption.trigger('mousedown')

    expect(wrapper.findComponent(IngredientEditModal).exists()).toBe(true)
  })

  it('warns about a mention that matches no known ingredient', () => {
    const wrapper = mountInput('Ajouter le @beurre puis mélanger.')
    expect(wrapper.text()).toContain('beurre')
    expect(wrapper.find('.mention-warning').exists()).toBe(true)
  })

  it('shows no warning once every mention matches a known ingredient', () => {
    const wrapper = mountInput('Faire revenir le @poireau puis ajouter le @huile_olive et mélanger.')
    expect(wrapper.find('.mention-warning').exists()).toBe(false)
  })
})
