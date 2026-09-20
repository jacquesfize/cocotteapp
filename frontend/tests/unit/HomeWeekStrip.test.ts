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

import { getNutritionSummary, listMealPlanEntries } from '../../src/api/planning'
import { listShoppingLists } from '../../src/api/shopping'
import HomeWeekStrip from '../../src/components/HomeWeekStrip.vue'

function mountStrip() {
  return mount(HomeWeekStrip, {
    global: {
      plugins: [i18n],
      stubs: { RouterLink: { props: ['to'], template: '<a><slot /></a>' } },
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
  it("lists today's meals in meal order and offers to plan when a day is empty", async () => {
    vi.mocked(listMealPlanEntries).mockResolvedValue([
      { id: 2, recipe: 20, recipe_title: 'Soupe', date: isoToday(), meal_type: 'dinner', servings: 2 },
      { id: 1, recipe: 10, recipe_title: 'Tartines', date: isoToday(), meal_type: 'breakfast', servings: 1 },
    ])
    vi.mocked(listShoppingLists).mockResolvedValue({ results: [], count: 0, next: null, previous: null })
    vi.mocked(getNutritionSummary).mockResolvedValue({ deficiencies: [] } as never)

    const wrapper = await mountStrip()
    await flushPromises()

    const items = wrapper.findAll('li').map((li) => li.text())
    expect(items[0]).toContain('Tartines')
    expect(items[1]).toContain('Soupe')
    expect(wrapper.text()).toContain('Planifier un repas') // tomorrow is empty
  })

  it('still renders when some requests fail', async () => {
    vi.mocked(listMealPlanEntries).mockResolvedValue([])
    vi.mocked(listShoppingLists).mockRejectedValue(new Error('boom'))
    vi.mocked(getNutritionSummary).mockRejectedValue(new Error('boom'))

    const wrapper = await mountStrip()
    await flushPromises()

    expect(wrapper.text()).toContain('Cette semaine')
    expect(wrapper.text()).not.toContain('Dernière liste de courses')
  })
})
