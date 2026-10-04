import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, reactive } from 'vue'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/allergens', () => ({
  listAllergens: vi.fn().mockResolvedValue([
    { slug: 'peanut', name: 'Arachide' },
    { slug: 'lactose', name: 'Lactose' },
    { slug: 'gluten', name: 'Gluten' },
  ]),
}))
vi.mock('../../src/api/cookware', () => ({
  listCookware: vi.fn().mockResolvedValue([
    { id: 1, name: 'Four', slug: 'four', translations: { en: 'oven' } },
    { id: 2, name: 'Friteuse à air', slug: 'friteuse-a-air', translations: {} },
  ]),
  createCookware: vi.fn(),
}))
vi.mock('../../src/api/personalTags', () => ({
  listPersonalTags: vi.fn().mockResolvedValue([
    { id: 7, name: 'À tester', emoji: '🧪', color: 'blue' },
    { id: 8, name: 'Anniversaires', emoji: '', color: 'pink' },
  ]),
}))
vi.mock('../../src/api/ingredients', () => ({
  listIngredients: vi.fn().mockResolvedValue({
    results: [{ id: 1, name: 'Tomate' }, { id: 2, name: 'Oignon' }],
    count: 2,
    next: null,
    previous: null,
  }),
}))

import RecipeFilters, { type RecipeFilterValues } from '../../src/components/recipes/RecipeFilters.vue'
import { listIngredients } from '../../src/api/ingredients'
import { listPersonalTags } from '../../src/api/personalTags'
import { useAuthStore } from '../../src/stores/auth'

function emptyFilters(overrides: Partial<RecipeFilterValues> = {}): RecipeFilterValues {
  return {
    search: '',
    diet_type: '',
    max_prep_time: '',
    max_cook_time: '',
    ingredients: '',
    in_season: false,
    carbon_level: '',
    exclude_allergens: '',
    cookware: '',
    personal_tags: '',
    ...overrides,
  }
}

async function mountFilters(overrides: Partial<RecipeFilterValues> = {}, myAllergens: string[] = []) {
  const state = reactive({ filters: emptyFilters(overrides), myAllergens })
  const Host = defineComponent({
    components: { RecipeFilters },
    setup: () => ({ state }),
    template: '<RecipeFilters v-model="state.filters" :my-allergens="state.myAllergens" />',
  })
  const wrapper = mount(Host, { global: { plugins: [i18n] }, attachTo: document.body })
  await flushPromises()
  return { wrapper, state }
}

beforeEach(() => {
  setActivePinia(createPinia())
  i18n.global.locale.value = 'fr'
  vi.clearAllMocks()
})

