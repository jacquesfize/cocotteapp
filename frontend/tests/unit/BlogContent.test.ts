import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import BlogContent from '../../src/components/blog/BlogContent.vue'
import { EMBED_HEIGHT_MESSAGE } from '../../src/utils/embedMessages'

describe('BlogContent', () => {
  it('resizes an embedded recipe iframe to the height it reports', async () => {
    const wrapper = mount(BlogContent, {
      props: { html: '<p>Texte</p><iframe src="/embed/recipes/1" data-cocotte-recipe="1"></iframe>' },
      attachTo: document.body,
    })
    const iframe = wrapper.find('iframe').element as HTMLIFrameElement

    window.dispatchEvent(
      new MessageEvent('message', {
        data: { type: EMBED_HEIGHT_MESSAGE, height: 187.4 },
        origin: window.location.origin,
        source: iframe.contentWindow,
      }),
    )

    expect(iframe.style.height).toBe('188px')
    wrapper.unmount()
  })

  it('ignores height messages from another origin', () => {
    const wrapper = mount(BlogContent, {
      props: { html: '<iframe src="/embed/recipes/1" data-cocotte-recipe="1"></iframe>' },
      attachTo: document.body,
    })
    const iframe = wrapper.find('iframe').element as HTMLIFrameElement

    window.dispatchEvent(
      new MessageEvent('message', {
        data: { type: EMBED_HEIGHT_MESSAGE, height: 900 },
        origin: 'https://evil.example',
        source: iframe.contentWindow,
      }),
    )

    expect(iframe.style.height).toBe('')
    wrapper.unmount()
  })
})
