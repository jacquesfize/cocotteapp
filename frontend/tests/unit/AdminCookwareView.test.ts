import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { i18n } from '../../src/i18n'

vi.mock('../../src/api/cookware', () => ({
  listCookware: vi.fn(),
  createCookware: vi.fn(),
  updateCookware: vi.fn(),
  deleteCookware: vi.fn(),
  mergeCookware: vi.fn(),
  uploadCookwareImage: vi.fn(),
  removeCookwareImage: vi.fn(),
}))

import {
  createCookware,
  deleteCookware,
  listCookware,
  mergeCookware,
  removeCookwareImage,
  updateCookware,
  uploadCookwareImage,
} from '../../src/api/cookware'
import AdminCookwareView from '../../src/views/admin/AdminCookwareView.vue'

const OVEN = { id: 1, name: 'Four', slug: 'four', emoji: '', image: '/media/cookware/four.jpg', translations: { en: 'oven', de: 'Ofen' } }
const PAN = { id: 2, name: 'Poêle', slug: 'poele', emoji: '🍳', image: null, translations: {} }
const WOK = {
  id: 3,
  name: 'Wok maison',
  slug: 'wok-maison',
  emoji: '',
  image: null,
  translations: {},
  is_verified: false,
  created_by: 7,
  created_by_username: 'bob',
  can_edit: true,
}

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

  describe('review queue', () => {
    beforeEach(() => {
      vi.mocked(listCookware).mockResolvedValue([OVEN, PAN, WOK])
    })

    it('counts, badges and filters unverified cookware', async () => {
      const wrapper = await mountView()
      expect(wrapper.get('.admin-filter-count').text()).toBe('1')
      const rows = wrapper.findAll('tbody tr')
      expect(rows[0].find('[data-testid="unverified-badge"]').exists()).toBe(false)
      expect(rows[2].get('[data-testid="unverified-badge"]').text()).toContain('Non vérifié · ajouté par bob')

      await wrapper.get('[data-testid="filter-unverified"]').trigger('click')
      expect(wrapper.get('[data-testid="filter-unverified"]').attributes('aria-pressed')).toBe('true')
      expect(wrapper.findAll('tbody tr').map((row) => row.find('.name').text())).toEqual([
        expect.stringContaining('Wok maison'),
      ])
      wrapper.unmount()
    })

    it('verifies cookware and updates its row', async () => {
      vi.mocked(updateCookware).mockResolvedValue({ ...WOK, is_verified: true })
      const wrapper = await mountView()

      await wrapper.get('[data-testid="verify"]').trigger('click')
      await flushPromises()

      expect(updateCookware).toHaveBeenCalledWith(3, { is_verified: true })
      expect(wrapper.find('[data-testid="unverified-badge"]').exists()).toBe(false)
      expect(wrapper.get('.admin-filter-count').text()).toBe('0')
      wrapper.unmount()
    })

    it('merges cookware into another one picked from the list', async () => {
      vi.mocked(mergeCookware).mockResolvedValue(PAN)
      const wrapper = await mountView()

      await wrapper.findAll('tbody tr')[2].get('[data-testid="merge"]').trigger('click')
      const select = wrapper.get('#cookware-merge-target')
      // Le matériel fusionné n'est pas proposé comme cible.
      expect(select.findAll('option').map((o) => o.text())).toEqual([
        'Choisir un matériel…',
        'Four',
        '🍳 Poêle',
      ])
      expect(wrapper.get('[role="dialog"] button[type="submit"]').attributes('disabled')).toBeDefined()

      await select.setValue('2')
      expect(wrapper.get('[data-testid="merge-confirm"]').text()).toContain(
        'Les recettes qui utilisent « Wok maison » passeront sur « Poêle »',
      )
      await wrapper.get('[role="dialog"] form').trigger('submit.prevent')
      await flushPromises()

      expect(mergeCookware).toHaveBeenCalledWith(3, 2)
      expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
      expect(listCookware).toHaveBeenCalledTimes(2)
      expect(wrapper.get('[role="status"]').text()).toContain('« Wok maison » a été fusionné dans « Poêle »')
      wrapper.unmount()
    })

    it('reports a failed merge', async () => {
      vi.mocked(mergeCookware).mockRejectedValue({ response: { status: 400 } })
      const wrapper = await mountView()

      await wrapper.findAll('tbody tr')[2].get('[data-testid="merge"]').trigger('click')
      await wrapper.get('#cookware-merge-target').setValue('1')
      await wrapper.get('[role="dialog"] form').trigger('submit.prevent')
      await flushPromises()

      expect(wrapper.get('[role="dialog"] [role="alert"]').text()).toContain('Fusion impossible')
      wrapper.unmount()
    })
  })
})
