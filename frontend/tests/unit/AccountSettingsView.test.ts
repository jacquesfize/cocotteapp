import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/auth', () => ({
  changePassword: vi.fn(),
  exportMyData: vi.fn(),
}))
vi.mock('../../src/api/planning', () => ({
  listPlanningShares: vi.fn(),
  createOrUpdatePlanningShare: vi.fn(),
  deletePlanningShare: vi.fn(),
}))

import { createOrUpdatePlanningShare, deletePlanningShare, listPlanningShares } from '../../src/api/planning'
import { useAuthStore } from '../../src/stores/auth'
import AccountSettingsView from '../../src/views/AccountSettingsView.vue'
import type { PlanningShare, User } from '../../src/types/models'

async function mountAccountSettings() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/account', component: AccountSettingsView }],
  })
  router.push('/account')
  await router.isReady()

  return mount(AccountSettingsView, {
    global: {
      plugins: [i18n, router],
    },
  })
}

function share(overrides?: Partial<PlanningShare>): PlanningShare {
  return {
    id: 1,
    shared_with_username: 'bob',
    shared_with_email: 'bob@example.com',
    permission: 'read',
    created_at: '2026-01-01T00:00:00Z',
    ...overrides,
  }
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
  window.confirm = vi.fn(() => true)
})

describe('AccountSettingsView planning sharing', () => {
  it('lists existing shares', async () => {
    const authStore = useAuthStore()
    authStore.user = { id: 1, username: 'me', email: 'me@example.com' } as unknown as User
    vi.mocked(listPlanningShares).mockResolvedValue([share()])

    const wrapper = await mountAccountSettings()
    await flushPromises()

    expect(wrapper.text()).toContain('bob')
    expect(wrapper.text()).toContain('bob@example.com')
  })

  it('shows an empty message when nothing is shared', async () => {
    const authStore = useAuthStore()
    authStore.user = { id: 1, username: 'me', email: 'me@example.com' } as unknown as User
    vi.mocked(listPlanningShares).mockResolvedValue([])

    const wrapper = await mountAccountSettings()
    await flushPromises()

    expect(wrapper.text()).toContain("Vous n'avez partagé votre agenda avec personne.")
  })

  it('creates a share from the form', async () => {
    const authStore = useAuthStore()
    authStore.user = { id: 1, username: 'me', email: 'me@example.com' } as unknown as User
    vi.mocked(listPlanningShares).mockResolvedValue([])
    vi.mocked(createOrUpdatePlanningShare).mockResolvedValue(share())

    const wrapper = await mountAccountSettings()
    await flushPromises()

    await wrapper.find('#share-email').setValue('bob@example.com')
    await wrapper.find('#share-permission').setValue('write')
    await wrapper.find('#share-email').trigger('change')
    const form = wrapper.findAll('form').find((f) => f.find('#share-email').exists())
    await form?.trigger('submit.prevent')
    await flushPromises()

    expect(createOrUpdatePlanningShare).toHaveBeenCalledWith({ email: 'bob@example.com', permission: 'write' })
  })

  it('revokes a share after confirmation', async () => {
    const authStore = useAuthStore()
    authStore.user = { id: 1, username: 'me', email: 'me@example.com' } as unknown as User
    vi.mocked(listPlanningShares).mockResolvedValue([share()])
    vi.mocked(deletePlanningShare).mockResolvedValue(undefined as never)

    const wrapper = await mountAccountSettings()
    await flushPromises()

    const revokeButton = wrapper.findAll('button').find((b) => b.text() === 'Révoquer')
    await revokeButton?.trigger('click')
    await flushPromises()

    expect(window.confirm).toHaveBeenCalled()
    expect(deletePlanningShare).toHaveBeenCalledWith(1)
  })
})
