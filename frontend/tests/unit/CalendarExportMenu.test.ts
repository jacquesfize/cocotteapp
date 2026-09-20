import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/planning', () => ({
  downloadWeekIcs: vi.fn(),
  getCalendarFeed: vi.fn(),
  regenerateCalendarFeed: vi.fn(),
}))

import { getCalendarFeed, regenerateCalendarFeed } from '../../src/api/planning'
import CalendarExportMenu from '../../src/components/CalendarExportMenu.vue'

const feed = { token: 't1', url: 'https://x.test/api/planning/feed/t1.ics', webcal_url: 'webcal://x.test/api/planning/feed/t1.ics' }

function mountMenu() {
  return mount(CalendarExportMenu, {
    props: { params: { date_after: '2026-03-02', date_before: '2026-03-08' } },
    global: { plugins: [i18n] },
    attachTo: document.body,
  })
}

describe('CalendarExportMenu', () => {
  beforeEach(() => {
    vi.mocked(getCalendarFeed).mockReset().mockResolvedValue(feed)
    vi.mocked(regenerateCalendarFeed).mockReset().mockResolvedValue({ ...feed, token: 't2', url: feed.url.replace('t1', 't2'), webcal_url: feed.webcal_url.replace('t1', 't2') })
  })

  it('loads the feed on open and builds the Google link', async () => {
    const wrapper = mountMenu()
    expect(wrapper.find('.menu').exists()).toBe(false)
    await wrapper.find('button').trigger('click')
    await flushPromises()
    expect(getCalendarFeed).toHaveBeenCalledTimes(1)
    expect(wrapper.find('a.google').attributes('href')).toContain(encodeURIComponent(feed.webcal_url))
  })

  it('regenerates the URL after confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const wrapper = mountMenu()
    await wrapper.find('button').trigger('click')
    await flushPromises()
    const buttons = wrapper.findAll('.menu button')
    await buttons[buttons.length - 1].trigger('click')
    await flushPromises()
    expect(regenerateCalendarFeed).toHaveBeenCalled()
    expect(wrapper.find('a.google').attributes('href')).toContain('t2')
  })

  it('renders the Google button with an inline logo', async () => {
    const wrapper = mountMenu()
    await wrapper.find('button').trigger('click')
    await flushPromises()
    const link = wrapper.find('a.google')
    expect(link.find('svg.google-logo').exists()).toBe(true)
    expect(link.text()).toBe('Ajouter à Google Agenda')
    wrapper.unmount()
  })

  it('closes on outside click but not on inside click', async () => {
    const wrapper = mountMenu()
    await wrapper.find('button').trigger('click')
    await flushPromises()
    await wrapper.find('.menu').trigger('mousedown')
    expect(wrapper.find('.menu').exists()).toBe(true)
    document.body.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))
    await flushPromises()
    expect(wrapper.find('.menu').exists()).toBe(false)
    wrapper.unmount()
  })

  it('closes on Escape', async () => {
    const wrapper = mountMenu()
    await wrapper.find('button').trigger('click')
    await flushPromises()
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushPromises()
    expect(wrapper.find('.menu').exists()).toBe(false)
    wrapper.unmount()
  })
})
