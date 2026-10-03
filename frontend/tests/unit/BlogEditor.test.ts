import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import BlogEditor from '../../src/components/blog/BlogEditor.vue'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/blog', () => ({
  uploadBlogImage: vi.fn().mockResolvedValue({ id: 1, image: '/media/blog/photo.jpg', created_at: '' }),
}))

// Stand-in for the real search picker: selecting a recipe is a single click.
const RecipePickerStub = defineComponent({
  emits: ['update:modelValue'],
  setup(_, { emit }) {
    return () =>
      h('button', { class: 'pick-recipe', type: 'button', onClick: () => emit('update:modelValue', { id: 7, title: 'Curry' }) })
  },
})

function mountEditor(modelValue = '<p>Bonjour</p>') {
  return mount(BlogEditor, {
    props: { modelValue },
    attachTo: document.body,
    global: { plugins: [i18n], stubs: { RecipePicker: RecipePickerStub } },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
})

describe('BlogEditor', () => {
  it('keeps an embedded recipe iframe from existing content', async () => {
    const wrapper = mountEditor('<p>Intro</p><iframe src="/embed/recipes/3" data-cocotte-recipe="3" title="Tarte"></iframe>')
    await flushPromises()

    const iframe = wrapper.find('iframe[data-cocotte-recipe="3"]')
    expect(iframe.exists()).toBe(true)
    expect(iframe.attributes('src')).toBe('/embed/recipes/3')
    wrapper.unmount()
  })

  it('inserts the picked recipe as an embed iframe', async () => {
    const wrapper = mountEditor()
    await flushPromises()

    await wrapper.find('[data-testid="blog-insert-recipe"]').trigger('click')
    await wrapper.find('.pick-recipe').trigger('click')
    await flushPromises()

    const emitted = wrapper.emitted('update:modelValue')!
    const html = emitted[emitted.length - 1][0] as string
    expect(html).toContain('data-cocotte-recipe="7"')
    expect(html).toContain('src="/embed/recipes/7"')
    expect(html).toContain('title="Curry"')
    expect(wrapper.find('.pick-recipe').exists()).toBe(false)
    wrapper.unmount()
  })

  it('opens the recipe picker with the keyboard shortcut', async () => {
    const wrapper = mountEditor()
    await flushPromises()

    const editable = wrapper.find('[contenteditable="true"]')
    await editable.trigger('keydown', { key: 'r', code: 'KeyR', keyCode: 82, ctrlKey: true, altKey: true })
    await flushPromises()

    expect(wrapper.find('.pick-recipe').exists()).toBe(true)
    wrapper.unmount()
  })
})
