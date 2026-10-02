import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/auth', () => ({
  changePassword: vi.fn(),
  exportMyData: vi.fn(),
  setHealthDataConsent: vi.fn(),
  deleteMe: vi.fn(),
}))
vi.mock('../../src/api/allergens', () => ({
  listAllergens: vi.fn().mockResolvedValue([
    { slug: 'gluten', name: 'Gluten' },
    { slug: 'lactose', name: 'Lactose' },
  ]),
}))
vi.mock('../../src/api/planning', () => ({
  listPlanningShares: vi.fn(),
  createOrUpdatePlanningShare: vi.fn(),
  deletePlanningShare: vi.fn(),
}))

import { deleteMe, setHealthDataConsent } from '../../src/api/auth'
import { createOrUpdatePlanningShare, deletePlanningShare, listPlanningShares } from '../../src/api/planning'
import { useAuthStore } from '../../src/stores/auth'
import AccountSettingsView from '../../src/views/AccountSettingsView.vue'
import type { PlanningShare, User } from '../../src/types/models'

async function mountAccountSettings() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/account', component: AccountSettingsView },
      { path: '/privacy', name: 'privacy', component: { template: '<div />' } },
    ],
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

describe('AccountSettingsView allergens', () => {
  it('pre-checks the profile allergens and keeps allergy/intolerance mutually exclusive', async () => {
    const authStore = useAuthStore()
    authStore.user = {
      id: 1,
      username: 'me',
      email: 'me@example.com',
      allergies: ['gluten'],
      intolerances: [],
    } as unknown as User
    vi.mocked(listPlanningShares).mockResolvedValue([])

    const wrapper = await mountAccountSettings()
    await flushPromises()

    const allergy = wrapper.find('[data-testid="allergies-gluten"]')
    const intolerance = wrapper.find('[data-testid="intolerances-gluten"]')
    expect((allergy.element as HTMLInputElement).checked).toBe(true)
    expect((intolerance.element as HTMLInputElement).checked).toBe(false)

    await intolerance.setValue(true)

    expect((wrapper.find('[data-testid="allergies-gluten"]').element as HTMLInputElement).checked).toBe(false)
    expect((wrapper.find('[data-testid="intolerances-gluten"]').element as HTMLInputElement).checked).toBe(true)
  })
})

describe('AccountSettingsView health data consent', () => {
  const baseUser = { id: 1, username: 'me', email: 'me@example.com', diet_type: 'vegan' }

  beforeEach(() => {
    vi.mocked(listPlanningShares).mockResolvedValue([])
  })

  it('shows the consent date and lets the user withdraw it', async () => {
    const authStore = useAuthStore()
    authStore.user = { ...baseUser, health_data_consent_at: '2026-01-02T10:00:00Z' } as unknown as User
    vi.mocked(setHealthDataConsent).mockResolvedValue({
      ...baseUser,
      diet_type: 'omnivore',
      allergies: [],
      intolerances: [],
      health_data_consent_at: null,
    } as unknown as User)

    const wrapper = await mountAccountSettings()
    await flushPromises()
    const card = wrapper.find('[data-testid="consent-card"]')
    expect(card.text()).toContain('Vous avez consenti le')

    await card.find('button').trigger('click')
    await flushPromises()

    expect(setHealthDataConsent).toHaveBeenCalledWith(false)
    expect(authStore.user?.health_data_consent_at).toBeNull()
    expect(wrapper.find('[data-testid="consent-card"]').text()).toContain("Vous n'avez pas consenti")
  })

  it('does not withdraw consent when the confirmation is declined', async () => {
    const authStore = useAuthStore()
    authStore.user = { ...baseUser, health_data_consent_at: '2026-01-02T10:00:00Z' } as unknown as User
    window.confirm = vi.fn(() => false)

    const wrapper = await mountAccountSettings()
    await flushPromises()
    await wrapper.find('[data-testid="consent-card"] button').trigger('click')

    expect(setHealthDataConsent).not.toHaveBeenCalled()
  })

  it('lets a user without consent give it', async () => {
    const authStore = useAuthStore()
    authStore.user = { ...baseUser, health_data_consent_at: null } as unknown as User
    vi.mocked(setHealthDataConsent).mockResolvedValue({
      ...baseUser,
      allergies: [],
      intolerances: [],
      health_data_consent_at: '2026-02-01T00:00:00Z',
    } as unknown as User)

    const wrapper = await mountAccountSettings()
    await flushPromises()
    await wrapper.find('[data-testid="consent-card"] button').trigger('click')
    await flushPromises()

    expect(setHealthDataConsent).toHaveBeenCalledWith(true)
  })
})

describe('AccountSettingsView account deletion', () => {
  it.each([
    [false, false],
    [true, true],
  ])('asks the API to keep recipes: %s', async (checked, expected) => {
    const authStore = useAuthStore()
    authStore.user = { id: 1, username: 'me', email: 'me@example.com' } as unknown as User
    vi.mocked(listPlanningShares).mockResolvedValue([])
    vi.mocked(deleteMe).mockResolvedValue(undefined as never)

    const wrapper = await mountAccountSettings()
    await flushPromises()
    if (checked) await wrapper.find('[data-testid="keep-recipes"]').setValue(true)
    await wrapper.find('button.danger').trigger('click')
    await flushPromises()

    expect(deleteMe).toHaveBeenCalledWith(expected)
  })
})
