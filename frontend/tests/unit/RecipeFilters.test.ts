import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { defineComponent, reactive } from 'vue'
import { i18n } from '../../src/i18n'
import RecipeFilters, { type RecipeFilterValues } from '../../src/components/RecipeFilters.vue'

function emptyFilters(overrides: Partial<RecipeFilterValues> = {}): RecipeFilterValues {
  return {
    search: '',
    diet_type: '',
    max_prep_time: '',
    max_cook_time: '',
    ingredients: '',
    in_season: false,
    carbon_level: '',
    ...overrides,
  }
}

function mountFilters(overrides: Partial<RecipeFilterValues> = {}) {
  const state = reactive({ filters: emptyFilters(overrides) })
  const Host = defineComponent({
    components: { RecipeFilters },
    setup: () => ({ state }),
    template: '<RecipeFilters v-model="state.filters" />',
  })
  const wrapper = mount(Host, { global: { plugins: [i18n] } })
  return { wrapper, state }
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
})

describe('RecipeFilters', () => {
  it('is collapsed by default, without badge', () => {
    const { wrapper } = mountFilters()
    expect(wrapper.find('#recipe-filters-panel').isVisible()).toBe(false)
    expect(wrapper.find('[data-testid="filters-badge"]').exists()).toBe(false)
    expect(wrapper.find('button.toggle').attributes('aria-expanded')).toBe('false')
  })

  it('toggles the panel from the Filtres button', async () => {
    const { wrapper } = mountFilters()
    await wrapper.find('button.toggle').trigger('click')
    expect(wrapper.find('#recipe-filters-panel').isVisible()).toBe(true)
    expect(wrapper.find('button.toggle').attributes('aria-expanded')).toBe('true')
    await wrapper.find('button.toggle').trigger('click')
    expect(wrapper.find('button.toggle').attributes('aria-expanded')).toBe('false')
    expect((wrapper.find('#recipe-filters-panel').element as HTMLElement).style.display).toBe('none')
  })

  it('shows the number of active filters', () => {
    const { wrapper } = mountFilters({ search: 'tarte', in_season: true, max_prep_time: 20 })
    expect(wrapper.find('[data-testid="filters-badge"]').text()).toBe('3')
  })

  it('updates the model when a field is edited', async () => {
    const { wrapper, state } = mountFilters()
    await wrapper.find('button.toggle').trigger('click')
    await wrapper.find('#search').setValue('soupe')
    expect(state.filters.search).toBe('soupe')
    expect(wrapper.find('[data-testid="filters-badge"]').text()).toBe('1')
  })

  it('resets every filter', async () => {
    const { wrapper, state } = mountFilters({ search: 'tarte', diet_type: 'vegan', in_season: true })
    await wrapper.find('button.toggle').trigger('click')
    const reset = wrapper.findAll('.panel-footer button')[0]
    await reset.trigger('click')
    expect(state.filters).toEqual(emptyFilters())
    expect(wrapper.find('[data-testid="filters-badge"]').exists()).toBe(false)
    expect(reset.attributes('disabled')).toBeDefined()
  })
})
