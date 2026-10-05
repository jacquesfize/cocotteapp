import { enableAutoUnmount, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { i18n } from '../../src/i18n'
import IngredientSections from '../../src/components/recipes/IngredientSections.vue'
import type { IngredientFormRow } from '../../src/types/recipeForm'
import type { Ingredient } from '../../src/types/models'

enableAutoUnmount(afterEach)

beforeEach(() => {
  i18n.global.locale.value = 'fr'
})

const butter = { id: 1, name: 'Beurre', default_unit: 'g' } as Ingredient
const flour = { id: 2, name: 'Farine', default_unit: 'g' } as Ingredient

function formRow(ingredient: Ingredient | null, quantity: number | string, group_name = '', order = 1): IngredientFormRow {
  return { ingredient, quantity, unit: 'g', group_name, order }
}

// Le sélecteur d'ingrédient (recherche API) est remplacé par un champ simple : un test choisit
// l'ingrédient en émettant `update:modelValue` depuis le stub.
const IngredientPickerStub = defineComponent({
  props: { modelValue: { type: Object, default: null }, id: { type: String, default: '' } },
  emits: ['update:modelValue'],
  setup(props) {
    return () => h('input', { id: props.id, class: 'picker-stub' })
  },
})

// Reproduit le `v-model` du parent : les lignes émises sont renvoyées au composant.
function mountSections(rows: IngredientFormRow[], fieldErrors: Record<string, string> = {}) {
  const emitted: IngredientFormRow[][] = []
  const wrapper = mount(IngredientSections, {
    props: {
      modelValue: rows,
      fieldErrors,
      'onUpdate:modelValue': (next: IngredientFormRow[]) => {
        emitted.push(next)
        wrapper.setProps({ modelValue: next })
      },
    },
    global: { plugins: [i18n], stubs: { IngredientPicker: IngredientPickerStub } },
  })
  return { wrapper, emitted }
}

async function pickIngredient(wrapper: ReturnType<typeof mountSections>['wrapper'], ingredient: Ingredient) {
  wrapper.findComponent(IngredientPickerStub).vm.$emit('update:modelValue', ingredient)
  await wrapper.vm.$nextTick()
}

describe('IngredientSections', () => {
  it('shows no section name field while there is a single section', () => {
    const { wrapper } = mountSections([formRow(flour, 200, '', 1)])

    expect(wrapper.findAll('section.ingredient-section')).toHaveLength(1)
    expect(wrapper.find('input.section-name').exists()).toBe(false)
  })

  it('shows one bordered section per group name, each with an editable name, the first included', () => {
    const { wrapper } = mountSections([
      formRow(flour, 200, 'Pâte', 1),
      formRow(butter, 80, 'Pâte', 2),
      formRow(butter, 50, 'Garniture', 3),
    ])

    const sections = wrapper.findAll('section.ingredient-section')
    expect(sections).toHaveLength(2)
    expect((sections[0].find('input.section-name').element as HTMLInputElement).value).toBe('Pâte')
    expect(sections[0].findAll('li.ingredient-item')).toHaveLength(2)
    expect((sections[1].find('input.section-name').element as HTMLInputElement).value).toBe('Garniture')
  })

  it('lets the first section stay unnamed, or be renamed, which renames its rows', async () => {
    const { wrapper, emitted } = mountSections([formRow(flour, 200, '', 1), formRow(butter, 50, 'Garniture', 2)])
    const [first] = wrapper.findAll('input.section-name')
    expect(first.attributes('placeholder')).toBe('Sans section')

    await first.setValue('Pâte')
    expect(emitted.at(-1)!.map((row) => row.group_name)).toEqual(['Pâte', 'Garniture'])

    await first.setValue('')
    expect(wrapper.text()).not.toContain('Une section doit avoir un nom.')
    expect(emitted.at(-1)!.map((row) => row.group_name)).toEqual(['', 'Garniture'])
  })

  it('adds a row that has no section (e.g. from a step mention) to the first section', async () => {
    const { wrapper, emitted } = mountSections([formRow(flour, 200, 'Pâte', 1), formRow(butter, 50, 'Garniture', 2)])

    await wrapper.setProps({ modelValue: [...wrapper.props('modelValue'), formRow(flour, '', '', 3)] })

    expect(emitted.at(-1)!.map((row) => row.group_name)).toEqual(['Pâte', 'Pâte', 'Garniture'])
  })

  it('adds an ingredient through the modal, in the section whose plus button was used', async () => {
    const { wrapper, emitted } = mountSections([formRow(flour, 200, 'Pâte', 1), formRow(flour, 30, 'Garniture', 2)])

    await wrapper.findAll('section')[1].find('button.ingredient-add').trigger('click')
    await pickIngredient(wrapper, butter)
    await wrapper.find('#row-modal-quantity').setValue('80')
    await wrapper.find('#row-modal-quantity').trigger('keydown.enter')

    const rows = emitted.at(-1)!
    expect(rows).toHaveLength(3)
    expect(rows[2]).toMatchObject({ ingredient: butter, quantity: 80, unit: 'g', group_name: 'Garniture' })
    expect(wrapper.find('#row-modal-quantity').exists()).toBe(false)
  })

  it('lets the same ingredient be used in two sections', async () => {
    const { wrapper, emitted } = mountSections([formRow(butter, 80, '', 1)])

    await wrapper.find('button.secondary:not(.ingredient-add):not(.icon-btn)').trigger('click')
    const sectionInput = wrapper.findAll('input.section-name')[1]
    await sectionInput.setValue('Garniture')
    await wrapper.findAll('section')[1].find('button.ingredient-add').trigger('click')
    await pickIngredient(wrapper, butter)
    await wrapper.find('#row-modal-quantity').setValue('50')
    await wrapper.find('#row-modal-quantity').trigger('keydown.enter')

    const rows = emitted.at(-1)!
    expect(rows.map((row) => [row.ingredient?.name, row.quantity, row.group_name])).toEqual([
      ['Beurre', 80, ''],
      ['Beurre', 50, 'Garniture'],
    ])
  })

  it('refuses an empty or duplicate section name and renames the rows of a valid one', async () => {
    const { wrapper, emitted } = mountSections([formRow(flour, 200, 'Pâte', 1), formRow(butter, 50, 'Garniture', 2)])

    const garniture = wrapper.findAll('input.section-name')[1]
    await garniture.setValue('Pâte')
    expect(wrapper.text()).toContain('Une autre section porte déjà ce nom.')
    expect(emitted).toHaveLength(0)

    await garniture.setValue('')
    expect(wrapper.text()).toContain('Une section doit avoir un nom.')

    await garniture.setValue('Crème')
    expect(emitted.at(-1)!.map((row) => row.group_name)).toEqual(['Pâte', 'Crème'])
  })

  it('does not add an ingredient without a quantity and shows why', async () => {
    const { wrapper, emitted } = mountSections([])

    await wrapper.find('button.ingredient-add').trigger('click')
    await pickIngredient(wrapper, butter)
    await wrapper.find('#row-modal-quantity').trigger('keydown.enter')

    expect(emitted).toHaveLength(0)
    expect(wrapper.text()).toContain('Quantité')
    expect(wrapper.find('#row-modal-quantity').attributes('aria-invalid')).toBe('true')
  })

  it('edits an existing row from the modal, and clears the "not found" state of an imported one', async () => {
    const imported: IngredientFormRow = { ...formRow(null, 1), unmatched: true, raw_line: '1 noix de beurre' }
    const { wrapper, emitted } = mountSections([imported])
    expect(wrapper.text()).toContain('1 noix de beurre')

    await wrapper.find('#ingredient-0').trigger('click')
    await pickIngredient(wrapper, butter)
    await wrapper.find('#row-modal-quantity').setValue('20')
    await wrapper.find('#row-modal-quantity').trigger('keydown.enter')

    expect(emitted.at(-1)![0]).toMatchObject({ ingredient: butter, quantity: 20, unmatched: false })
  })

  it('removes a row, and asks before removing a section that still has ingredients', async () => {
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)
    const { wrapper, emitted } = mountSections([formRow(butter, 50, '', 1), formRow(flour, 200, 'Pâte', 2)])

    // La première section est celle sans nom : sa seule ligne est le beurre.
    await wrapper.findAll('li.ingredient-item')[0].findAll('button')[1].trigger('click')
    expect(emitted.at(-1)!.map((row) => row.ingredient?.name)).toEqual(['Farine'])

    const removePate = () => wrapper.findAll('section')[1].find('.ingredient-section-header button')
    await removePate().trigger('click')
    expect(confirmSpy).toHaveBeenCalledTimes(1)
    expect(emitted).toHaveLength(1) // refusé : rien n'a changé

    confirmSpy.mockReturnValue(true)
    await removePate().trigger('click')
    expect(emitted.at(-1)).toEqual([])

    confirmSpy.mockRestore()
  })
})
