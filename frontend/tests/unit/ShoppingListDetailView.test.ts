import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/shopping', () => ({
  getShoppingList: vi.fn(),
  exportShoppingList: vi.fn(),
  markOwned: vi.fn(),
}))

vi.mock('../../src/offline/sync', () => ({
  QUEUE_FLUSHED_EVENT: 'cocotte:queue-flushed',
  isMarkOwnedQueued: vi.fn().mockResolvedValue(false),
  isNetworkError: vi.fn().mockReturnValue(false),
  queueMarkOwned: vi.fn(),
}))

vi.mock('../../src/utils/download', () => ({
  downloadBlob: vi.fn(),
}))

import { exportShoppingList, getShoppingList } from '../../src/api/shopping'
import { downloadBlob } from '../../src/utils/download'
import ShoppingListDetailView from '../../src/views/ShoppingListDetailView.vue'

const list = {
  id: 1,
  name: 'Liste de courses',
  items: [
    {
      id: 1,
      ingredient: { id: 10, name: 'Carotte' },
      quantity: 400,
      unit: 'g',
      is_owned: false,
    },
  ],
}

function mountView() {
  return mount(ShoppingListDetailView, {
    props: { id: 1 },
    global: { plugins: [i18n] },
  })
}

describe('ShoppingListDetailView export/share', () => {
  const originalShare = (navigator as unknown as { share?: unknown }).share

  beforeEach(() => {
    vi.mocked(getShoppingList).mockReset().mockResolvedValue(list as never)
    vi.mocked(exportShoppingList).mockReset().mockResolvedValue({ content: '- 400 g Carotte' })
    vi.mocked(downloadBlob).mockReset()
  })

  afterEach(() => {
    if (originalShare === undefined) {
      delete (navigator as unknown as { share?: unknown }).share
    } else {
      ;(navigator as unknown as { share?: unknown }).share = originalShare
    }
  })

  it('shares the list content via navigator.share when available', async () => {
    const share = vi.fn().mockResolvedValue(undefined)
    ;(navigator as unknown as { share?: unknown }).share = share

    const wrapper = mountView()
    await flushPromises()
    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(share).toHaveBeenCalledWith({ title: 'Liste de courses', text: '- 400 g Carotte' })
    expect(downloadBlob).not.toHaveBeenCalled()
  })

  it('does nothing when the user cancels the share sheet (AbortError)', async () => {
    const abortError = Object.assign(new Error('cancelled'), { name: 'AbortError' })
    const share = vi.fn().mockRejectedValue(abortError)
    ;(navigator as unknown as { share?: unknown }).share = share

    const wrapper = mountView()
    await flushPromises()
    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(share).toHaveBeenCalled()
    expect(downloadBlob).not.toHaveBeenCalled()
  })

  it('falls back to downloading a .txt file when navigator.share is unavailable', async () => {
    delete (navigator as unknown as { share?: unknown }).share

    const wrapper = mountView()
    await flushPromises()
    await wrapper.find('button').trigger('click')
    await flushPromises()

    expect(downloadBlob).toHaveBeenCalledTimes(1)
    const [blob, filename] = vi.mocked(downloadBlob).mock.calls[0]
    expect(filename).toBe('Liste de courses.txt')
    expect(blob.type).toBe('text/plain;charset=utf-8')
  })
})
