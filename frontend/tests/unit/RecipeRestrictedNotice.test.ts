import { mount } from '@vue/test-utils'
import { createPinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import RecipeRestrictedNotice from '../../src/components/RecipeRestrictedNotice.vue'
import { i18n } from '../../src/i18n'
import type { Recipe } from '../../src/types/models'

function mountNotice(recipe: Partial<Recipe>) {
  return mount(RecipeRestrictedNotice, {
    props: { recipe: recipe as Recipe },
    global: {
      plugins: [i18n, createPinia()],
    },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
})

describe('RecipeRestrictedNotice', () => {
  it('embeds the YouTube player instead of the image when a video is available', () => {
    const wrapper = mountNotice({
      source_url: 'https://youtu.be/abc123',
      video_url: 'https://youtu.be/abc123',
      youtube_id: 'abc123',
      image_url: 'https://example.com/photo.jpg',
    })

    const iframe = wrapper.find('iframe')
    expect(iframe.exists()).toBe(true)
    expect(iframe.attributes('src')).toBe('https://www.youtube-nocookie.com/embed/abc123')
    expect(wrapper.find('.hero-photo').exists()).toBe(false)
  })

  it('shows a blurred hero image with a centered source button when there is no video', () => {
    const wrapper = mountNotice({
      source_url: 'https://cuisine.example/recette',
      image_url: 'https://example.com/photo.jpg',
      youtube_id: null,
    })

    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.find('.hero-photo').exists()).toBe(true)
    const button = wrapper.find('.hero-source-button')
    expect(button.exists()).toBe(true)
    expect(button.attributes('href')).toBe('https://cuisine.example/recette')
  })

  it('falls back to a plain source link when there is neither image nor video', () => {
    const wrapper = mountNotice({
      source_url: 'https://cuisine.example/recette',
      youtube_id: null,
    })

    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.find('.hero-photo-wrapper').exists()).toBe(false)
    const link = wrapper.find('.fallback-source-link')
    expect(link.exists()).toBe(true)
    expect(link.attributes('href')).toBe('https://cuisine.example/recette')
  })

  it('always shows allergens and the carbon footprint', () => {
    const wrapper = mountNotice({
      allergens: ['gluten'],
      carbon_footprint_kg_co2e: 1.2345,
    })

    expect(wrapper.text()).toContain('1.23')
  })
})
