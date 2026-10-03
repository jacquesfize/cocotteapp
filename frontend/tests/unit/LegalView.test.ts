import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/auth', () => ({ fetchLegalInfo: vi.fn() }))

import { fetchLegalInfo } from '../../src/api/auth'
import LegalView from '../../src/views/LegalView.vue'

const info = {
  policy_version: '2',
  publisher_name: 'Association Cocotte',
  publisher_address: '1 rue des Fourneaux',
  contact_email: 'contact@example.org',
  host_name: 'OVH',
  host_address: '',
  privacy_contact_email: 'privacy@example.org',
  inactive_retention_days: 730,
  planning_snack_enabled: false,
  nutrition_alerts_enabled: false,
}

function mountPage(page: 'legal' | 'privacy') {
  return mount(LegalView, { props: { page }, global: { plugins: [i18n] } })
}

beforeEach(() => {
  i18n.global.locale.value = 'en'
  vi.clearAllMocks()
  vi.mocked(fetchLegalInfo).mockResolvedValue(info)
})

describe('LegalView', () => {
  it('shows the publisher and host, with a placeholder for missing fields', async () => {
    const wrapper = mountPage('legal')
    await flushPromises()

    expect(wrapper.text()).toContain('Association Cocotte')
    expect(wrapper.text()).toContain('OVH')
    expect(wrapper.text()).toContain('Not provided by the instance administrator.')
  })

  it('shows the privacy contact, the retention period and the policy version', async () => {
    const wrapper = mountPage('privacy')
    await flushPromises()

    expect(wrapper.text()).toContain('privacy@example.org')
    expect(wrapper.text()).toContain('730 days')
    expect(wrapper.text()).toContain('Policy version 2')
    expect(wrapper.findAll('li').length).toBeGreaterThan(0)
  })

  it('omits the inactivity sentence when purging is disabled', async () => {
    vi.mocked(fetchLegalInfo).mockResolvedValue({ ...info, inactive_retention_days: 0 })

    const wrapper = mountPage('privacy')
    await flushPromises()

    expect(wrapper.text()).not.toContain('no login for')
  })

  it('shows an error when the info cannot be loaded', async () => {
    vi.mocked(fetchLegalInfo).mockRejectedValue(new Error('offline'))

    const wrapper = mountPage('legal')
    await flushPromises()

    expect(wrapper.text()).toContain('Could not load this page.')
  })
})
