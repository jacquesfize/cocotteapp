import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it } from 'vitest'
import { i18n } from '../../src/i18n'
import NavBar from '../../src/components/shared/NavBar.vue'
import { useAuthStore } from '../../src/stores/auth'

function mountNavBar() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: ['/', '/login', '/register', '/recipes', '/recipes/random', '/blog', '/planning', '/shopping-lists', '/account'].map(
      (path) => ({ path, component: { template: '<div />' } }),
    ),
  })
  return mount(NavBar, { global: { plugins: [i18n, router] } })
}

describe('NavBar header actions', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('renders a single login icon link instead of the account menu when logged out', () => {
    const wrapper = mountNavBar()
    const login = wrapper.find('[data-testid="login-button"]')
    expect(login.attributes('href')).toBe('/login')
    expect(login.attributes('aria-label')).toBe('Connexion')
    expect(wrapper.find('#account-panel').exists()).toBe(false)
  })

  it('shows the account menu instead of the login link when authenticated', () => {
    localStorage.setItem('access_token', 'token')
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    const wrapper = mountNavBar()
    expect(wrapper.find('[data-testid="login-button"]').exists()).toBe(false)
    expect(wrapper.find('#account-panel').exists()).toBe(true)
  })

  it('switches language from the locale button, whether logged in or not', async () => {
    const wrapper = mountNavBar()
    const button = wrapper.find('[data-testid="locale-button"]')
    expect(button.attributes('aria-label')).toBe('Langue : Français')
    await button.trigger('click')
    const english = wrapper.findAll('.locale-option').find((o) => o.text().includes('English'))!
    await english.trigger('click')
    expect(i18n.global.locale.value).toBe('en')
    expect(button.attributes('aria-label')).toBe('Language: English')
    i18n.global.locale.value = 'fr'
  })
})
