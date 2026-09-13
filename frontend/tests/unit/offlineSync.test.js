import 'fake-indexeddb/auto'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../src/api/shopping', () => ({
  markOwned: vi.fn(),
}))

import { markOwned } from '../../src/api/shopping'
import { clearQueue } from '../../src/offline/db'
import {
  clearPrivateOfflineData,
  flushQueue,
  isMarkOwnedQueued,
  isNetworkError,
  QUEUE_FLUSHED_EVENT,
  queueMarkOwned,
} from '../../src/offline/sync'

beforeEach(async () => {
  vi.clearAllMocks()
  await clearQueue()
})

describe('isNetworkError', () => {
  it('is true for an axios error that never reached the server', () => {
    expect(isNetworkError({ message: 'Network Error' })).toBe(true)
  })

  it('is false for a real API error with a response', () => {
    expect(isNetworkError({ response: { status: 400 } })).toBe(false)
  })
})

describe('offline write queue', () => {
  it('queues a mark-owned write and reports it as pending only for that item', async () => {
    await queueMarkOwned(5, [42])

    expect(await isMarkOwnedQueued(5, 42)).toBe(true)
    expect(await isMarkOwnedQueued(5, 99)).toBe(false)
    expect(await isMarkOwnedQueued(6, 42)).toBe(false)
  })

  it('flushes a queued write by calling the API and clears it on success', async () => {
    markOwned.mockResolvedValue({})
    await queueMarkOwned(5, [42])

    await flushQueue()

    expect(markOwned).toHaveBeenCalledWith(5, [42])
    expect(await isMarkOwnedQueued(5, 42)).toBe(false)
  })

  it('keeps an entry queued when it still fails with a network error', async () => {
    markOwned.mockRejectedValue({ message: 'Network Error' })
    await queueMarkOwned(5, [42])

    await flushQueue()

    expect(await isMarkOwnedQueued(5, 42)).toBe(true)
  })

  it('drops an entry that fails with a real API error instead of retrying forever', async () => {
    markOwned.mockRejectedValue({ response: { status: 404 } })
    await queueMarkOwned(5, [42])

    await flushQueue()

    expect(await isMarkOwnedQueued(5, 42)).toBe(false)
  })

  it('dispatches the flushed event only when something was actually synced', async () => {
    const handler = vi.fn()
    window.addEventListener(QUEUE_FLUSHED_EVENT, handler)

    try {
      markOwned.mockResolvedValue({})
      await queueMarkOwned(5, [42])
      await flushQueue()
      expect(handler).toHaveBeenCalledTimes(1)

      await flushQueue() // nothing left to sync this time
      expect(handler).toHaveBeenCalledTimes(1)
    } finally {
      window.removeEventListener(QUEUE_FLUSHED_EVENT, handler)
    }
  })

  it('clearPrivateOfflineData empties the queue (e.g. on logout)', async () => {
    await queueMarkOwned(5, [42])

    await clearPrivateOfflineData()

    expect(await isMarkOwnedQueued(5, 42)).toBe(false)
  })
})
