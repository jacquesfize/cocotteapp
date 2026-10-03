import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import RecipeComments from '../../src/components/recipes/RecipeComments.vue'
import { i18n } from '../../src/i18n'
import type { RecipeComment } from '../../src/types/models'

const { listRecipeComments, createRecipeComment, hideRecipeComment } = vi.hoisted(() => ({
  listRecipeComments: vi.fn(),
  createRecipeComment: vi.fn(),
  hideRecipeComment: vi.fn(),
}))

vi.mock('../../src/api/recipes', () => ({
  listRecipeComments,
  createRecipeComment,
  hideRecipeComment,
}))

function comment(overrides: Partial<RecipeComment> = {}): RecipeComment {
  return {
    id: 1,
    recipe: 1,
    author_name: 'Camille',
    username: null,
    body: 'Délicieux !',
    is_hidden: false,
    created_at: '2026-01-05T10:00:00Z',
    ...overrides,
  }
}

function mountComments(canModerate = false) {
  return mount(RecipeComments, {
    props: { recipeId: 1, canModerate },
    global: { plugins: [i18n] },
  })
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  listRecipeComments.mockReset()
  createRecipeComment.mockReset()
  hideRecipeComment.mockReset()
  listRecipeComments.mockResolvedValue({ count: 0, next: null, previous: null, results: [] })
})

describe('RecipeComments', () => {
  it('loads and displays existing comments', async () => {
    listRecipeComments.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [comment()],
    })

    const wrapper = mountComments()
    await flushPromises()

    expect(wrapper.text()).toContain('Camille')
    expect(wrapper.text()).toContain('Délicieux !')
  })

  it('shows an empty state when there are no comments', async () => {
    const wrapper = mountComments()
    await flushPromises()

    expect(wrapper.text()).toContain('Aucun commentaire pour l\'instant.')
  })

  it('submits a new comment without requiring authentication', async () => {
    createRecipeComment.mockResolvedValue(comment({ id: 2, author_name: 'Léo', body: 'Top recette' }))

    const wrapper = mountComments()
    await flushPromises()

    await wrapper.find('#comment-author-name').setValue('Léo')
    await wrapper.find('#comment-body').setValue('Top recette')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createRecipeComment).toHaveBeenCalledWith(1, { author_name: 'Léo', body: 'Top recette' })
    expect(wrapper.text()).toContain('Léo')
  })

  it('does not show a hide button unless canModerate is true', async () => {
    listRecipeComments.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [comment()],
    })

    const wrapper = mountComments(false)
    await flushPromises()

    expect(wrapper.find('button.secondary').exists()).toBe(false)
  })

  it('lets a moderator hide a comment', async () => {
    listRecipeComments.mockResolvedValue({
      count: 1,
      next: null,
      previous: null,
      results: [comment()],
    })
    hideRecipeComment.mockResolvedValue(comment({ is_hidden: true }))

    const wrapper = mountComments(true)
    await flushPromises()

    await wrapper.find('button.secondary').trigger('click')
    await flushPromises()

    expect(hideRecipeComment).toHaveBeenCalledWith(1, 1)
    expect(wrapper.text()).toContain('masqué')
  })
})
