import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/shopping', () => ({
  getShoppingList: vi.fn(),
  markOwned: vi.fn(),
  exportShoppingList: vi.fn(),
}))

vi.mock('../../src/offline/sync', () => ({
  isMarkOwnedQueued: vi.fn().mockResolvedValue(false),
  isNetworkError: vi.fn().mockReturnValue(false),
  queueMarkOwned: vi.fn(),
  QUEUE_FLUSHED_EVENT: 'cocotte:queue-flushed',
}))

import { getShoppingList, markOwned } from '../../src/api/shopping'
import ShoppingListDetailView from '../../src/views/ShoppingListDetailView.vue'
import type { ShoppingList } from '../../src/types/models'

function item(overrides: Record<string, unknown> = {}) {
  return {
    id: overrides.id ?? 1,
    quantity: 100,
    unit: 'g',
    is_owned: false,
    is_checked: false,
    ingredient: {
      id: 1,
      name: 'Carotte',
      slug: 'carotte',
      category: 'vegetable',
      default_unit: 'g',
      available_months: [],
    },
    ...overrides,
  }
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
  vi.mocked(getShoppingList).mockResolvedValue({
    id: 1,
    name: 'Liste de courses',
    created_at: '2026-01-01T00:00:00Z',
    items: [
      item({ id: 1, ingredient: { id: 1, name: 'Carotte', slug: 'carotte', category: 'vegetable', default_unit: 'g', available_months: [] } }),
      item({
        id: 2,
        ingredient: { id: 2, name: 'Lait', slug: 'lait', category: 'dairy', default_unit: 'ml', available_months: [] },
      }),
      item({
        id: 3,
        ingredient: { id: 3, name: 'Pomme', slug: 'pomme', category: 'fruit', default_unit: 'piece', available_months: [] },
      }),
    ],
  } as unknown as ShoppingList)
})

describe('ShoppingListDetailView', () => {
  it('groups items under a heading per ingredient category, in the canonical category order', async () => {
    const wrapper = mount(ShoppingListDetailView, {
      props: { id: 1 },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    const headings = wrapper.findAll('.category-title').map((h) => h.text())
    // Légume (vegetable), Fruit, Produit laitier (dairy) in that canonical order even though
    // the mocked API response lists vegetable/dairy/fruit.
    expect(headings).toEqual(['Légume', 'Fruit', 'Produit laitier'])

    const groups = wrapper.findAll('.category-group')
    expect(groups[0].text()).toContain('Carotte')
    expect(groups[1].text()).toContain('Pomme')
    expect(groups[2].text()).toContain('Lait')
  })

  it('lets an owned item be unchecked, posting owned: false', async () => {
    vi.mocked(markOwned).mockResolvedValue({} as never)
    const wrapper = mount(ShoppingListDetailView, {
      props: { id: 1 },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    const checkboxes = wrapper.findAll('input[type="checkbox"]')
    const carrotCheckbox = checkboxes[0]

    // Tick it on (first interaction, going from unowned to owned).
    await carrotCheckbox.setValue(true)
    await flushPromises()
    expect(markOwned).toHaveBeenCalledWith(1, [1], true)
    expect(carrotCheckbox.attributes('disabled')).toBeUndefined()

    // Now untick it — the checkbox must not be disabled, and the API call must carry
    // `owned: false` so the fix for the "can't uncheck" bug actually reaches the backend.
    await carrotCheckbox.setValue(false)
    await flushPromises()
    expect(markOwned).toHaveBeenLastCalledWith(1, [1], false)
    expect(carrotCheckbox.attributes('disabled')).toBeUndefined()
  })

  it('reverts the optimistic uncheck without queuing anything when offline', async () => {
    const { isNetworkError, queueMarkOwned } = await import('../../src/offline/sync')
    vi.mocked(isNetworkError).mockReturnValue(true)
    vi.mocked(markOwned).mockRejectedValue({ message: 'Network Error' })
    vi.mocked(getShoppingList).mockResolvedValue({
      id: 1,
      name: 'Liste de courses',
      created_at: '2026-01-01T00:00:00Z',
      items: [
        item({
          id: 2,
          is_owned: true,
          ingredient: { id: 2, name: 'Lait', slug: 'lait', category: 'dairy', default_unit: 'ml', available_months: [] },
        }),
      ],
    } as unknown as ShoppingList)

    const wrapper = mount(ShoppingListDetailView, {
      props: { id: 1 },
      global: { plugins: [i18n] },
    })
    await flushPromises()

    const milkCheckbox = wrapper.find('input[type="checkbox"]')
    // Simulate an already-owned item being unchecked while offline: the optimistic uncheck
    // fails to sync (the write queue only ever replays "mark owned", never an unmark), so it
    // must bounce back to checked rather than silently losing state or queuing the wrong thing.
    await milkCheckbox.setValue(false)
    await flushPromises()

    expect((milkCheckbox.element as HTMLInputElement).checked).toBe(true)
    expect(queueMarkOwned).not.toHaveBeenCalled()
  })
})
