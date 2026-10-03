import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/planning', () => ({
  listMealPlanEntries: vi.fn(),
  getNutritionSummary: vi.fn(),
}))
vi.mock('../../src/api/shopping', () => ({
  listShoppingLists: vi.fn(),
}))
vi.mock('../../src/api/auth', () => ({
  fetchLegalInfo: vi.fn(),
}))

import { fetchLegalInfo } from '../../src/api/auth'
import { getNutritionSummary, listMealPlanEntries } from '../../src/api/planning'
import { listShoppingLists } from '../../src/api/shopping'
import HomeWeekStrip from '../../src/components/planning/HomeWeekStrip.vue'

function mountStrip() {
  return mount(HomeWeekStrip, {
    global: {
      plugins: [i18n],
      stubs: {
        RouterLink: { props: ['to'], template: '<a><slot /></a>' },
        AddMealModal: {
          name: 'AddMealModal',
          props: ['date', 'mealType'],
          emits: ['close', 'added'],
          template: '<div class="stub-add-meal" />',
        },
      },
    },
  })
}

function isoToday() {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  vi.clearAllMocks()
})

describe('HomeWeekStrip', () => {
  it("lists today's meals as photo tiles in meal order and offers to plan when a day is empty", async () => {
    vi.mocked(listMealPlanEntries).mockResolvedValue([
      {
        id: 2,
        recipe: 20,
        recipe_title: 'Soupe',
        recipe_image: null,
        recipe_image_url: '',
        date: isoToday(),
        meal_type: 'dinner',
        servings: 2,
      },
      {
        id: 1,
        recipe: 10,
        recipe_title: 'Tartines',
        recipe_image: null,
        recipe_image_url: 'https://example.com/tartines.jpg',
        date: isoToday(),
        meal_type: 'breakfast',
        servings: 1,
      },
    ])
    vi.mocked(listShoppingLists).mockResolvedValue({ results: [], count: 0, next: null, previous: null })
    vi.mocked(getNutritionSummary).mockResolvedValue({ deficiencies: [] } as never)
    vi.mocked(fetchLegalInfo).mockResolvedValue({ planning_snack_enabled: false } as never)

    const wrapper = await mountStrip()
    await flushPromises()

    const tiles = wrapper.findAll('.week-tile:not(.week-slot-empty)')
    expect(tiles.map((tile) => tile.text())).toEqual([expect.stringContaining('Tartines'), expect.stringContaining('Soupe')])
    // Tartines has a photo (uses the image_url fallback), Soupe falls back to the placeholder.
    expect(tiles[0].find('img').attributes('src')).toBe('https://example.com/tartines.jpg')
    expect(tiles[1].find('img').exists()).toBe(false)
    expect(tiles[1].find('.week-tile-placeholder').exists()).toBe(true)

    // Today has breakfast and dinner filled, so only lunch gets an add-slot button; tomorrow
    // is fully empty, so it gets one per meal type (snack excluded, disabled by default).
    const emptySlots = wrapper.findAll('.week-slot-empty')
    expect(emptySlots).toHaveLength(4)
    expect(emptySlots.map((slot) => slot.text())).toEqual(
      expect.arrayContaining(['Déjeuner', 'Petit-déjeuner', 'Déjeuner', 'Dîner']),
    )
  })

  it('offers a snack add-slot when the instance enables it', async () => {
    vi.mocked(listMealPlanEntries).mockResolvedValue([])
    vi.mocked(listShoppingLists).mockResolvedValue({ results: [], count: 0, next: null, previous: null })
    vi.mocked(getNutritionSummary).mockResolvedValue({ deficiencies: [] } as never)
    vi.mocked(fetchLegalInfo).mockResolvedValue({ planning_snack_enabled: true } as never)

    const wrapper = await mountStrip()
    await flushPromises()

    expect(wrapper.findAll('.week-slot-empty')).toHaveLength(8) // 4 meal types x 2 days
    expect(wrapper.text()).toContain('Collation')
  })

  it('still renders when some requests fail', async () => {
    vi.mocked(listMealPlanEntries).mockResolvedValue([])
    vi.mocked(listShoppingLists).mockRejectedValue(new Error('boom'))
    vi.mocked(getNutritionSummary).mockRejectedValue(new Error('boom'))
    vi.mocked(fetchLegalInfo).mockRejectedValue(new Error('boom'))

    const wrapper = await mountStrip()
    await flushPromises()

    expect(wrapper.text()).toContain('Cette semaine')
    expect(wrapper.text()).not.toContain('Dernière liste de courses')
  })

  it('opens the quick-create menu and offers manual creation or URL import', async () => {
    vi.mocked(listMealPlanEntries).mockResolvedValue([])
    vi.mocked(listShoppingLists).mockResolvedValue({ results: [], count: 0, next: null, previous: null })
    vi.mocked(getNutritionSummary).mockResolvedValue({ deficiencies: [] } as never)
    vi.mocked(fetchLegalInfo).mockResolvedValue({ planning_snack_enabled: false } as never)

    const wrapper = await mountStrip()
    await flushPromises()

    expect(wrapper.find('#home-create-panel').classes()).not.toContain('is-open')

    await wrapper.find('.create-toggle').trigger('click')
    expect(wrapper.find('#home-create-panel').classes()).toContain('is-open')

    const manualLink = wrapper.findAll('a').find((a) => a.text().includes('Créer manuellement'))
    expect(manualLink).toBeTruthy()

    const importLink = wrapper.findAll('.create-link').find((el) => el.text().includes('Importer depuis une URL'))
    await importLink?.trigger('click')

    expect(wrapper.emitted('open-import')).toHaveLength(1)
    expect(wrapper.find('#home-create-panel').classes()).not.toContain('is-open')
  })

  it('opens the add-meal dialog for an empty slot and refreshes the tiles once a meal is added', async () => {
    vi.mocked(listMealPlanEntries).mockResolvedValue([])
    vi.mocked(listShoppingLists).mockResolvedValue({ results: [], count: 0, next: null, previous: null })
    vi.mocked(getNutritionSummary).mockResolvedValue({ deficiencies: [] } as never)
    vi.mocked(fetchLegalInfo).mockResolvedValue({ planning_snack_enabled: false } as never)

    const wrapper = await mountStrip()
    await flushPromises()
    expect(wrapper.findComponent({ name: 'AddMealModal' }).exists()).toBe(false)

    // Today's slots come first: breakfast, lunch, dinner.
    await wrapper.findAll('.week-slot-empty')[1].trigger('click')
    const modal = wrapper.findComponent({ name: 'AddMealModal' })
    expect(modal.props()).toEqual({ date: isoToday(), mealType: 'lunch' })

    vi.mocked(listMealPlanEntries).mockResolvedValue([
      {
        id: 3,
        recipe: 30,
        recipe_title: 'Salade',
        recipe_image: null,
        recipe_image_url: '',
        date: isoToday(),
        meal_type: 'lunch',
        servings: 2,
      },
    ])
    modal.vm.$emit('added')
    await flushPromises()

    expect(wrapper.findComponent({ name: 'AddMealModal' }).exists()).toBe(false)
    expect(wrapper.find('.week-tile:not(.week-slot-empty)').text()).toContain('Salade')
  })
})
