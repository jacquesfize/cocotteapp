import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'
import { useAuthStore } from '../../src/stores/auth'
import AuthView from '../../src/views/auth/AuthView.vue'

const push = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
  useRoute: () => ({ query: {} }),
}))

beforeEach(() => {
  setActivePinia(createPinia())
  i18n.global.locale.value = 'en'
  push.mockReset()
})

function mountRegister() {
  return mount(AuthView, {
    props: { mode: 'register' },
    global: {
      plugins: [i18n],
      stubs: { RouterLink: { template: '<a><slot /></a>' }, Transition: false },
    },
  })
}

async function fillAccount(wrapper: ReturnType<typeof mountRegister>) {
  await wrapper.get('#username').setValue('alice')
  await wrapper.get('#email').setValue('alice@example.com')
  await wrapper.get('#password').setValue('s3cret-pass')
}

describe('AuthView (register)', () => {
  it('creates the account without health data when consent is not given', async () => {
    const wrapper = mountRegister()
    const register = vi.spyOn(useAuthStore(), 'register').mockResolvedValue()

    expect(wrapper.get('#health_data_consent').attributes('required')).toBeUndefined()
    expect(wrapper.find('#diet_type').exists()).toBe(false)
    expect(wrapper.find('#activity_level').exists()).toBe(false)

    await fillAccount(wrapper)
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(register).toHaveBeenCalledWith({
      username: 'alice',
      email: 'alice@example.com',
      password: 's3cret-pass',
      health_data_consent: false,
    })
    expect(push).toHaveBeenCalled()
  })

  it('shows and sends diet and activity level once consent is given', async () => {
    const wrapper = mountRegister()
    const register = vi.spyOn(useAuthStore(), 'register').mockResolvedValue()

    await fillAccount(wrapper)
    await wrapper.get('#health_data_consent').setValue(true)
    await wrapper.get('#diet_type').setValue('vegan')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(register).toHaveBeenCalledWith(
      expect.objectContaining({ health_data_consent: true, diet_type: 'vegan', activity_level: 'moderate' }),
    )
  })
})