describe('RecipeFilters', () => {
  it('is collapsed by default on mobile, without badge', async () => {
    const { wrapper } = await mountFilters()
    expect(wrapper.find('#recipe-filters-panel').classes()).not.toContain('is-open')
    expect(wrapper.find('[data-testid="filters-badge"]').exists()).toBe(false)
    expect(wrapper.find('button.toggle').attributes('aria-expanded')).toBe('false')
  })

  it('toggles the panel from the Filtres button', async () => {
    const { wrapper } = await mountFilters()
    await wrapper.find('button.toggle').trigger('click')
    expect(wrapper.find('#recipe-filters-panel').classes()).toContain('is-open')
    expect(wrapper.find('button.toggle').attributes('aria-expanded')).toBe('true')
    await wrapper.find('button.toggle').trigger('click')
    expect(wrapper.find('button.toggle').attributes('aria-expanded')).toBe('false')
    expect(wrapper.find('#recipe-filters-panel').classes()).not.toContain('is-open')
  })

  it('shows the number of active filters, on the toggle and in the panel header', async () => {
    const { wrapper } = await mountFilters({ search: 'tarte', in_season: true, max_prep_time: 20 })
    expect(wrapper.find('[data-testid="filters-badge"]').text()).toBe('3')
    expect(wrapper.find('.header-badge').text()).toBe('3')
  })

  it('updates the model when a field is edited', async () => {
    const { wrapper, state } = await mountFilters()
    await wrapper.find('#search').setValue('soupe')
    expect(state.filters.search).toBe('soupe')
    expect(wrapper.find('[data-testid="filters-badge"]').text()).toBe('1')
  })

  it('picks the diet from a radio list, including "all diets"', async () => {
    const { wrapper, state } = await mountFilters({ diet_type: 'vegan' })
    const radios = wrapper.findAll('input[type="radio"][name="diet_type"]')
    expect(radios).toHaveLength(3)
    expect((radios[2].element as HTMLInputElement).checked).toBe(true)
    await radios[1].setValue(true)
    expect(state.filters.diet_type).toBe('vegetarian')
    await radios[0].setValue(true)
    expect(state.filters.diet_type).toBe('')
  })

  it('sets max prep/cook times from sliders, the last notch meaning "no limit"', async () => {
    const { wrapper, state } = await mountFilters()
    const prep = wrapper.find('#max_prep')
    expect(prep.attributes('type')).toBe('range')
    expect(wrapper.text()).toContain('Sans limite')

    await prep.setValue('30')
    expect(state.filters.max_prep_time).toBe(30)
    expect(wrapper.text()).toContain('30 min')

    await wrapper.find('#max_cook').setValue('60')
    expect(state.filters.max_cook_time).toBe(60)

    await prep.setValue(prep.attributes('max'))
    expect(state.filters.max_prep_time).toBe('')
  })

  it('maps the carbon slider notches to any / low / medium / high', async () => {
    const { wrapper, state } = await mountFilters({ carbon_level: 'medium' })
    const slider = wrapper.find('#carbon_level')
    expect((slider.element as HTMLInputElement).value).toBe('2')
    expect(slider.classes()).toContain('carbon-medium')

    await slider.setValue('1')
    expect(state.filters.carbon_level).toBe('low')
    await slider.setValue('3')
    expect(state.filters.carbon_level).toBe('high')
    await slider.setValue('0')
    expect(state.filters.carbon_level).toBe('')
  })

  it('toggles "De saison" with an icon button carrying the long label as tooltip', async () => {
    const { wrapper, state } = await mountFilters()
    const toggle = wrapper.find('[data-testid="in-season-toggle"]')
    expect(toggle.text()).toBe('De saison')
    expect(toggle.attributes('title')).toBe('Ingrédients de saison uniquement')
    expect(toggle.attributes('aria-pressed')).toBe('false')

    await toggle.trigger('click')
    expect(state.filters.in_season).toBe(true)
    expect(toggle.attributes('aria-pressed')).toBe('true')
    expect(toggle.classes()).toContain('is-active')
  })

  it('shows selected ingredients as pills and removes one on click', async () => {
    const { wrapper, state } = await mountFilters({ ingredients: 'Tomate,Oignon' })
    const tags = wrapper.findAll('.multiselect__tag')
    expect(tags.map((tag) => tag.text())).toEqual(['Tomate', 'Oignon'])

    await tags[0].find('.multiselect__tag-icon').trigger('mousedown')
    expect(state.filters.ingredients).toBe('Oignon')
  })

  it('searches ingredients through the API and adds the picked one', async () => {
    vi.useFakeTimers()
    const { wrapper, state } = await mountFilters({ ingredients: 'Ail' })
    await wrapper.find('#ingredients').trigger('focus')
    await wrapper.find('#ingredients').setValue('tom')
    await vi.advanceTimersByTimeAsync(300)
    vi.useRealTimers()
    await flushPromises()

    expect(listIngredients).toHaveBeenLastCalledWith({ search: 'tom' })
    const option = wrapper.findAll('.multiselect__option').find((item) => item.text() === 'Tomate')
    // Clic natif : le trigger() de test-utils n'atteint pas le handler de l'option ici.
    option!.element.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()
    expect(state.filters.ingredients).toBe('Ail,Tomate')
  })

  it('lists excluded allergens as pills, with a shortcut to add the profile ones', async () => {
    const { wrapper, state } = await mountFilters({ exclude_allergens: 'gluten' }, ['peanut', 'lactose'])
    const allergenField = wrapper.findAll('.multiselect')[2]
    expect(allergenField.findAll('.multiselect__tag').map((tag) => tag.text())).toEqual(['Gluten'])

    await wrapper.find('[data-testid="add-my-allergens"]').trigger('click')
    expect(state.filters.exclude_allergens).toBe('gluten,peanut,lactose')
    expect(wrapper.find('[data-testid="add-my-allergens"]').exists()).toBe(false)

    await allergenField.findAll('.multiselect__tag-icon')[0].trigger('mousedown')
    expect(state.filters.exclude_allergens).toBe('peanut,lactose')
  })

  it('shows one removable chip per active filter, including one per list value', async () => {
    const { wrapper, state } = await mountFilters({
      diet_type: 'vegan',
      in_season: true,
      ingredients: 'Ail,Tomate',
      max_prep_time: 30,
      exclude_allergens: 'gluten,lactose',
    })
    // Le même résumé existe en double dans le DOM (copie mobile à côté du bouton, copie desktop
    // rattachée au panneau — cf. CSS .active-filters--mobile/--desktop) : jsdom n'évalue pas les
    // media queries, donc on se restreint à une seule des deux pour ne pas compter chaque pilule
    // deux fois.
    const chips = () => wrapper.findAll('.active-filters--mobile .filter-chip')
    expect(chips().map((chip) => chip.text())).toEqual([
      expect.stringContaining('Végan'),
      expect.stringContaining('De saison'),
      'Ail',
      'Tomate',
      expect.stringContaining('30 min'),
      'Gluten',
      'Lactose',
    ])

    await chips().find((chip) => chip.text() === 'Tomate')!.trigger('click')
    expect(state.filters.ingredients).toBe('Ail')

    await chips().find((chip) => chip.text() === 'Gluten')!.trigger('click')
    expect(state.filters.exclude_allergens).toBe('lactose')
  })

  it('resets every filter', async () => {
    const { wrapper, state } = await mountFilters({ search: 'tarte', diet_type: 'vegan', in_season: true })
    const reset = wrapper.find('button.reset')
    await reset.trigger('click')
    expect(state.filters).toEqual(emptyFilters())
    expect(wrapper.find('[data-testid="filters-badge"]').exists()).toBe(false)
    expect(reset.attributes('disabled')).toBeDefined()
  })

  it('filters by cookware slugs, shown as removable chips with their names', async () => {
    const { wrapper, state } = await mountFilters({ cookware: 'four' })

    const field = wrapper.find('#cookware').element.closest('.multiselect') as HTMLElement
    expect([...field.querySelectorAll('.multiselect__tag')].map((tag) => tag.textContent?.trim())).toEqual(['Four'])

    const chip = wrapper.findAll('.active-filters--mobile .filter-chip').find((c) => c.text() === 'Four')
    await chip!.trigger('click')
    expect(state.filters.cookware).toBe('')
  })

  it('hides the personal tags filter from anonymous visitors', async () => {
    const { wrapper } = await mountFilters()
    expect(listPersonalTags).not.toHaveBeenCalled()
    expect(wrapper.find('#personal_tags').exists()).toBe(false)
  })

  it('filters by the signed-in user\'s personal tags, shown as removable chips', async () => {
    useAuthStore().accessToken = 'token'
    const { wrapper, state } = await mountFilters({ personal_tags: '7' })

    const field = wrapper.find('#personal_tags').element.closest('.multiselect') as HTMLElement
    expect([...field.querySelectorAll('.multiselect__tag')].map((tag) => tag.textContent?.trim())).toEqual(['À tester'])

    const chip = wrapper.findAll('.active-filters--mobile .filter-chip').find((c) => c.text() === '🧪 À tester')
    await chip!.trigger('click')
    expect(state.filters.personal_tags).toBe('')
  })
})
