import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, reactive } from 'vue'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/personalTags', () => ({
  listPersonalTags: vi.fn(),
  createPersonalTag: vi.fn(),
  findSimilarPersonalTags: vi.fn(),
}))
vi.mock('../../src/api/recipes', () => ({
  setRecipeTags: vi.fn(),
}))

import { createPersonalTag, findSimilarPersonalTags, listPersonalTags } from '../../src/api/personalTags'
import { setRecipeTags } from '../../src/api/recipes'
import PersonalTagsEditor from '../../src/components/recipes/PersonalTagsEditor.vue'
import type { PersonalTag } from '../../src/types/models'

const PASTA: PersonalTag = { id: 1, name: 'Pâtes', emoji: '🍝', color: 'orange' }
const TRY: PersonalTag = { id: 2, name: 'À tester', emoji: '', color: 'blue' }

async function mountEditor(initial: PersonalTag[] = []) {
  const state = reactive({ tags: initial })
  const Host = defineComponent({
    components: { PersonalTagsEditor },
    setup: () => ({ state }),
    template: '<PersonalTagsEditor ref="editor" v-model="state.tags" :recipe-id="5" />',
  })
  const wrapper = mount(Host, {
    global: { plugins: [i18n], stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    attachTo: document.body,
  })
  await flushPromises()
  const editor = wrapper.findComponent(PersonalTagsEditor)
  return { wrapper, editor, state }
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  vi.clearAllMocks()
  vi.mocked(listPersonalTags).mockResolvedValue([PASTA, TRY])
  vi.mocked(setRecipeTags).mockImplementation((_id, ids) =>
    Promise.resolve([PASTA, TRY].filter((tag) => ids.includes(tag.id))),
  )
})

describe('PersonalTagsEditor', () => {
  it('shows the recipe tags in their color and removes one', async () => {
    const { wrapper, state } = await mountEditor([PASTA, TRY])
    const chips = wrapper.findAll('.selected-tag')
    expect(chips.map((chip) => chip.text())).toEqual(['🍝Pâtes', 'À tester'])
    expect(chips[0].attributes('style')).toContain('--tag-hue: #e07a1f')

    await chips[0].find('button.remove-tag').trigger('click')
    await flushPromises()
    expect(setRecipeTags).toHaveBeenCalledWith(5, [2])
    expect(state.tags).toEqual([TRY])
  })

  it('adds an existing tag typed with a different case instead of creating it', async () => {
    const { editor, state } = await mountEditor()
    await (editor.vm as unknown as { requestCreate: (name: string) => Promise<void> }).requestCreate('pâtes')
    await flushPromises()
    expect(findSimilarPersonalTags).not.toHaveBeenCalled()
    expect(createPersonalTag).not.toHaveBeenCalled()
    expect(state.tags).toEqual([PASTA])
  })

  it('creates a new tag directly when nothing similar exists', async () => {
    const BRUNCH: PersonalTag = { id: 3, name: 'Brunch', emoji: '', color: 'gray' }
    vi.mocked(findSimilarPersonalTags).mockResolvedValue([])
    vi.mocked(createPersonalTag).mockResolvedValue(BRUNCH)
    vi.mocked(setRecipeTags).mockResolvedValue([BRUNCH])
    const { editor, state } = await mountEditor()

    await (editor.vm as unknown as { requestCreate: (name: string) => Promise<void> }).requestCreate(' Brunch ')
    await flushPromises()
    expect(createPersonalTag).toHaveBeenCalledWith({ name: 'Brunch' })
    expect(setRecipeTags).toHaveBeenCalledWith(5, [3])
    expect(state.tags).toEqual([BRUNCH])
  })

  it('shows similar tags before creating, to reuse one or create anyway', async () => {
    vi.mocked(findSimilarPersonalTags).mockResolvedValue([PASTA])
    const { wrapper, editor, state } = await mountEditor()

    await (editor.vm as unknown as { requestCreate: (name: string) => Promise<void> }).requestCreate('Pates')
    await flushPromises()
    expect(createPersonalTag).not.toHaveBeenCalled()
    const hint = wrapper.find('.similar-tags')
    expect(hint.text()).toContain('Des étiquettes proches existent déjà')

    await hint.find('.similar-tag-button').trigger('click')
    await flushPromises()
    expect(state.tags).toEqual([PASTA])
    expect(wrapper.find('.similar-tags').exists()).toBe(false)

    const PATES: PersonalTag = { id: 4, name: 'Pates', emoji: '', color: 'gray' }
    vi.mocked(createPersonalTag).mockResolvedValue(PATES)
    vi.mocked(setRecipeTags).mockResolvedValue([PASTA, PATES])
    await (editor.vm as unknown as { requestCreate: (name: string) => Promise<void> }).requestCreate('Pates')
    await flushPromises()
    const createAnyway = wrapper.findAll('.similar-tags button').find((b) => b.text().includes('quand même'))
    await createAnyway!.trigger('click')
    await flushPromises()
    expect(createPersonalTag).toHaveBeenCalledWith({ name: 'Pates' })
    expect(state.tags).toEqual([PASTA, PATES])
  })

  it('restores the previous tags when saving fails', async () => {
    vi.mocked(setRecipeTags).mockRejectedValue(new Error('offline'))
    const { wrapper, state } = await mountEditor([PASTA])
    await wrapper.find('button.remove-tag').trigger('click')
    await flushPromises()
    expect(state.tags).toEqual([PASTA])
    expect(wrapper.find('[role="alert"]').text()).toBe("Impossible d'enregistrer l'étiquette.")
  })
})
