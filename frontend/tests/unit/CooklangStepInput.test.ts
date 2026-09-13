import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import CooklangStepInput from '../../src/components/CooklangStepInput.vue'
import { i18n } from '../../src/i18n'

function mountInput(modelValue = '') {
  return mount(CooklangStepInput, {
    props: { modelValue, ingredientNames: ['poireau', 'huile olive'] },
    global: { plugins: [i18n] },
  })
}

// Le composant est en v-model manuel (:value/@input) : hors d'un vrai parent, il faut
// re-synchroniser modelValue nous-mêmes après chaque frappe, comme le ferait un v-model.
async function typeInto(wrapper: ReturnType<typeof mountInput>, value: string) {
  const textarea = wrapper.get('textarea')
  await textarea.setValue(value)
  await wrapper.setProps({ modelValue: value })
}

describe('CooklangStepInput', () => {
  it('shows ingredient suggestions filtered by what follows "@"', async () => {
    const wrapper = mountInput()
    await typeInto(wrapper, 'Faire revenir le @poi')

    const items = wrapper.findAll('.suggestions li')
    expect(items).toHaveLength(1)
    expect(items[0].text()).toBe('poireau')
  })

  it('hides suggestions once a space is typed after the "@" word', async () => {
    const wrapper = mountInput()
    await typeInto(wrapper, 'Faire revenir le @poireau ')

    expect(wrapper.find('.suggestions').exists()).toBe(false)
  })

  it('inserts the underscore-joined token when a multi-word suggestion is picked', async () => {
    const wrapper = mountInput()
    await typeInto(wrapper, 'Ajouter @huile')

    await wrapper.get('.suggestions li').trigger('mousedown')

    expect(wrapper.emitted('update:modelValue')?.at(-1)?.[0]).toBe('Ajouter @huile_olive ')
  })

  it('warns about a mention that matches no known ingredient', async () => {
    const wrapper = mountInput('Ajouter le @beurre puis mélanger.')
    expect(wrapper.text()).toContain('beurre')
    expect(wrapper.find('.mention-warning').exists()).toBe(true)
  })

  it('shows no warning once every mention matches a known ingredient', () => {
    const wrapper = mountInput('Faire revenir le @poireau puis ajouter le @huile_olive et mélanger.')
    expect(wrapper.find('.mention-warning').exists()).toBe(false)
  })
})
