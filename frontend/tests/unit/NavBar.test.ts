import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import { beforeEach, describe, expect, it } from 'vitest'
import { i18n } from '../../src/i18n'
import NavBar from '../../src/components/NavBar.vue'
import { useAuthStore } from '../../src/stores/auth'

function mountNavBar() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: ['/', '/login', '/register', '/recipes', '/recipes/random', '/planning', '/shopping-lists', '/account'].map(
      (path) => ({ path, component: { template: '<div />' } }),
    ),
  })
  return mount(NavBar, { global: { plugins: [i18n, router] } })
}

describe('NavBar mobile auth buttons', () => {
  beforeEach(() => {
    localStorage.clear()
    setActivePinia(createPinia())
  })

  it('renders login and register links in the header actions when logged out', () => {
    const wrapper = mountNavBar()
    const block = wrapper.find('[data-testid="mobile-auth"]')
    expect(block.exists()).toBe(true)
    expect(block.findAll('a').map((a) => a.attributes('href'))).toEqual(['/login', '/register'])
  })

  it('hides them when authenticated', () => {
    localStorage.setItem('access_token', 'token')
    setActivePinia(createPinia())
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(true)
    const wrapper = mountNavBar()
    expect(wrapper.find('[data-testid="mobile-auth"]').exists()).toBe(false)
  })
})
