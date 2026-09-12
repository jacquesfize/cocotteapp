import { setActivePinia, createPinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { useAuthStore } from '../../src/stores/auth'

vi.mock('../../src/api/auth', () => ({
  register: vi.fn(),
  obtainToken: vi.fn(),
  refreshTokenRequest: vi.fn(),
  fetchMe: vi.fn(),
  updateMe: vi.fn(),
}))

import { fetchMe, obtainToken, refreshTokenRequest } from '../../src/api/auth'

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
    obtainToken.mockResolvedValue({ access: 'access-123', refresh: 'refresh-456' })
    fetchMe.mockResolvedValue({ id: 1, username: 'alice' })

    const store = useAuthStore()
    await store.login('alice', 'password123')

    expect(store.isAuthenticated).toBe(true)
    expect(store.accessToken).toBe('access-123')
    expect(store.user.username).toBe('alice')
    expect(localStorage.getItem('access_token')).toBe('access-123')
  })

  it('clears state and storage on logout', async () => {
    obtainToken.mockResolvedValue({ access: 'access-123', refresh: 'refresh-456' })
    fetchMe.mockResolvedValue({ id: 1, username: 'alice' })

    const store = useAuthStore()
    await store.login('alice', 'password123')
    store.logout()

    expect(store.isAuthenticated).toBe(false)
    expect(store.user).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
  })

  it('refreshes the access token using the stored refresh token', async () => {
    obtainToken.mockResolvedValue({ access: 'access-123', refresh: 'refresh-456' })
    fetchMe.mockResolvedValue({ id: 1, username: 'alice' })
    refreshTokenRequest.mockResolvedValue({ access: 'access-789' })

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
})
