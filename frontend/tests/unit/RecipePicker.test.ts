import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/recipes', () => ({
  listRecipes: vi.fn().mockResolvedValue({ results: [], count: 0, next: null, previous: null }),
}))

import { listRecipes } from '../../src/api/recipes'
import RecipePicker from '../../src/components/recipes/RecipePicker.vue'
import type { Recipe } from '../../src/types/models'

function recipe(overrides?: Partial<Recipe>): Recipe {
  return {
    id: 3,
    title: 'Tarte aux pommes',
    slug: 'tarte-aux-pommes',
    description: '',
    author: 'Jacques',
    author_id: 1,
    servings: 4,
    prep_time_minutes: 20,
    cook_time_minutes: 40,
    total_time_minutes: 60,
    diet_type: 'omnivore',
    source_type: 'manual',
    source_url: '',
    video_url: '',
    youtube_id: null,
    image: null,
    image_url: '',
    image_license: '',
    image_credit_author: '',
    image_credit_source_url: '',
    ...overrides,
  } as Recipe
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  vi.clearAllMocks()
})

describe('RecipePicker', () => {
  describe('suggestions list', () => {
    const tarte = recipe()

    async function typeAndLoad(wrapper: ReturnType<typeof mount>, text = 'Tarte') {
      vi.mocked(listRecipes).mockResolvedValue({ results: [tarte], count: 1, next: null, previous: null })
      await wrapper.find('input').setValue(text)
      await vi.advanceTimersByTimeAsync(300)
      await flushPromises()
    }

    beforeEach(() => {
      vi.useFakeTimers()
    })
    afterEach(() => {
      vi.useRealTimers()
    })

    it('closes after selection and stays closed past the debounce delay (regression: double-click bug)', async () => {
      const wrapper = mount(RecipePicker, { global: { plugins: [i18n] } })
      await typeAndLoad(wrapper)
      expect(wrapper.find('ul.suggestions-dropdown').exists()).toBe(true)

      await wrapper.find('li').trigger('mousedown')
      // The dropdown must close immediately on selection...
      expect(wrapper.find('ul.suggestions-dropdown').exists()).toBe(false)

      // ...and must NOT reopen once the debounce window that a programmatic `query` change
      // could have scheduled has elapsed (this is the bug: selecting used to set `query`,
      // which a `watch(query, ...)` picked up as if the user had typed, re-triggering a
      // search whose `onResults` reopened the dropdown ~250ms later).
      await vi.advanceTimersByTimeAsync(500)
      await flushPromises()

      expect(wrapper.find('ul.suggestions-dropdown').exists()).toBe(false)
      expect((wrapper.find('input').element as HTMLInputElement).value).toBe(tarte.title)
      expect(listRecipes).toHaveBeenCalledTimes(1)
      expect(wrapper.emitted('update:modelValue')?.[0]).toEqual([tarte])
    })

    it('does not reopen on refocus or blur without new typing', async () => {
      const wrapper = mount(RecipePicker, { global: { plugins: [i18n] } })
      await typeAndLoad(wrapper)
      await wrapper.find('li').trigger('mousedown')

      await wrapper.find('input').trigger('blur')
      await vi.advanceTimersByTimeAsync(300)
      await wrapper.find('input').trigger('focus')
      await flushPromises()

      expect(wrapper.find('ul.suggestions-dropdown').exists()).toBe(false)
    })
  })
})
