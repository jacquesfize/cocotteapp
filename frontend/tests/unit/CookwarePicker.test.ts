import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/cookware', () => ({
  listCookware: vi.fn(),
  createCookware: vi.fn(),
  updateCookware: vi.fn(),
  deleteCookware: vi.fn(),
}))

import { deleteCookware, listCookware, updateCookware } from '../../src/api/cookware'
import CookwareEditModal from '../../src/components/recipes/CookwareEditModal.vue'
import CookwarePicker from '../../src/components/recipes/CookwarePicker.vue'
import type { Cookware } from '../../src/types/models'

const OVEN: Cookware = { id: 1, name: 'Four', slug: 'four', is_verified: true, can_edit: false }
const WOK: Cookware = {
  id: 3,
  name: 'Wok maison',
  slug: 'wok-maison',
  translations: { de: 'Wok' },
  is_verified: false,
  created_by: 7,
  created_by_username: 'bob',
  can_edit: true,
}

enableAutoUnmount(afterEach)

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  vi.clearAllMocks()
  vi.mocked(listCookware).mockResolvedValue([OVEN, WOK])
  window.confirm = vi.fn(() => true)
})

async function mountPicker(modelValue: Cookware[] = [OVEN, WOK]) {
  const wrapper = mount(CookwarePicker, {
    props: { modelValue, 'onUpdate:modelValue': (value: Cookware[]) => wrapper.setProps({ modelValue: value }) },
    global: { plugins: [i18n] },
  })
  await flushPromises()
  return wrapper
}

function tag(wrapper: Awaited<ReturnType<typeof mountPicker>>, name: string) {
  return wrapper.findAll('.cookware-tag').find((t) => t.text().includes(name))!
}

describe('CookwarePicker', () => {
  it('flags unverified cookware and offers editing only when allowed', async () => {
    const wrapper = await mountPicker()
    expect(tag(wrapper, 'Four').find('[data-testid="unverified-badge"]').exists()).toBe(false)
    expect(tag(wrapper, 'Four').find('[data-testid="cookware-picker-edit"]').exists()).toBe(false)
    expect(tag(wrapper, 'Wok maison').find('[data-testid="unverified-badge"]').exists()).toBe(true)
    expect(tag(wrapper, 'Wok maison').find('[data-testid="cookware-picker-edit"]').exists()).toBe(true)
  })

  it('edits the cookware and updates the selection', async () => {
    const fixed = { ...WOK, name: 'Wok', translations: { de: 'Wok', en: 'wok' } }
    vi.mocked(updateCookware).mockResolvedValue(fixed)
    const wrapper = await mountPicker()

    await tag(wrapper, 'Wok maison').get('[data-testid="cookware-picker-edit"]').trigger('click')
    const modal = wrapper.findComponent(CookwareEditModal)
    expect(modal.text()).toContain('un administrateur va le vérifier')
    await modal.get('#cookware-edit-name').setValue('Wok')
    await modal.get('#cookware-edit-name-en').setValue('wok')
    await modal.get('form').trigger('submit.prevent')
    await flushPromises()

    expect(updateCookware).toHaveBeenCalledWith(3, { name: 'Wok', translations: { de: 'Wok', en: 'wok' }, emoji: '' })
    expect(wrapper.findComponent(CookwareEditModal).exists()).toBe(false)
    expect(wrapper.props('modelValue')).toEqual([OVEN, fixed])
  })

  it('reports a duplicate name', async () => {
    vi.mocked(updateCookware).mockRejectedValue({ response: { status: 400 } })
    const wrapper = await mountPicker()

    await tag(wrapper, 'Wok maison').get('[data-testid="cookware-picker-edit"]').trigger('click')
    await wrapper.findComponent(CookwareEditModal).get('form').trigger('submit.prevent')
    await flushPromises()

    expect(wrapper.findComponent(CookwareEditModal).text()).toContain('Ce matériel existe déjà.')
  })

  it('deletes the cookware and removes it from the selection', async () => {
    vi.mocked(deleteCookware).mockResolvedValue(undefined as never)
    const wrapper = await mountPicker()

    await tag(wrapper, 'Wok maison').get('[data-testid="cookware-picker-edit"]').trigger('click')
    await wrapper.get('[data-testid="cookware-edit-delete"]').trigger('click')
    await flushPromises()

    expect(deleteCookware).toHaveBeenCalledWith(3)
    expect(wrapper.props('modelValue')).toEqual([OVEN])
    expect(wrapper.findComponent(CookwareEditModal).exists()).toBe(false)
  })
})
