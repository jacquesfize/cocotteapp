import { setActivePinia, createPinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuthStore } from '../../src/stores/auth'

vi.mock('../../src/api/auth', () => ({
  register: vi.fn(),
  obtainToken: vi.fn(),
  refreshTokenRequest: vi.fn(),
  fetchMe: vi.fn(),
  updateMe: vi.fn(),
  deleteMe: vi.fn(),
  changePassword: vi.fn(),
  exportMyData: vi.fn(),
}))

import { deleteMe, fetchMe, obtainToken, refreshTokenRequest } from '../../src/api/auth'
import type { User } from '../../src/types/models'

beforeEach(() => {
  setActivePinia(createPinia())
  localStorage.clear()
  vi.clearAllMocks()
})

describe('auth store', () => {
  it('is not authenticated by default', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
  })

  it('stores tokens and fetches the user on login', async () => {
    vi.mocked(obtainToken).mockResolvedValue({ access: 'access-123', refresh: 'refresh-456' })
    vi.mocked(fetchMe).mockResolvedValue({ id: 1, username: 'alice' } as User)

    const store = useAuthStore()
    await store.login('alice', 'password123')

    expect(store.isAuthenticated).toBe(true)
    expect(store.accessToken).toBe('access-123')
    expect(store.user?.username).toBe('alice')
    expect(localStorage.getItem('access_token')).toBe('access-123')
  })

  it('clears state and storage on logout', async () => {
    vi.mocked(obtainToken).mockResolvedValue({ access: 'access-123', refresh: 'refresh-456' })
    vi.mocked(fetchMe).mockResolvedValue({ id: 1, username: 'alice' } as User)

    const store = useAuthStore()
    await store.login('alice', 'password123')
    store.logout()

    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('refreshes the access token using the stored refresh token', async () => {
    vi.mocked(obtainToken).mockResolvedValue({ access: 'access-123', refresh: 'refresh-456' })
    vi.mocked(fetchMe).mockResolvedValue({ id: 1, username: 'alice' } as User)
    vi.mocked(refreshTokenRequest).mockResolvedValue({ access: 'access-789', refresh: 'refresh-456' })

    const store = useAuthStore()
    await store.login('alice', 'password123')
    const refreshed = await store.refreshAccessToken()

    expect(refreshed).toBe(true)
    expect(store.accessToken).toBe('access-789')
  })

  it('returns false when there is no refresh token to use', async () => {
    const store = useAuthStore()
    const refreshed = await store.refreshAccessToken()
    expect(refreshed).toBe(false)
  })

  it('deletes the account then clears local state, like logout', async () => {
    vi.mocked(obtainToken).mockResolvedValue({ access: 'access-123', refresh: 'refresh-456' })
    vi.mocked(fetchMe).mockResolvedValue({ id: 1, username: 'alice' } as User)
    vi.mocked(deleteMe).mockResolvedValue(undefined as never)

    const store = useAuthStore()
    await store.login('alice', 'password123')
    await store.deleteAccount()

    expect(deleteMe).toHaveBeenCalledWith(false)
    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('can keep the public recipes when deleting the account', async () => {
    vi.mocked(deleteMe).mockResolvedValue(undefined as never)

    const store = useAuthStore()
    await store.deleteAccount(true)

    expect(deleteMe).toHaveBeenCalledWith(true)
  })
})
