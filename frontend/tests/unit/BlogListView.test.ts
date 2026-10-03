import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/blog', () => ({
  listBlogPosts: vi.fn(),
  listBlogAuthors: vi.fn(),
  deleteBlogPost: vi.fn(),
}))

import { deleteBlogPost, listBlogAuthors, listBlogPosts } from '../../src/api/blog'
import { useAuthStore } from '../../src/stores/auth'
import BlogListView from '../../src/views/blog/BlogListView.vue'
import type { BlogPostSummary, User } from '../../src/types/models'

function post(id: number, authorId: number): BlogPostSummary {
  return {
    id,
    title: `Article ${id}`,
    author: `user${authorId}`,
    author_id: authorId,
    excerpt: 'Un extrait',
    cover_image: null,
    comments_enabled: true,
    created_at: '2026-10-01T10:00:00Z',
    updated_at: '2026-10-01T10:00:00Z',
  }
}

async function mountList(path = '/blog') {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/blog', name: 'blog', component: BlogListView },
      { path: '/blog/new', name: 'blog-new', component: { template: '<div />' } },
      { path: '/blog/:id', name: 'blog-detail', component: { template: '<div />' } },
      { path: '/blog/:id/edit', name: 'blog-edit', component: { template: '<div />' } },
    ],
  })
  router.push(path)
  await router.isReady()
  const wrapper = mount(BlogListView, { global: { plugins: [i18n, router] } })
  await flushPromises()
  return { wrapper, router }
}

beforeEach(() => {
  i18n.global.locale.value = 'en'
  setActivePinia(createPinia())
  vi.clearAllMocks()
  vi.mocked(listBlogAuthors).mockResolvedValue([
    { id: 1, username: 'user1' },
    { id: 2, username: 'user2' },
  ])
  vi.mocked(listBlogPosts).mockResolvedValue({ count: 2, next: null, previous: null, results: [post(1, 1), post(2, 2)] })
})

describe('BlogListView', () => {
  it('loads filters from the URL and shows them as removable chips', async () => {
    const { wrapper } = await mountList('/blog?search=courge&author=2')

    expect(listBlogPosts).toHaveBeenCalledWith({ search: 'courge', author: 2 })
    const chips = wrapper.findAll('.active-filters--desktop .filter-chip').map((chip) => chip.text())
    expect(chips).toEqual(['courge', 'By user2'])
  })

  it('searches as you type and keeps the search in the URL', async () => {
    vi.useFakeTimers()
    const { wrapper, router } = await mountList()

    await wrapper.find('#blog-search').setValue('soupe')
    await vi.advanceTimersByTimeAsync(350)
    await flushPromises()

    expect(listBlogPosts).toHaveBeenLastCalledWith({ search: 'soupe' })
    expect(router.currentRoute.value.query).toEqual({ search: 'soupe' })
    vi.useRealTimers()
  })

  it('shows edit and delete only on the current user’s posts', async () => {
    useAuthStore().user = { id: 1, username: 'user1', is_staff: false } as unknown as User
    const { wrapper } = await mountList()

    const cards = wrapper.findAll('.blog-card')
    expect(cards[0].find('.blog-card-actions').exists()).toBe(true)
    expect(cards[1].find('.blog-card-actions').exists()).toBe(false)
  })

  it('lets staff delete any post', async () => {
    useAuthStore().user = { id: 9, username: 'admin', is_staff: true } as unknown as User
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(deleteBlogPost).mockResolvedValue({} as never)
    const { wrapper } = await mountList()

    await wrapper.findAll('.blog-card')[1].find('button.danger-action').trigger('click')
    await flushPromises()

    expect(deleteBlogPost).toHaveBeenCalledWith(2)
    expect(listBlogPosts).toHaveBeenCalledTimes(2)
  })
})
