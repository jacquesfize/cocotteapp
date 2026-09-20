import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'
import AllergenBadges from '../../src/components/AllergenBadges.vue'
import { i18n } from '../../src/i18n'
import { useAuthStore } from '../../src/stores/auth'
import type { User } from '../../src/types/models'

function mountBadges(props: InstanceType<typeof AllergenBadges>['$props']) {
  return mount(AllergenBadges, { props, global: { plugins: [i18n] } })
}

beforeEach(() => {
  setActivePinia(createPinia())
  i18n.global.locale.value = 'fr'
  useAuthStore().user = { allergies: ['peanut'], intolerances: ['lactose'] } as unknown as User
})

describe('AllergenBadges', () => {
  it('marks allergies and intolerances of the profile, allergies first', () => {
    const wrapper = mountBadges({ allergens: ['gluten', 'lactose', 'peanut'] })

    const order = wrapper.findAll('.allergen-badge').map((b) => b.attributes('data-testid'))
    expect(order).toEqual(['allergen-peanut', 'allergen-lactose', 'allergen-gluten'])
    expect(wrapper.find('[data-testid="allergen-peanut"]').classes()).toContain('allergy')
    expect(wrapper.find('[data-testid="allergen-lactose"]').classes()).toContain('intolerance')
    expect(wrapper.find('[data-testid="allergen-gluten"]').classes()).toContain('neutral')
  })

  it('only shows the profile allergens in compact mode', () => {
    const wrapper = mountBadges({ allergens: ['gluten', 'peanut'], onlyMine: true, unverified: true })

    expect(wrapper.findAll('.allergen-badge')).toHaveLength(1)
    expect(wrapper.text()).not.toContain('non vérifiés')
  })

  it('flags unverified ingredients and renders nothing when there is nothing to say', () => {
    expect(mountBadges({ allergens: [], unverified: true }).text()).toContain('non vérifiés')
    expect(mountBadges({ allergens: [] }).find('.allergen-badges').exists()).toBe(false)
  })
})
