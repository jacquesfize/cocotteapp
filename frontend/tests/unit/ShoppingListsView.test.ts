import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/shopping', () => ({
  listShoppingLists: vi.fn(),
  deleteShoppingList: vi.fn(),
}))

import { deleteShoppingList, listShoppingLists } from '../../src/api/shopping'
import ShoppingListsView from '../../src/views/shopping/ShoppingListsView.vue'
import type { ShoppingList } from '../../src/types/models'

function list(overrides: Record<string, unknown> = {}): ShoppingList {
  return {
    id: 1,
    name: 'Liste de courses',
    created_at: '2026-01-01T00:00:00Z',
    items: [],
    ...overrides,
  } as unknown as ShoppingList
}

function item(isOwned: boolean) {
  return {
    id: Math.random(),
    quantity: 1,
    unit: 'g',
    is_owned: isOwned,
    is_checked: false,
    ingredient: { id: 1, name: 'Carotte', slug: 'carotte', category: 'vegetable', default_unit: 'g', available_months: [] },
  } as unknown as ShoppingList['items'][number]
}

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/shopping-lists', name: 'shopping-lists', component: ShoppingListsView },
      { path: '/shopping-lists/:id', name: 'shopping-list-detail', component: { template: '<div />' } },
    ],
  })
  router.push('/shopping-lists')
  await router.isReady()

  const wrapper = mount(ShoppingListsView, {
    global: {
      plugins: [i18n, router],
      stubs: {
        RouterLink: { props: ['to'], template: '<a :data-to="JSON.stringify(to)"><slot /></a>' },
      },
    },
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  vi.clearAllMocks()
  vi.mocked(deleteShoppingList).mockResolvedValue(undefined as never)
})

describe('ShoppingListsView', () => {
  it('shows a progress summary per list based on its items', async () => {
    vi.mocked(listShoppingLists).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [list({ items: [item(true), item(true), item(false)] })],
    })

    const wrapper = await mountView()

    expect(wrapper.text()).toContain('2/3 achetés')
    const link = wrapper.find('a[data-to]')
    expect(link.attributes('data-to')).toContain('"name":"shopping-list-detail"')
  })

  it('omits the progress summary for an empty list', async () => {
    vi.mocked(listShoppingLists).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [list({ items: [] })],
    })

    const wrapper = await mountView()

    expect(wrapper.text()).not.toContain('achetés')
    expect(wrapper.find('.list-progress-track').exists()).toBe(false)
  })

  it('deletes a list and reloads when the delete button is clicked', async () => {
    vi.mocked(listShoppingLists).mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [list({ id: 5 })],
    })

    const wrapper = await mountView()
    await wrapper.find('.list-delete').trigger('click')
    await flushPromises()

    expect(deleteShoppingList).toHaveBeenCalledWith(5)
    expect(listShoppingLists).toHaveBeenCalledTimes(2)
  })
})
