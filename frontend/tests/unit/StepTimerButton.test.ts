import { mount } from '@vue/test-utils'
import { defineComponent, h } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import StepTimerButton from '../../src/components/StepTimerButton.vue'
import { useStepTimer } from '../../src/composables/useStepTimer'
import { i18n } from '../../src/i18n'

function mountTimer(seconds: number, label?: string) {
  return mount(StepTimerButton, {
    props: { seconds, label },
    global: { plugins: [i18n] },
  })
}

// Deux pastilles pilotant le même minuteur partagé (cas du mode cuisine, où la pastille inline
// et le dock affichent/contrôlent la même instance) : construite via un composant hôte, puisque
// useStepTimer() a besoin d'un contexte de composant actif (useI18n/onBeforeUnmount).
function mountSharedTimer(seconds: number, label?: string) {
  const Host = defineComponent({
    setup() {
      const handle = useStepTimer(seconds, label)
      return () =>
        h('div', [h(StepTimerButton, { handle, label, ref: 'a' }), h(StepTimerButton, { handle, label, ref: 'b' })])
    },
  })
  return mount(Host, { global: { plugins: [i18n] } })
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

  it('shares state between two instances given the same handle', async () => {
    const wrapper = mountSharedTimer(120, 'repos')
    const [chipA, chipB] = wrapper.findAllComponents(StepTimerButton)

    await chipA.find('button').trigger('click')

    expect(chipA.find('[role="timer"]').exists()).toBe(true)
    expect(chipB.find('[role="timer"]').exists()).toBe(true)

    await vi.advanceTimersByTimeAsync(3000)
    expect(chipA.find('[role="timer"]').text()).toContain('1:57')
    expect(chipB.find('[role="timer"]').text()).toContain('1:57')

    await chipB.get('[aria-label="Mettre en pause"]').trigger('click')
    expect(chipA.find('[aria-label="Reprendre"]').exists()).toBe(true)
  })
})

describe('StepTimerButton browser notifications', () => {
  let requestPermission: ReturnType<typeof vi.fn>
  let showNotification: ReturnType<typeof vi.fn>
  let notificationCtor: ReturnType<typeof vi.fn>

  beforeEach(() => {
    requestPermission = vi.fn().mockResolvedValue('granted')
    showNotification = vi.fn().mockResolvedValue(undefined)
    notificationCtor = vi.fn()

    class FakeNotification {
      static permission: NotificationPermission = 'default'
      static requestPermission = requestPermission
      constructor(...args: unknown[]) {
        notificationCtor(...args)
      }
    }
    vi.stubGlobal('Notification', FakeNotification)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    // @ts-expect-error nettoyage du stub de test, la propriété n'existe pas nativement en jsdom
    delete navigator.serviceWorker
  })

  async function finishTimer(wrapper: ReturnType<typeof mountTimer>, seconds: number) {
    await wrapper.find('button').trigger('click')
    await vi.advanceTimersByTimeAsync(seconds * 1000)
    await vi.advanceTimersByTimeAsync(0)
    await Promise.resolve()
    await Promise.resolve()
  }

  it('requests permission on start when not yet decided', async () => {
    const wrapper = mountTimer(5)
    await wrapper.find('button').trigger('click')

    expect(requestPermission).toHaveBeenCalled()
  })

  it('does not re-request permission once already granted or denied', async () => {
    ;(globalThis.Notification as unknown as { permission: NotificationPermission }).permission = 'granted'
    const wrapper = mountTimer(5)
    await wrapper.find('button').trigger('click')

    expect(requestPermission).not.toHaveBeenCalled()
  })

  it('shows a notification through the PWA service worker when one is available', async () => {
    ;(globalThis.Notification as unknown as { permission: NotificationPermission }).permission = 'granted'
    Object.defineProperty(navigator, 'serviceWorker', {
      value: { ready: Promise.resolve({ showNotification }) },
      configurable: true,
    })

    const wrapper = mountTimer(2, 'repos')
    await finishTimer(wrapper, 2)

    expect(showNotification).toHaveBeenCalledWith(
      'Minuteur terminé !',
      expect.objectContaining({ body: expect.stringContaining('repos') }),
    )
    expect(notificationCtor).not.toHaveBeenCalled()
  })

  it('falls back to the Notification constructor when there is no service worker', async () => {
    ;(globalThis.Notification as unknown as { permission: NotificationPermission }).permission = 'granted'

    const wrapper = mountTimer(2)
    await finishTimer(wrapper, 2)

    expect(notificationCtor).toHaveBeenCalled()
  })

  it('does not notify when permission is denied', async () => {
    ;(globalThis.Notification as unknown as { permission: NotificationPermission }).permission = 'denied'

    const wrapper = mountTimer(2)
    await finishTimer(wrapper, 2)

    expect(showNotification).not.toHaveBeenCalled()
    expect(notificationCtor).not.toHaveBeenCalled()
  })
})
