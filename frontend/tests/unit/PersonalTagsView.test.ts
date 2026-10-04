import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/personalTags', () => ({
  listPersonalTags: vi.fn(),
  createPersonalTag: vi.fn(),
  updatePersonalTag: vi.fn(),
  deletePersonalTag: vi.fn(),
  findSimilarPersonalTags: vi.fn(),
}))

import {
  createPersonalTag,
  deletePersonalTag,
  findSimilarPersonalTags,
  listPersonalTags,
  updatePersonalTag,
} from '../../src/api/personalTags'
import PersonalTagsView from '../../src/views/account/PersonalTagsView.vue'
import type { PersonalTag } from '../../src/types/models'

const PASTA: PersonalTag = { id: 1, name: 'Pâtes', emoji: '🍝', color: 'orange', recipes_count: 3 }
const TRY: PersonalTag = { id: 2, name: 'À tester', emoji: '', color: 'blue', recipes_count: 0 }

async function mountView() {
  const wrapper = mount(PersonalTagsView, {
    global: {
      plugins: [i18n],
      stubs: { RouterLink: { props: ['to'], template: '<a :data-to="JSON.stringify(to)"><slot /></a>' } },
    },
    attachTo: document.body,
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  vi.clearAllMocks()
  vi.useRealTimers()
  vi.mocked(listPersonalTags).mockResolvedValue([PASTA, TRY])
  vi.mocked(findSimilarPersonalTags).mockResolvedValue([])
})

describe('PersonalTagsView', () => {
  it('lists the tags with their recipe count, linking to the filtered recipe list', async () => {
    const wrapper = await mountView()
    const rows = wrapper.findAll('.tag-list li')
    expect(rows.map((row) => row.find('.personal-tag').text())).toEqual(['🍝Pâtes', 'À tester'])
    expect(rows[0].find('.recipes-link').text()).toBe('3 recettes')
    expect(rows[1].find('.recipes-link').text()).toBe('Aucune recette')
    expect(JSON.parse(rows[0].find('.recipes-link').attributes('data-to')!)).toEqual({
      name: 'recipes',
      query: { personal_tags: '1' },
    })
  })

  it('creates a tag with an emoji and a color', async () => {
    vi.mocked(createPersonalTag).mockResolvedValue({ id: 3, name: 'Brunch', emoji: '🥞', color: 'green' })
    const wrapper = await mountView()

    await wrapper.find('.page-header button').trigger('click')
    await wrapper.find('#personal-tag-name').setValue(' Brunch ')
    await wrapper.find('#personal-tag-emoji').setValue('🥞')
    await wrapper.find('input[type="radio"][value="green"]').setValue(true)
    expect(wrapper.find('form .personal-tag').attributes('style')).toContain('--tag-hue: #3f9d4b')
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    expect(createPersonalTag).toHaveBeenCalledWith({ name: 'Brunch', emoji: '🥞', color: 'green' })
    expect(listPersonalTags).toHaveBeenCalledTimes(2)
  })

  it('shows similar existing tags while typing a new name', async () => {
    vi.useFakeTimers()
    vi.mocked(findSimilarPersonalTags).mockResolvedValue([PASTA])
    const wrapper = await mountView()

    await wrapper.find('.page-header button').trigger('click')
    await wrapper.find('#personal-tag-name').setValue('pates')
    await vi.advanceTimersByTimeAsync(300)
    await flushPromises()

    expect(findSimilarPersonalTags).toHaveBeenCalledWith('pates', undefined)
    expect(wrapper.find('.similar-tags').text()).toContain('Pâtes')

    await wrapper.find('.similar-tag-button').trigger('click')
    expect(wrapper.find('form').exists()).toBe(false)
    expect(wrapper.find('.tag-list li.is-highlighted').text()).toContain('Pâtes')
  })

  it('edits a tag, excluding it from its own similar suggestions', async () => {
    vi.useFakeTimers()
    vi.mocked(updatePersonalTag).mockResolvedValue({ ...PASTA, name: 'Pâtes fraîches', color: 'red' })
    const wrapper = await mountView()

    await wrapper.findAll('.tag-list li')[0].find('button.secondary').trigger('click')
    expect((wrapper.find('#personal-tag-name').element as HTMLInputElement).value).toBe('Pâtes')
    await wrapper.find('#personal-tag-name').setValue('Pâtes fraîches')
    await vi.advanceTimersByTimeAsync(300)
    expect(findSimilarPersonalTags).toHaveBeenCalledWith('Pâtes fraîches', 1)

    await wrapper.find('input[type="radio"][value="red"]').setValue(true)
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(updatePersonalTag).toHaveBeenCalledWith(1, { name: 'Pâtes fraîches', emoji: '🍝', color: 'red' })
  })

  it('reports a duplicate name', async () => {
    vi.mocked(createPersonalTag).mockRejectedValue({ isAxiosError: true, response: { status: 400 } })
    const wrapper = await mountView()
    await wrapper.find('.page-header button').trigger('click')
    await wrapper.find('#personal-tag-name').setValue('pâtes')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(wrapper.find('form .error').text()).toBe('Vous avez déjà une étiquette de ce nom.')
  })

  it('deletes a tag after confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(deletePersonalTag).mockResolvedValue({} as never)
    const wrapper = await mountView()
    await wrapper.findAll('.tag-list li')[1].find('button.danger').trigger('click')
    await flushPromises()
    expect(deletePersonalTag).toHaveBeenCalledWith(2)
  })
})
