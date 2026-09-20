import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/ingredients', () => ({
  listIngredients: vi.fn(),
  createIngredient: vi.fn(),
  updateIngredient: vi.fn(),
  deleteIngredient: vi.fn(),
  suggestIngredientNutrition: vi.fn(),
}))

import {
  deleteIngredient,
  listIngredients,
  updateIngredient,
} from '../../src/api/ingredients'
import AdminIngredientsView from '../../src/views/AdminIngredientsView.vue'
import type { Ingredient } from '../../src/types/models'

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/admin/ingredients', component: AdminIngredientsView }],
  })
  router.push('/admin/ingredients')
  await router.isReady()
  return mount(AdminIngredientsView, { global: { plugins: [i18n, router] } })
}

function ingredient(overrides?: Partial<Ingredient>): Ingredient {
  return {
    id: 1,
    name: 'ail',
    slug: 'ail',
    category: 'vegetable',
    default_unit: 'g',
    available_months: [],
    translations: { en: 'garlic' },
    calories_kcal: 149,
    protein_g: 6,
    carbs_g: 33,
    fat_g: 0.5,
    fiber_g: 2,
    iron_mg: 1.7,
    vitamin_b12_ug: 0,
    calcium_mg: 181,
    omega3_g: 0,
    zinc_mg: 1.2,
    carbon_kg_co2e_per_kg: 0.38,
    ...overrides,
  }
}

const page = (results: Ingredient[]) => ({ results, count: results.length, next: null, previous: null })

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
  window.confirm = vi.fn(() => true)
})

describe('AdminIngredientsView', () => {
  it('lists ingredients with their English name', async () => {
    vi.mocked(listIngredients).mockResolvedValue(page([ingredient()]))
    const wrapper = await mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('ail')
    expect(wrapper.text()).toContain('garlic')
  })

  it('edits an ingredient through the modal', async () => {
    vi.mocked(listIngredients).mockResolvedValue(page([ingredient()]))
    vi.mocked(updateIngredient).mockResolvedValue(ingredient({ name: 'ail rose' }))
    const wrapper = await mountView()
    await flushPromises()

    await wrapper.findAll('button').find((b) => b.text() === 'Modifier')?.trigger('click')
    await flushPromises()
    await wrapper.find('#ingredient-modal-name-en').setValue('pink garlic')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(updateIngredient).toHaveBeenCalledTimes(1)
    const [id, payload] = vi.mocked(updateIngredient).mock.calls[0]
    expect(id).toBe(1)
    expect(payload.translations).toEqual({ en: 'pink garlic' })
    expect(wrapper.find('form').exists()).toBe(false)
  })

  it('deletes an ingredient after confirmation', async () => {
    vi.mocked(listIngredients).mockResolvedValue(page([ingredient()]))
    vi.mocked(deleteIngredient).mockResolvedValue(undefined as never)
    const wrapper = await mountView()
    await flushPromises()

    await wrapper.find('button.danger').trigger('click')
    await flushPromises()

    expect(deleteIngredient).toHaveBeenCalledWith(1)
  })

  it('shows a clear message when the ingredient is in use', async () => {
    vi.mocked(listIngredients).mockResolvedValue(page([ingredient()]))
    vi.mocked(deleteIngredient).mockRejectedValue({ response: { status: 409 } })
    const wrapper = await mountView()
    await flushPromises()

    await wrapper.find('button.danger').trigger('click')
    await flushPromises()

    expect(wrapper.find('[role="alert"]').text()).toContain('utilisé par des recettes')
  })

  it('shows an access-denied message on 403', async () => {
    vi.mocked(listIngredients).mockRejectedValue({ response: { status: 403 } })
    const wrapper = await mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Accès réservé aux administrateurs')
  })
})
