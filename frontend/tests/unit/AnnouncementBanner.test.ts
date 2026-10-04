import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('../../src/api/announcements', () => ({ listAnnouncements: vi.fn() }))

import { listAnnouncements } from '../../src/api/announcements'
import AnnouncementBanner from '../../src/components/shared/AnnouncementBanner.vue'
import { i18n } from '../../src/i18n'

async function mountBanner(items: unknown[]) {
  vi.mocked(listAnnouncements).mockResolvedValue(items as never)
  const wrapper = mount(AnnouncementBanner, { global: { plugins: [i18n] } })
  await flushPromises()
  return wrapper
}

const update = {
  id: 1,
  level: 'info',
  dismissible: true,
  title_fr: 'Nouveauté',
  title_en: 'New',
  message_fr: 'Les tags arrivent.',
  message_en: '',
  updated_at: '2026-10-04T10:00:00Z',
}

beforeEach(() => {
  localStorage.clear()
  i18n.global.locale.value = 'fr'
})

describe('AnnouncementBanner', () => {
  it('renders nothing when there is no announcement', async () => {
    const wrapper = await mountBanner([])
    expect(wrapper.find('.announcement').exists()).toBe(false)
  })

  it('shows the text in the current language and falls back to the other one', async () => {
    const wrapper = await mountBanner([update])
    expect(wrapper.text()).toContain('Nouveauté')
    i18n.global.locale.value = 'en'
    await wrapper.vm.$nextTick()
    expect(wrapper.text()).toContain('New')
    expect(wrapper.text()).toContain('Les tags arrivent.')
  })

  it('uses the built-in translated text for the test instance, which cannot be dismissed', async () => {
    const wrapper = await mountBanner([{ id: 'test-instance', level: 'warning', dismissible: false }])
    expect(wrapper.text()).toContain('Instance de test')
    expect(wrapper.find('.announcement__close').exists()).toBe(false)
  })

  it('remembers a dismissal, but shows the announcement again once it is edited', async () => {
    const wrapper = await mountBanner([update])
    await wrapper.find('.announcement__close').trigger('click')
    expect(wrapper.find('.announcement').exists()).toBe(false)

    expect((await mountBanner([update])).find('.announcement').exists()).toBe(false)
    const edited = { ...update, updated_at: '2026-10-05T10:00:00Z' }
    expect((await mountBanner([edited])).find('.announcement').exists()).toBe(true)
  })

  it('announces critical messages as alerts', async () => {
    const wrapper = await mountBanner([{ ...update, level: 'critical' }])
    expect(wrapper.find('.announcement').attributes('role')).toBe('alert')
  })

  it('stays silent when the API fails', async () => {
    vi.mocked(listAnnouncements).mockRejectedValue(new Error('down'))
    const wrapper = mount(AnnouncementBanner, { global: { plugins: [i18n] } })
    await flushPromises()
    expect(wrapper.find('.announcement').exists()).toBe(false)
  })
})

describe('AnnouncementBanner links', () => {
  it('only renders site paths and http(s) links', async () => {
    const link = (url: string) => ({ ...update, link_url: url, link_label_fr: 'Voir' })
    expect((await mountBanner([link('/blog')])).find('a').attributes('href')).toBe('/blog')
    expect((await mountBanner([link('https://example.org')])).find('a').exists()).toBe(true)
    for (const bad of ['javascript:alert(1)', '//evil.example', 'data:text/html,x']) {
      expect((await mountBanner([link(bad)])).find('a').exists()).toBe(false)
    }
  })
})
