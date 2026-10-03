import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { defineComponent, h } from 'vue'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/blog', () => ({
  createBlogPost: vi.fn(),
  updateBlogPost: vi.fn(),
  getBlogPost: vi.fn(),
  uploadBlogCover: vi.fn(),
  deleteBlogCover: vi.fn(),
}))

import { createBlogPost, deleteBlogCover, getBlogPost, updateBlogPost, uploadBlogCover } from '../../src/api/blog'
import BlogPostFormView from '../../src/views/blog/BlogPostFormView.vue'

// The real TipTap editor is covered by BlogEditor.test.ts; a textarea is enough here.
const BlogEditorStub = defineComponent({
  props: { modelValue: { type: String, default: '' } },
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    return () =>
      h('textarea', {
        class: 'editor-stub',
        value: props.modelValue,
        onInput: (e: Event) => emit('update:modelValue', (e.target as HTMLTextAreaElement).value),
      })
  },
})

async function mountForm(id?: number) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/blog/new', name: 'blog-new', component: { template: '<div />' } },
      { path: '/blog/:id', name: 'blog-detail', component: { template: '<div />' } },
    ],
  })
  router.push('/blog/new')
  await router.isReady()
  const wrapper = mount(BlogPostFormView, {
    props: id === undefined ? {} : { id },
    global: { plugins: [i18n, router], stubs: { BlogEditor: BlogEditorStub } },
  })
  await flushPromises()
  return { wrapper, router }
}

beforeEach(() => {
  i18n.global.locale.value = 'en'
  vi.clearAllMocks()
})

describe('BlogPostFormView', () => {
  it('shows the anti-discrimination and copyright rules', async () => {
    const { wrapper } = await mountForm()

    const text = wrapper.find('[data-testid="blog-guidelines"]').text()
    expect(text).toContain('discriminatory')
    expect(text).toContain('copyright')
  })

  it('refuses to publish until the rules are accepted', async () => {
    const { wrapper } = await mountForm()
    await wrapper.find('#blog-title').setValue('Mon menu')
    await wrapper.find('.editor-stub').setValue('<p>Bonjour</p>')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createBlogPost).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Please confirm that your post follows the publishing rules.')
  })

  it('creates the post and opens it', async () => {
    vi.mocked(createBlogPost).mockResolvedValue({ id: 12 } as never)
    const { wrapper, router } = await mountForm()
    await wrapper.find('#blog-title').setValue('Mon menu')
    await wrapper.find('.editor-stub').setValue('<p>Bonjour</p>')
    await wrapper.find('#blog-comments-enabled').setValue(false)
    await wrapper.find('#blog-accept-guidelines').setValue(true)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createBlogPost).toHaveBeenCalledWith({ title: 'Mon menu', content: '<p>Bonjour</p>', comments_enabled: false })
    expect(router.currentRoute.value.fullPath).toBe('/blog/12')
  })

  it('refuses an empty post', async () => {
    const { wrapper } = await mountForm()
    await wrapper.find('#blog-title').setValue('Vide')
    await wrapper.find('.editor-stub').setValue('<p></p>')
    await wrapper.find('#blog-accept-guidelines').setValue(true)

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createBlogPost).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Your post is empty.')
  })

  it('loads and updates an existing post', async () => {
    vi.mocked(getBlogPost).mockResolvedValue({
      id: 5,
      title: 'Ancien titre',
      content: '<p>Texte</p>',
      comments_enabled: true,
      cover_image: null,
    } as never)
    vi.mocked(updateBlogPost).mockResolvedValue({ id: 5 } as never)
    const { wrapper } = await mountForm(5)

    expect((wrapper.find('#blog-title').element as HTMLInputElement).value).toBe('Ancien titre')
    await wrapper.find('#blog-accept-guidelines').setValue(true)
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(updateBlogPost).toHaveBeenCalledWith(5, { title: 'Ancien titre', content: '<p>Texte</p>', comments_enabled: true })
  })

  it('uploads the chosen cover image once the post is created', async () => {
    vi.mocked(createBlogPost).mockResolvedValue({ id: 12 } as never)
    URL.createObjectURL = vi.fn(() => 'blob:cover')
    URL.revokeObjectURL = vi.fn()
    const { wrapper } = await mountForm()
    await wrapper.find('#blog-title').setValue('Avec image')
    await wrapper.find('.editor-stub').setValue('<p>Bonjour</p>')
    await wrapper.find('#blog-accept-guidelines').setValue(true)
    const file = new File(['x'], 'cover.jpg', { type: 'image/jpeg' })
    const input = wrapper.find('#blog-cover')
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')

    expect(wrapper.find('[data-testid="blog-cover-preview"]').attributes('src')).toBe('blob:cover')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(uploadBlogCover).toHaveBeenCalledWith(12, file)
  })

  it('deletes the existing cover image when it is removed', async () => {
    vi.mocked(getBlogPost).mockResolvedValue({
      id: 5,
      title: 'Titre',
      content: '<p>Texte</p>',
      comments_enabled: true,
      cover_image: '/media/blog/covers/a.jpg',
    } as never)
    vi.mocked(updateBlogPost).mockResolvedValue({ id: 5 } as never)
    const { wrapper } = await mountForm(5)

    await wrapper.find('[data-testid="blog-cover-remove"]').trigger('click')
    await wrapper.find('#blog-accept-guidelines').setValue(true)
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(deleteBlogCover).toHaveBeenCalledWith(5)
    expect(uploadBlogCover).not.toHaveBeenCalled()
  })
})
