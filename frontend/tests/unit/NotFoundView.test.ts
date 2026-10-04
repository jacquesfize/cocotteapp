import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { i18n } from '../../src/i18n'
import router from '../../src/router'
import NotFoundView from '../../src/views/NotFoundView.vue'

beforeEach(() => {
  i18n.global.locale.value = 'fr'
})

describe('NotFoundView', () => {
  it('shows a friendly message with links to home and recipes', () => {
    const wrapper = mount(NotFoundView, {
      global: {
        plugins: [i18n],
        stubs: { RouterLink: { props: ['to'], template: '<a :data-to="JSON.stringify(to)"><slot /></a>' } },
      },
    })

    expect(wrapper.text()).toContain('Page introuvable')
    const targets = wrapper.findAll('a').map((a) => a.attributes('data-to'))
    expect(targets).toEqual([JSON.stringify({ name: 'home' }), JSON.stringify({ name: 'recipes' })])
  })

  it('is reached by a public catch-all route instead of a redirect', () => {
    const resolved = router.resolve('/does/not/exist')
    expect(resolved.name).toBe('not-found')
    expect(resolved.meta.public).toBe(true)
    expect(resolved.meta.title).toBe('pageTitle.notFound')
  })
})
