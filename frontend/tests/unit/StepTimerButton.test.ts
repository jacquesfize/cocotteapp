import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import StepTimerButton from '../../src/components/StepTimerButton.vue'
import { i18n } from '../../src/i18n'

function mountTimer(seconds: number, label?: string) {
  return mount(StepTimerButton, {
    props: { seconds, label },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('StepTimerButton', () => {
  it('shows a start button with the formatted duration', () => {
    const wrapper = mountTimer(600)
    expect(wrapper.find('button').text()).toContain('10 min')
    expect(wrapper.find('[role="timer"]').exists()).toBe(false)
  })

  it('includes the timer label next to the duration when provided', () => {
    const wrapper = mountTimer(600, 'repos')
    expect(wrapper.find('button').text()).toContain('repos')
  })

  it('shows a sub-minute duration in seconds rather than rounding up to a minute', () => {
    const wrapper = mountTimer(30)
    expect(wrapper.find('button').text()).toContain('30 s')
    expect(wrapper.find('button').text()).not.toContain('1 min')
  })

  it('shows a non-exact-minute duration as minutes and seconds', () => {
    const wrapper = mountTimer(90)
    expect(wrapper.find('button').text()).toContain('1 min 30 s')
  })

  it('counts down once started, and can be paused/resumed', async () => {
    const wrapper = mountTimer(5)
    await wrapper.find('button').trigger('click')

    expect(wrapper.find('[role="timer"]').text()).toContain('0:05')

    await vi.advanceTimersByTimeAsync(2000)
    expect(wrapper.find('[role="timer"]').text()).toContain('0:03')

    await wrapper.get('[aria-label="Mettre en pause"]').trigger('click')
    await vi.advanceTimersByTimeAsync(2000)
    expect(wrapper.find('[role="timer"]').text()).toContain('0:03')

    await wrapper.get('[aria-label="Reprendre"]').trigger('click')
    await vi.advanceTimersByTimeAsync(1000)
    expect(wrapper.find('[role="timer"]').text()).toContain('0:02')
  })

  it('keeps the name label visible once the timer is running', async () => {
    const wrapper = mountTimer(600, 'repos')
    await wrapper.find('button').trigger('click')

    expect(wrapper.find('[role="timer"]').text()).toContain('repos')
  })

  it('shows an hour-long countdown as H:MM:SS instead of overflowing minutes', async () => {
    const wrapper = mountTimer(3600)
    await wrapper.find('button').trigger('click')

    expect(wrapper.find('[role="timer"]').text()).toContain('1:00:00')

    await vi.advanceTimersByTimeAsync(5000)
    expect(wrapper.find('[role="timer"]').text()).toContain('59:55')
  })

  it('shows a finished state once the countdown reaches zero', async () => {
    const wrapper = mountTimer(2)
    await wrapper.find('button').trigger('click')

    await vi.advanceTimersByTimeAsync(2000)

    expect(wrapper.find('.finished').text()).toContain('Terminé !')
  })

  it('resets back to the idle button', async () => {
    const wrapper = mountTimer(120)
    await wrapper.find('button').trigger('click')
    await vi.advanceTimersByTimeAsync(120000)

    await wrapper.get('[aria-label="Réinitialiser"]').trigger('click')

    expect(wrapper.find('[role="timer"]').exists()).toBe(false)
    expect(wrapper.find('button').text()).toContain('2 min')
  })
})
