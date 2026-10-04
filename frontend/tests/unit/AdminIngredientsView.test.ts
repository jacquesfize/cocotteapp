import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/allergens', () => ({ listAllergens: vi.fn().mockResolvedValue([]) }))
vi.mock('../../src/api/ingredients', () => ({
  listIngredients: vi.fn(),
  createIngredient: vi.fn(),
  updateIngredient: vi.fn(),
  deleteIngredient: vi.fn(),
  mergeIngredient: vi.fn(),
  suggestIngredientNutrition: vi.fn(),
}))

import {
  deleteIngredient,
  listIngredients,
  mergeIngredient,
  updateIngredient,
} from '../../src/api/ingredients'
import IngredientPicker from '../../src/components/recipes/IngredientPicker.vue'
import AdminIngredientsView from '../../src/views/admin/AdminIngredientsView.vue'
import type { Ingredient } from '../../src/types/models'

async function mountView(path = '/admin/ingredients') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/admin/ingredients', component: AdminIngredientsView }],
  })
  router.push(path)
  await router.isReady()
  const wrapper = mount(AdminIngredientsView, { global: { plugins: [i18n, router] } })
  return Object.assign(wrapper, { router })
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
    is_verified: true,
    created_by: null,
    created_by_username: null,
    can_edit: true,
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
  it('lists ingredients without the removed columns', async () => {
    vi.mocked(listIngredients).mockResolvedValue(page([ingredient()]))
    const wrapper = await mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('ail')
    expect(wrapper.text()).not.toContain('garlic')
    expect(wrapper.text()).not.toContain('kcal')
    expect(wrapper.find('.admin-table .actions button').exists()).toBe(true)
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

  describe('review queue', () => {
    const unverified = () =>
      ingredient({ id: 5, name: 'ail des ours', is_verified: false, created_by: 3, created_by_username: 'alice' })

    it('shows the unverified count and a badge with the creator on unverified rows', async () => {
      vi.mocked(listIngredients).mockImplementation(async (params = {}) =>
        params.is_verified === false
          ? { ...page([unverified()]), count: 4 }
          : page([ingredient(), unverified()]),
      )
      const wrapper = await mountView()
      await flushPromises()

      expect(wrapper.get('[data-testid="filter-unverified"] .admin-filter-count').text()).toBe('4')
      const rows = wrapper.findAll('tbody tr')
      expect(rows[0].find('[data-testid="unverified-badge"]').exists()).toBe(false)
      expect(rows[0].find('[data-testid="verify"]').exists()).toBe(false)
      expect(rows[1].get('[data-testid="unverified-badge"]').text()).toContain('Non vérifié · ajouté par alice')
    })

    it('filters on unverified ingredients and keeps the filter in the URL', async () => {
      vi.mocked(listIngredients).mockResolvedValue(page([unverified()]))
      const wrapper = await mountView()
      await flushPromises()

      await wrapper.get('[data-testid="filter-unverified"]').trigger('click')
      await flushPromises()

      expect(listIngredients).toHaveBeenLastCalledWith({ is_verified: false })
      expect(wrapper.get('[data-testid="filter-unverified"]').attributes('aria-pressed')).toBe('true')
      expect(wrapper.router.currentRoute.value.query).toEqual({ is_verified: 'false' })
    })

    it('restores the filter from the URL', async () => {
      vi.mocked(listIngredients).mockResolvedValue(page([]))
      const wrapper = await mountView('/admin/ingredients?is_verified=false')
      await flushPromises()

      expect(listIngredients).toHaveBeenCalledWith({ is_verified: false })
      expect(wrapper.get('[data-testid="filter-unverified"]').attributes('aria-pressed')).toBe('true')
      expect(wrapper.text()).toContain('Rien à vérifier.')
    })

    it('verifies an ingredient and updates its row', async () => {
      vi.mocked(listIngredients).mockResolvedValue(page([unverified()]))
      vi.mocked(updateIngredient).mockResolvedValue({ ...unverified(), is_verified: true })
      const wrapper = await mountView()
      await flushPromises()

      await wrapper.get('[data-testid="verify"]').trigger('click')
      await flushPromises()

      expect(updateIngredient).toHaveBeenCalledWith(5, { is_verified: true })
      expect(wrapper.find('[data-testid="unverified-badge"]').exists()).toBe(false)
      expect(wrapper.find('[data-testid="verify"]').exists()).toBe(false)
      expect(wrapper.get('.admin-filter-count').text()).toBe('0')
    })

    it('merges an ingredient into the chosen target after explaining the consequences', async () => {
      const target = ingredient({ id: 1, name: 'ail' })
      vi.mocked(listIngredients).mockResolvedValue(page([target, unverified()]))
      vi.mocked(mergeIngredient).mockResolvedValue(target)
      const wrapper = await mountView()
      await flushPromises()

      await wrapper.findAll('[data-testid="merge"]')[1].trigger('click')
      const dialog = wrapper.get('[role="dialog"]')
      expect(dialog.text()).toContain('Fusionner « ail des ours » dans…')
      // Pas de création d'ingrédient depuis le choix de la cible.
      expect(wrapper.findComponent(IngredientPicker).props('selectOnly')).toBe(true)
      const submit = dialog.get('button[type="submit"]')
      expect(submit.attributes('disabled')).toBeDefined()

      wrapper.findComponent(IngredientPicker).vm.$emit('update:modelValue', target)
      await flushPromises()
      expect(wrapper.get('[data-testid="merge-confirm"]').text()).toContain(
        'Les recettes et listes de courses qui utilisent « ail des ours » passeront sur « ail »',
      )

      vi.mocked(listIngredients).mockClear()
      await wrapper.get('[role="dialog"] form').trigger('submit')
      await flushPromises()

      expect(mergeIngredient).toHaveBeenCalledWith(5, 1)
      expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
      expect(listIngredients).toHaveBeenCalled()
      expect(wrapper.get('[role="status"]').text()).toContain('« ail des ours » a été fusionné dans « ail »')
    })

    it('refuses to merge an ingredient into itself and reports API errors', async () => {
      vi.mocked(listIngredients).mockResolvedValue(page([unverified(), ingredient()]))
      vi.mocked(mergeIngredient).mockRejectedValue({ response: { status: 400 } })
      const wrapper = await mountView()
      await flushPromises()

      await wrapper.findAll('[data-testid="merge"]')[0].trigger('click')
      wrapper.findComponent(IngredientPicker).vm.$emit('update:modelValue', unverified())
      await flushPromises()
      expect(wrapper.get('[role="dialog"]').text()).toContain('Choisissez un autre élément')
      expect(wrapper.get('[role="dialog"] button[type="submit"]').attributes('disabled')).toBeDefined()

      wrapper.findComponent(IngredientPicker).vm.$emit('update:modelValue', ingredient())
      await flushPromises()
      await wrapper.get('[role="dialog"] form').trigger('submit')
      await flushPromises()

      expect(mergeIngredient).toHaveBeenCalledWith(5, 1)
      expect(wrapper.get('[role="dialog"] [role="alert"]').text()).toContain('Fusion impossible')
    })
  })
})
