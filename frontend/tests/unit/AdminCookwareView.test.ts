import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/cookware', () => ({
  listCookware: vi.fn(),
  createCookware: vi.fn(),
  updateCookware: vi.fn(),
  deleteCookware: vi.fn(),
  uploadCookwareImage: vi.fn(),
  removeCookwareImage: vi.fn(),
}))

import {
  createCookware,
  deleteCookware,
  listCookware,
  removeCookwareImage,
  updateCookware,
  uploadCookwareImage,
} from '../../src/api/cookware'
import AdminCookwareView from '../../src/views/admin/AdminCookwareView.vue'

const OVEN = { id: 1, name: 'Four', slug: 'four', emoji: '', image: '/media/cookware/four.jpg', translations: { en: 'oven', de: 'Ofen' } }
const PAN = { id: 2, name: 'Poêle', slug: 'poele', emoji: '🍳', image: null, translations: {} }

async function mountView() {
  const wrapper = mount(AdminCookwareView, { global: { plugins: [i18n] }, attachTo: document.body })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  i18n.global.locale.value = 'fr'
  vi.clearAllMocks()
  vi.mocked(listCookware).mockResolvedValue([OVEN, PAN])
})

describe('AdminCookwareView', () => {
  it('lists the cookware and filters it by French or English name', async () => {
    const wrapper = await mountView()
    expect(wrapper.findAll('tbody tr').map((row) => row.find('.name').text())).toEqual(['Four', 'Poêle'])

    await wrapper.find('#admin-cookware-search').setValue('OVEN')
    expect(wrapper.findAll('tbody tr').map((row) => row.find('.name').text())).toEqual(['Four'])
  })

  it('creates cookware with its English name', async () => {
    vi.mocked(createCookware).mockResolvedValue({ id: 3, name: 'Wok', slug: 'wok' })
    const wrapper = await mountView()

    await wrapper.findAll('button').find((b) => b.text().includes('Nouveau matériel'))!.trigger('click')
    await wrapper.find('#cookware-modal-name').setValue(' Wok ')
    await wrapper.find('#cookware-modal-name-en').setValue('wok')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(createCookware).toHaveBeenCalledWith({ name: 'Wok', translations: { en: 'wok' }, emoji: '' })
    expect(listCookware).toHaveBeenCalledTimes(2)
  })

  it('edits cookware, keeping its other translations, and reports a duplicate name', async () => {
    vi.mocked(updateCookware).mockRejectedValueOnce({ response: { status: 400 } })
    const wrapper = await mountView()

    await wrapper.findAll('tbody tr')[0].find('button.secondary').trigger('click')
    expect((wrapper.find('#cookware-modal-name-en').element as HTMLInputElement).value).toBe('oven')
    await wrapper.find('#cookware-modal-name').setValue('Poêle')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()

    expect(updateCookware).toHaveBeenCalledWith(1, { name: 'Poêle', translations: { en: 'oven', de: 'Ofen' }, emoji: '' })
    expect(wrapper.text()).toContain('Ce matériel existe déjà.')
  })

  it('deletes cookware after confirmation', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    vi.mocked(deleteCookware).mockResolvedValue(undefined as never)
    const wrapper = await mountView()

    await wrapper.findAll('tbody tr')[1].find('button.danger').trigger('click')
    await flushPromises()

    expect(deleteCookware).toHaveBeenCalledWith(2)
  })

  it('shows the photo or emoji of each item in the table', async () => {
    const wrapper = await mountView()
    const rows = wrapper.findAll('tbody tr')
    expect(rows[0].find('img.image-thumb').attributes('src')).toBe('/media/cookware/four.jpg')
    expect(rows[1].find('.emoji').text()).toBe('🍳')
  })

  it('saves the emoji, uploads a new photo, and removes an existing one', async () => {
    vi.mocked(updateCookware).mockImplementation(async (id) => (id === 1 ? OVEN : PAN))
    const wrapper = await mountView()

    // Poêle : nouvel emoji + photo téléversée après l'enregistrement.
    await wrapper.findAll('tbody tr')[1].find('button.secondary').trigger('click')
    await wrapper.find('#cookware-modal-emoji').setValue('🥘')
    const file = new File(['x'], 'poele.jpg', { type: 'image/jpeg' })
    const input = wrapper.find('#cookware-modal-image')
    Object.defineProperty(input.element, 'files', { value: [file] })
    globalThis.URL.createObjectURL = vi.fn(() => 'blob:preview')
    await input.trigger('change')
    // Une nouvelle photo exige sa licence, et son auteur + sa source en CC BY-SA.
    await wrapper.find('form').trigger('submit.prevent')
    expect(wrapper.text()).toContain('Choisissez une licence')
    await wrapper.find('#cookware-modal-license').setValue('cc_by_sa')
    await wrapper.find('form').trigger('submit.prevent')
    expect(updateCookware).not.toHaveBeenCalled()
    await wrapper.find('#cookware-modal-author').setValue('Pengo')
    await wrapper.find('#cookware-modal-source').setValue('https://commons.wikimedia.org/wiki/File:X.jpg')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(updateCookware).toHaveBeenCalledWith(2, { name: 'Poêle', translations: {}, emoji: '🥘' })
    expect(uploadCookwareImage).toHaveBeenCalledWith(2, file, {
      image_license: 'cc_by_sa',
      image_credit_author: 'Pengo',
      image_credit_source_url: 'https://commons.wikimedia.org/wiki/File:X.jpg',
      image_credit_license_url: 'https://creativecommons.org/licenses/by-sa/4.0/',
    })

    // Four : retrait de la photo existante.
    await wrapper.findAll('tbody tr')[0].find('button.secondary').trigger('click')
    await wrapper.findAll('button').find((b) => b.text() === 'Retirer la photo')!.trigger('click')
    await wrapper.find('form').trigger('submit.prevent')
    await flushPromises()
    expect(removeCookwareImage).toHaveBeenCalledWith(1)
  })
})
