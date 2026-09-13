import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../src/api/ingredients', () => ({
  createIngredient: vi.fn(),
  suggestIngredientNutrition: vi.fn(),
}))

import { createIngredient, suggestIngredientNutrition } from '../../src/api/ingredients'
import IngredientEditModal from '../../src/components/IngredientEditModal.vue'
import { i18n } from '../../src/i18n'
import type { Ingredient } from '../../src/types/models'

function mountModal(initialName = 'poireau') {
  return mount(IngredientEditModal, {
    props: { initialName },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  vi.clearAllMocks()
})

describe('IngredientEditModal', () => {
  it('prefills the name from the mention that triggered it', () => {
    const wrapper = mountModal('huile olive')
    expect(wrapper.get('#ingredient-modal-name').element).toHaveProperty('value', 'huile olive')
  })

  it('creates the ingredient with the form values and emits it', async () => {
    const created = { id: 9, name: 'poireau' } as Ingredient
    vi.mocked(createIngredient).mockResolvedValue(created)

    const wrapper = mountModal('poireau')
    await wrapper.get('#ingredient-modal-category').setValue('vegetable')
    await wrapper.get('form').trigger('submit')
    await wrapper.vm.$nextTick()

    expect(createIngredient).toHaveBeenCalledWith(expect.objectContaining({ name: 'poireau', category: 'vegetable' }))
    expect(wrapper.emitted('created')?.[0]).toEqual([created])
  })

  it('shows an error message when creation fails', async () => {
    vi.mocked(createIngredient).mockRejectedValue(new Error('boom'))

    const wrapper = mountModal()
    await wrapper.get('form').trigger('submit')
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error').exists()).toBe(true)
    expect(wrapper.emitted('created')).toBeUndefined()
  })

  it('emits close when the cancel button is clicked', async () => {
    const wrapper = mountModal()
    await wrapper.get('button.secondary').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('applies suggested nutrition values to the form when found', async () => {
    vi.mocked(suggestIngredientNutrition).mockResolvedValue({
      found: true,
      suggestion: { calories_kcal: 149, protein_g: 6.4 },
    })

    const wrapper = mountModal('ail')
    await wrapper.get('#ingredient-modal-suggest').trigger('click')
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(suggestIngredientNutrition).toHaveBeenCalledWith('ail')
    expect(wrapper.get('#ingredient-modal-calories_kcal').element).toHaveProperty('value', '149')
    expect(wrapper.get('#ingredient-modal-protein_g').element).toHaveProperty('value', '6.4')
    expect(wrapper.text()).toContain('Valeurs suggérées appliquées')
  })

  it('applies the suggested carbon footprint alongside nutrition values', async () => {
    vi.mocked(suggestIngredientNutrition).mockResolvedValue({
      found: true,
      suggestion: { calories_kcal: 149, carbon_kg_co2e_per_kg: 0.383 },
    })

    const wrapper = mountModal('ail')
    await wrapper.get('#ingredient-modal-suggest').trigger('click')
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(wrapper.get('#ingredient-modal-carbon').element).toHaveProperty('value', '0.383')
  })

  it('shows a message when no suggestion is found', async () => {
    vi.mocked(suggestIngredientNutrition).mockResolvedValue({ found: false })

    const wrapper = mountModal('ingrédient très rare')
    await wrapper.get('#ingredient-modal-suggest').trigger('click')
    await wrapper.vm.$nextTick()
    await wrapper.vm.$nextTick()

    expect(wrapper.text()).toContain('Aucune suggestion trouvée')
    expect(wrapper.get('#ingredient-modal-calories_kcal').element).toHaveProperty('value', '0')
  })
})
