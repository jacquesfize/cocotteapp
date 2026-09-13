import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../src/api/ingredients', () => ({
  createIngredient: vi.fn(),
}))

import { createIngredient } from '../../src/api/ingredients'
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
})
