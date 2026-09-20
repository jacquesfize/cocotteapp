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
})
