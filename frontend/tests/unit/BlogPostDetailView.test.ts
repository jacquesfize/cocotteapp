import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/blog', () => ({
  getBlogPost: vi.fn(),
  deleteBlogPost: vi.fn(),
  listBlogPostComments: vi.fn().mockResolvedValue({ count: 0, next: null, previous: null, results: [] }),
  createBlogPostComment: vi.fn(),
  hideBlogPostComment: vi.fn(),
}))

import { getBlogPost } from '../../src/api/blog'
import { useAuthStore } from '../../src/stores/auth'
import BlogPostDetailView from '../../src/views/blog/BlogPostDetailView.vue'
import type { BlogPost, User } from '../../src/types/models'

function post(overrides: Partial<BlogPost> = {}): BlogPost {
  return {
    id: 1,
    title: 'Mes courges',
    author: 'chef',
    author_id: 42,
    content: '<p>Une <strong>belle</strong> saison.</p>',
    cover_image: null,
    comments_enabled: true,
    created_at: '2026-10-01T10:00:00Z',
    updated_at: '2026-10-01T10:00:00Z',
    ...overrides,
  }
}

async function mountDetail() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/:p(.*)*', component: { template: '<div />' } }],
  })
  const wrapper = mount(BlogPostDetailView, { props: { id: 1 }, global: { plugins: [i18n, router] } })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  i18n.global.locale.value = 'en'
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('BlogPostDetailView', () => {
  it('renders the post HTML and its byline', async () => {
    vi.mocked(getBlogPost).mockResolvedValue(post())
    const wrapper = await mountDetail()

    expect(wrapper.find('.blog-prose strong').text()).toBe('belle')
    expect(wrapper.text()).toContain('By chef')
    expect(wrapper.text()).not.toContain('Edit')
  })

  it('shows the cover image at the top of the post', async () => {
    vi.mocked(getBlogPost).mockResolvedValue(post({ cover_image: '/media/blog/covers/c.jpg' }))
    const wrapper = await mountDetail()

    expect(wrapper.find('.blog-post-cover').attributes('src')).toBe('/media/blog/covers/c.jpg')
  })

  it('replaces the comment form with a note when comments are disabled', async () => {
    vi.mocked(getBlogPost).mockResolvedValue(post({ comments_enabled: false }))
    const wrapper = await mountDetail()

    expect(wrapper.find('#comment-body').exists()).toBe(false)
    expect(wrapper.text()).toContain('Comments are closed for this post.')
  })

  it('shows edit and delete to the author', async () => {
    useAuthStore().user = { id: 42, username: 'chef' } as unknown as User
    vi.mocked(getBlogPost).mockResolvedValue(post())
    const wrapper = await mountDetail()

    expect(wrapper.text()).toContain('Edit')
    expect(wrapper.text()).toContain('Delete')
  })
})
