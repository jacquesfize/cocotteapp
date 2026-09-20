import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import AllergenWarning from '../../src/components/AllergenWarning.vue'
import { i18n } from '../../src/i18n'
import { matchUserAllergens } from '../../src/utils/allergens'
import { useAuthStore } from '../../src/stores/auth'
import type { User } from '../../src/types/models'

beforeEach(() => {
  setActivePinia(createPinia())
  i18n.global.locale.value = 'fr'
  useAuthStore().user = { allergies: ['peanut'], intolerances: ['lactose'] } as unknown as User
})

describe('matchUserAllergens', () => {
  it('splits recipe allergens by profile severity and ignores the others', () => {
    expect(matchUserAllergens(['gluten', 'lactose', 'peanut'], useAuthStore().user)).toEqual({
      allergies: ['peanut'],
      intolerances: ['lactose'],
    })
    expect(matchUserAllergens(undefined, null)).toEqual({ allergies: [], intolerances: [] })
  })
})

describe('AllergenWarning', () => {
  it('warns separately about allergies and intolerances', () => {
    const wrapper = mount(AllergenWarning, {
      props: { allergens: ['gluten', 'lactose', 'peanut'] },
      global: { plugins: [i18n] },
    })

    expect(wrapper.get('[data-testid="warning-allergy"]').text()).toContain('Arachides')
    expect(wrapper.get('[data-testid="warning-intolerance"]').text()).toContain('Lactose')
    expect(wrapper.text()).not.toContain('Gluten')
  })

  it('renders nothing when the recipe has no allergen of the profile', () => {
    const wrapper = mount(AllergenWarning, { props: { allergens: ['gluten'] }, global: { plugins: [i18n] } })

    expect(wrapper.find('.allergen-warning').exists()).toBe(false)
  })
})
