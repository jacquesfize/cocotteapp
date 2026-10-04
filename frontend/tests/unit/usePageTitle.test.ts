import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it } from 'vitest'
import { defineComponent, h, nextTick, ref } from 'vue'
import { i18n } from '../../src/i18n'
import { formatDocumentTitle, setRouteTitle, usePageTitle } from '../../src/composables/usePageTitle'

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  setRouteTitle(undefined)
})

describe('usePageTitle', () => {
  it('formats the tab title with the app name', () => {
    expect(formatDocumentTitle('Recettes')).toBe('Recettes · Cocotte')
    expect(formatDocumentTitle('')).toBe('Cocotte')
  })

  it('uses the route meta title and follows locale changes', async () => {
    setRouteTitle('pageTitle.planning')
    expect(document.title).toBe('Agenda · Cocotte')

    i18n.global.locale.value = 'en'
    await nextTick()
    expect(document.title).toBe('Planner · Cocotte')
  })

  it('falls back to the app name alone without meta title', () => {
    setRouteTitle(undefined)
    expect(document.title).toBe('Cocotte')
  })

  it('lets a view override the title once its data is loaded, until it unmounts', async () => {
    setRouteTitle('pageTitle.recipeDetail')
    const title = ref<string | undefined>(undefined)
    const wrapper = mount(
      defineComponent({
        setup() {
          usePageTitle(() => title.value)
          return () => h('div')
        },
      }),
    )
    await flushPromises()
    expect(document.title).toBe('Recette · Cocotte')

    title.value = 'Curry de saison'
    await flushPromises()
    expect(document.title).toBe('Curry de saison · Cocotte')

    wrapper.unmount()
    await flushPromises()
    expect(document.title).toBe('Recette · Cocotte')
  })
})
