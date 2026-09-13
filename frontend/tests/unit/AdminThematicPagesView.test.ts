import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/adminThematicPages', () => ({
  listThematicPages: vi.fn(),
  createThematicPage: vi.fn(),
  updateThematicPage: vi.fn(),
  deleteThematicPage: vi.fn(),
}))

import {
  createThematicPage,
  deleteThematicPage,
  listThematicPages,
  updateThematicPage,
} from '../../src/api/adminThematicPages'
import AdminThematicPagesView from '../../src/views/AdminThematicPagesView.vue'
import type { AdminThematicPage } from '../../src/types/models'

async function mountView() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/admin/thematic-pages', component: AdminThematicPagesView }],
  })
  router.push('/admin/thematic-pages')
  await router.isReady()

  return mount(AdminThematicPagesView, {
    global: {
      plugins: [i18n, router],
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
      },
    },
  })
}

function page(overrides?: Partial<AdminThematicPage>): AdminThematicPage {
  return {
    id: 1,
    title: 'Produits de saison',
    slug: 'produits-de-saison',
    description: '',
    icon: '🌱',
    filters: { in_season: 'true' },
    order: 1,
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    ...overrides,
  }
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setActivePinia(createPinia())
  vi.clearAllMocks()
  window.confirm = vi.fn(() => true)
})

describe('AdminThematicPagesView', () => {
  it('lists thematic pages with a summary of their filters', async () => {
    vi.mocked(listThematicPages).mockResolvedValue([page()])

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('Produits de saison')
    expect(wrapper.text()).toContain('in_season=true')
  })

  it('shows an access-denied message for a non-staff visitor rejected by the API', async () => {
    vi.mocked(listThematicPages).mockRejectedValue({ response: { status: 403 } })

    const wrapper = await mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('Accès réservé aux administrateurs.')
  })

  it('toggles the active state of a page', async () => {
    vi.mocked(listThematicPages).mockResolvedValue([page()])
    vi.mocked(updateThematicPage).mockResolvedValue(page({ is_active: false }))

    const wrapper = await mountView()
    await flushPromises()

    const toggleButton = wrapper.findAll('button').find((b) => b.text() === 'Active')
    await toggleButton?.trigger('click')
    await flushPromises()

    expect(updateThematicPage).toHaveBeenCalledWith(1, { is_active: false })
  })

  it('deletes a page after confirmation', async () => {
    vi.mocked(listThematicPages).mockResolvedValue([page()])
    vi.mocked(deleteThematicPage).mockResolvedValue(undefined as never)

    const wrapper = await mountView()
    await flushPromises()

    await wrapper.find('button.danger').trigger('click')
    await flushPromises()

    expect(window.confirm).toHaveBeenCalled()
    expect(deleteThematicPage).toHaveBeenCalledWith(1)
  })

  it('creates a new thematic page from the structured filter fields', async () => {
    vi.mocked(listThematicPages).mockResolvedValue([])
    vi.mocked(createThematicPage).mockResolvedValue(page())

    const wrapper = await mountView()
    await flushPromises()

    await wrapper.find('button').trigger('click') // "Nouvelle page thématique"
    await wrapper.find('#tp-title').setValue('Spécial végan')
    await wrapper.find('#tp-diet').setValue('vegan')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createThematicPage).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'Spécial végan',
        filters: { diet_type: 'vegan' },
      }),
    )
  })

  it('rejects invalid advanced JSON filters without submitting', async () => {
    vi.mocked(listThematicPages).mockResolvedValue([])

    const wrapper = await mountView()
    await flushPromises()

    await wrapper.find('button').trigger('click')
    await wrapper.find('#tp-title').setValue('Brouillon')
    await wrapper.find('#tp-advanced').setValue('{not valid json')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createThematicPage).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Le JSON des filtres avancés est invalide.')
  })
})
