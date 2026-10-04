import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../src/api/allergens', () => ({
  listAllergens: vi.fn().mockResolvedValue([
    { slug: 'gluten', name: 'Gluten' },
    { slug: 'egg', name: 'Œufs' },
  ]),
}))
vi.mock('../../src/api/ingredients', () => ({
  createIngredient: vi.fn(),
  updateIngredient: vi.fn(),
  deleteIngredient: vi.fn(),
  suggestIngredientNutrition: vi.fn(),
}))

import { createIngredient, deleteIngredient, suggestIngredientNutrition } from '../../src/api/ingredients'
import IngredientEditModal from '../../src/components/recipes/IngredientEditModal.vue'
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

  it('always exposes English name and season months, and sends them', async () => {
    vi.mocked(createIngredient).mockResolvedValue({ id: 1 } as Ingredient)
    const wrapper = mountModal('poireau')
    await wrapper.get('#ingredient-modal-name-en').setValue('leek')
    await wrapper.findAll('.month input')[2].setValue(true)
    await wrapper.get('form').trigger('submit')
    await wrapper.vm.$nextTick()
    expect(createIngredient).toHaveBeenCalledWith(
      expect.objectContaining({ translations: { en: 'leek' }, available_months: [3] }),
    )
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

  it('sends the ticked allergens and marks the ingredient as reviewed', async () => {
    vi.mocked(createIngredient).mockResolvedValue({ id: 1 } as Ingredient)
    const wrapper = mountModal('pâtes')
    await flushPromises()

    const reviewed = wrapper.get('[data-testid="allergens-reviewed"]')
    expect((reviewed.element as HTMLInputElement).checked).toBe(false)

    await wrapper.get('[data-testid="allergen-gluten"]').setValue(true)
    expect((reviewed.element as HTMLInputElement).checked).toBe(true)
    expect((reviewed.element as HTMLInputElement).disabled).toBe(true)

    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createIngredient).toHaveBeenCalledWith(
      expect.objectContaining({ allergens: ['gluten'], allergens_reviewed: true }),
    )
  })

  it('lets the user declare "no allergen" explicitly', async () => {
    vi.mocked(createIngredient).mockResolvedValue({ id: 1 } as Ingredient)
    const wrapper = mountModal('riz')
    await flushPromises()

    await wrapper.get('[data-testid="allergens-reviewed"]').setValue(true)
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(createIngredient).toHaveBeenCalledWith(
      expect.objectContaining({ allergens: [], allergens_reviewed: true }),
    )
  })

  describe('editing an ingredient created by the user', () => {
    const own = {
      id: 12,
      name: 'ail noir',
      slug: 'ail-noir',
      category: 'condiment',
      default_unit: 'g',
      available_months: [],
      is_verified: false,
      created_by: 3,
      created_by_username: 'alice',
      can_edit: true,
    } as unknown as Ingredient

    function mountEdit(ingredient: Ingredient, deletable = true) {
      return mount(IngredientEditModal, { props: { ingredient, deletable }, global: { plugins: [i18n] } })
    }

    beforeEach(() => {
      window.confirm = vi.fn(() => true)
    })

    it('shows the unverified badge and explanation', () => {
      const wrapper = mountEdit(own)
      expect(wrapper.find('[data-testid="unverified-badge"]').exists()).toBe(true)
      expect(wrapper.text()).toContain('un administrateur va le vérifier')
    })

    it('does not show the badge on a verified ingredient', () => {
      const wrapper = mountEdit({ ...own, is_verified: true })
      expect(wrapper.find('[data-testid="unverified-badge"]').exists()).toBe(false)
    })

    it('offers deletion only when deletable and allowed by the API', () => {
      expect(mountEdit(own).find('[data-testid="ingredient-modal-delete"]').exists()).toBe(true)
      expect(mountEdit({ ...own, can_edit: false }).find('[data-testid="ingredient-modal-delete"]').exists()).toBe(false)
      expect(mountEdit(own, false).find('[data-testid="ingredient-modal-delete"]').exists()).toBe(false)
    })

    it('deletes the ingredient after confirmation and emits it', async () => {
      vi.mocked(deleteIngredient).mockResolvedValue(undefined as never)
      const wrapper = mountEdit(own)
      await wrapper.get('[data-testid="ingredient-modal-delete"]').trigger('click')
      await flushPromises()
      expect(deleteIngredient).toHaveBeenCalledWith(12)
      expect(wrapper.emitted('deleted')?.[0]).toEqual([12])
    })

    it('explains when the ingredient is still used', async () => {
      vi.mocked(deleteIngredient).mockRejectedValue({ response: { status: 409 } })
      const wrapper = mountEdit(own)
      await wrapper.get('[data-testid="ingredient-modal-delete"]').trigger('click')
      await flushPromises()
      expect(wrapper.get('[role="alert"]').text()).toContain('utilisé par des recettes')
      expect(wrapper.emitted('deleted')).toBeUndefined()
    })
  })
})
