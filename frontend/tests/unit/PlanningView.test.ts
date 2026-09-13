import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/planning', () => ({
  listMealPlanEntries: vi.fn(),
  getNutritionSummary: vi.fn(),
  downloadWeekPdf: vi.fn(),
  listSharedWithMe: vi.fn(),
}))
vi.mock('../../src/api/shopping', () => ({
  createShoppingList: vi.fn(),
}))

import { getNutritionSummary, listMealPlanEntries, listSharedWithMe } from '../../src/api/planning'
import PlanningView from '../../src/views/PlanningView.vue'
import type { PlanningShareReceived } from '../../src/types/models'

async function mountPlanningView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/planning', component: PlanningView }],
  })
  router.push('/planning')
  await router.isReady()

  return mount(PlanningView, {
    global: {
      plugins: [i18n, router],
      stubs: {
        MealSlot: {
          props: ['date', 'mealType', 'entries', 'owner', 'readOnly'],
          template: '<div class="meal-slot-stub" :data-owner="owner" :data-readonly="readOnly" />',
        },
      },
    },
  })
}

function sharedAgenda(overrides?: Partial<PlanningShareReceived>): PlanningShareReceived {
  return {
    id: 1,
    owner: 42,
    owner_username: 'alice',
    owner_email: 'alice@example.com',
    permission: 'read',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  vi.clearAllMocks()
  vi.mocked(listMealPlanEntries).mockResolvedValue([])
  vi.mocked(getNutritionSummary).mockResolvedValue({
    totals: {} as never,
    daily_average: {} as never,
    deficiencies: [],
    carbon_footprint_kg_co2e: 0,
    carbon_footprint_daily_average_kg_co2e: 0,
  })
  vi.mocked(listSharedWithMe).mockResolvedValue([])
})

describe('PlanningView agenda sharing', () => {
  it('does not show an agenda selector when nothing is shared with me', async () => {
    const wrapper = await mountPlanningView()
    await flushPromises()

    expect(wrapper.find('#agenda-select').exists()).toBe(false)
  })

  it('lists shared agendas and switches to one on selection', async () => {
    vi.mocked(listSharedWithMe).mockResolvedValue([sharedAgenda({ permission: 'read' })])

    const wrapper = await mountPlanningView()
    await flushPromises()

    const select = wrapper.find('#agenda-select')
    expect(select.exists()).toBe(true)
    expect(select.text()).toContain('alice')
    expect(select.text()).toContain('lecture seule')

    await select.setValue('42')
    await flushPromises()

    expect(listMealPlanEntries).toHaveBeenLastCalledWith(expect.objectContaining({ owner: 42 }))
    const slot = wrapper.find('.meal-slot-stub')
    expect(slot.attributes('data-readonly')).toBe('true')
    expect(slot.attributes('data-owner')).toBe('42')
  })

  it('keeps meal editing enabled for a write share', async () => {
    vi.mocked(listSharedWithMe).mockResolvedValue([sharedAgenda({ permission: 'write' })])

    const wrapper = await mountPlanningView()
    await flushPromises()

    await wrapper.find('#agenda-select').setValue('42')
    await flushPromises()

    const slot = wrapper.find('.meal-slot-stub')
    expect(slot.attributes('data-readonly')).toBe('false')
  })
})
