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
vi.mock('../../src/api/auth', () => ({
  fetchLegalInfo: vi.fn(),
}))

import { fetchLegalInfo } from '../../src/api/auth'
import { getNutritionSummary, listMealPlanEntries, listSharedWithMe } from '../../src/api/planning'
import PlanningView from '../../src/views/PlanningView.vue'
import type { LegalInfo, PlanningShareReceived } from '../../src/types/models'

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

function legalInfo(overrides?: Partial<LegalInfo>): LegalInfo {
  return {
    policy_version: '1',
    publisher_name: '',
    publisher_address: '',
    contact_email: '',
    host_name: '',
    host_address: '',
    privacy_contact_email: '',
    inactive_retention_days: 730,
    planning_snack_enabled: false,
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
  // La collation est désactivée par défaut au niveau de l'instance (voir /api/auth/legal/).
  vi.mocked(fetchLegalInfo).mockResolvedValue(legalInfo())
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

describe('PlanningView calendar views', () => {
  it('shows the week view by default and switches to the month grid', async () => {
    const wrapper = await mountPlanningView()
    await flushPromises()

    expect(wrapper.findAll('.view-btn')).toHaveLength(2)
    expect(wrapper.find('[data-view="cards"]').exists()).toBe(false)
    expect(wrapper.find('.agenda-week').exists()).toBe(true)
    // 3 meal types (snack is instance-disabled by default) x 7 days.
    expect(wrapper.findAll('.agenda-week .meal-slot-stub')).toHaveLength(21)

    await wrapper.find('[data-view="month"]').trigger('click')
    await flushPromises()
    expect(wrapper.find('.agenda-month').exists()).toBe(true)
    const now = new Date()
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
    expect(wrapper.findAll('.month-cell:not(.empty)')).toHaveLength(daysInMonth)
  })

  it('loads the whole month range in month view and keeps PDF/shopping actions', async () => {
    const wrapper = await mountPlanningView()
    await flushPromises()
    await wrapper.find('[data-view="month"]').trigger('click')
    await flushPromises()

    const now = new Date()
    const pad = (n: number) => String(n).padStart(2, '0')
    const last = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate()
    expect(listMealPlanEntries).toHaveBeenLastCalledWith(
      expect.objectContaining({
        date_after: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-01`,
        date_before: `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(last)}`,
      }),
    )
    expect(wrapper.text()).toContain('PDF')
  })
})

describe('PlanningView snack meal slot (instance toggle)', () => {
  it('hides the snack row by default (instance setting disabled)', async () => {
    const wrapper = await mountPlanningView()
    await flushPromises()

    expect(fetchLegalInfo).toHaveBeenCalled()
    expect(wrapper.find('[data-meal-type="snack"]').exists()).toBe(false)
    expect(wrapper.findAll('.agenda-row-head').map((el) => el.text())).not.toContain(
      i18n.global.t('mealType.snack'),
    )
    expect(wrapper.findAll('.agenda-week .meal-slot-stub')).toHaveLength(21)
  })

  it('shows the snack row once the instance enables it', async () => {
    vi.mocked(fetchLegalInfo).mockResolvedValue(legalInfo({ planning_snack_enabled: true }))

    const wrapper = await mountPlanningView()
    await flushPromises()

    expect(wrapper.find('[data-meal-type="snack"]').exists()).toBe(true)
    expect(wrapper.findAll('.agenda-week .meal-slot-stub')).toHaveLength(28)
  })
})

describe('PlanningView nutrition modal', () => {
  it('opens from a button with the alerts and closes via Escape, outside click and close button', async () => {
    vi.mocked(getNutritionSummary).mockResolvedValue({
      totals: {} as never,
      daily_average: {} as never,
      deficiencies: [{ nutrient: 'iron', amount: 1, minimum: 2, unit: 'mg' }] as never,
      carbon_footprint_kg_co2e: 3,
      carbon_footprint_daily_average_kg_co2e: 0,
    } as never)
    const wrapper = await mountPlanningView()
    await flushPromises()
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)

    const open = async () => {
      await wrapper.find('.nutrition-btn').trigger('click')
      expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
    }
    await open()
    expect(wrapper.find('.deficiency-banner').exists()).toBe(true)
    expect(wrapper.find('[role="dialog"]').text()).toContain('3.0 kg CO2e')

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushPromises()
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)

    await open()
    await wrapper.find('.base-modal-overlay').trigger('mousedown')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)

    await open()
    await wrapper.find('.base-modal-close').trigger('click')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
  })

  it('hides the deficiency banner when there are none (e.g. NUTRITION_ALERTS_ENABLED=False)', async () => {
    // beforeEach already mocks getNutritionSummary with an empty deficiencies list, matching
    // what the backend returns when the instance-level nutrition alert toggle is off.
    const wrapper = await mountPlanningView()
    await flushPromises()

    await wrapper.find('.nutrition-btn').trigger('click')

    expect(wrapper.find('[role="dialog"]').exists()).toBe(true)
    expect(wrapper.find('.deficiency-banner').exists()).toBe(false)
  })
})
