import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/admin', () => ({
  listUsers: vi.fn(),
  updateUser: vi.fn(),
  deleteUser: vi.fn(),
}))

import { deleteUser, listUsers, updateUser } from '../../src/api/admin'
import { useAuthStore } from '../../src/stores/auth'
import AdminUsersView from '../../src/views/admin/AdminUsersView.vue'
import type { AdminUser, User } from '../../src/types/models'

async function mountAdminUsers() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/admin/users', component: AdminUsersView }],
  })
  router.push('/admin/users')
  await router.isReady()

  return mount(AdminUsersView, {
    global: {
      plugins: [i18n, router],
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

function user(overrides?: Partial<AdminUser>): AdminUser {
  return {
    id: 1,
    username: 'alice',
    email: 'alice@example.com',
    is_active: true,
    is_staff: false,
    date_joined: '2024-01-01',
    recipe_count: 3,
    ...overrides,
  }
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
  window.confirm = vi.fn(() => true)
})

describe('AdminUsersView', () => {
  it('lists users and lets a staff admin toggle another account', async () => {
    const authStore = useAuthStore()
    authStore.user = { ...user({ id: 99, username: 'admin', is_staff: true }) } as unknown as User

    vi.mocked(listUsers).mockResolvedValue({ results: [user()], count: 1, next: null, previous: null })
    vi.mocked(updateUser).mockResolvedValue(user({ is_active: false }))

    const wrapper = await mountAdminUsers()
    await flushPromises()

    expect(wrapper.text()).toContain('alice')
    expect(wrapper.text()).toContain('alice@example.com')

    const toggleButton = wrapper.findAll('button').find((b) => b.text() === 'Actif')
    await toggleButton?.trigger('click')
    await flushPromises()

    expect(updateUser).toHaveBeenCalledWith(1, { is_active: false })
  })

  it("hides action buttons on the admin's own row", async () => {
    const authStore = useAuthStore()
    authStore.user = { ...user({ id: 99, username: 'admin', is_staff: true }) } as unknown as User

    vi.mocked(listUsers).mockResolvedValue({
      results: [user({ id: 99, username: 'admin' })],
      count: 1,
      next: null,
      previous: null,
    })

    const wrapper = await mountAdminUsers()
    await flushPromises()

    expect(wrapper.text()).toContain("C'est vous")
    expect(wrapper.find('button.danger').exists()).toBe(false)
  })

  it('deletes a user after confirmation', async () => {
    const authStore = useAuthStore()
    authStore.user = { ...user({ id: 99, username: 'admin', is_staff: true }) } as unknown as User

    vi.mocked(listUsers).mockResolvedValue({ results: [user()], count: 1, next: null, previous: null })
    vi.mocked(deleteUser).mockResolvedValue(undefined as never)

    const wrapper = await mountAdminUsers()
    await flushPromises()

    await wrapper.find('button.danger').trigger('click')
    await flushPromises()

    expect(window.confirm).toHaveBeenCalled()
    expect(deleteUser).toHaveBeenCalledWith(1)
  })

  it('shows an access-denied message for a non-staff visitor rejected by the API', async () => {
    const authStore = useAuthStore()
    authStore.user = { ...user({ id: 1, is_staff: false }) } as unknown as User

    vi.mocked(listUsers).mockRejectedValue({ response: { status: 403 } })

    const wrapper = await mountAdminUsers()
    await flushPromises()

    expect(wrapper.text()).toContain('Accès réservé aux administrateurs.')
  })
})
