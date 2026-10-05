import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import RecipeCookMode from '../../src/components/recipes/RecipeCookMode.vue'
import { useIngredientSwaps } from '../../src/composables/useIngredientSwaps'
import { i18n } from '../../src/i18n'
import type { Recipe, RecipeStep } from '../../src/types/models'

function step(overrides: Pick<RecipeStep, 'id' | 'order' | 'instruction'>): RecipeStep {
  return {
    image: null,
    image_url: '',
    image_license: '',
    image_credit_author: '',
    image_credit_source_url: '',
    image_credit_license_url: '',
    image_credit_note: '',
    ...overrides,
  }
}

function baseRecipe(overrides: Partial<Recipe> = {}): Recipe {
  return {
    id: 1,
    title: 'Recette',
    slug: 'recette',
    description: '',
    author: 'chef',
    author_id: 1,
    servings: 4,
    prep_time_minutes: 10,
    cook_time_minutes: 20,
    total_time_minutes: 30,
    diet_type: 'omnivore',
    source_type: 'manual',
    source_url: '',
    video_url: '',
    youtube_id: null,
    image: '',
    image_url: '',
    is_public: true,
    ingredients: [
      {
        id: 1,
        ingredient: {
          id: 10,
          name: 'sel',
          slug: 'sel',
          category: 'condiment',
          default_unit: 'g',
          available_months: [],
          calories_kcal: 0,
          protein_g: 0,
          carbs_g: 0,
          fat_g: 0,
          fiber_g: 0,
          iron_mg: 0,
          vitamin_b12_ug: 0,
          calcium_mg: 0,
          omega3_g: 0,
          zinc_mg: 0,
        },
        quantity: 2,
        unit: 'pinch',
        group_name: '',
        order: 0,
      },
    ],
    steps: [
      step({ id: 1, order: 0, instruction: 'Ajouter le @sel puis mélanger.' }),
      step({ id: 2, order: 1, instruction: 'Servir chaud.' }),
    ],
    ...overrides,
  } as Recipe
}

function mountCookMode(recipe: Recipe) {
  return mount(RecipeCookMode, {
    props: { recipe },
    global: { plugins: [i18n] },
  })
}

function touch(x: number, y: number) {
  return { clientX: x, clientY: y } as Touch
}

describe('RecipeCookMode', () => {
  it('shows the first step and the step counter', () => {
    const wrapper = mountCookMode(baseRecipe())
    expect(wrapper.text()).toContain('Étape 1 / 2')
    expect(wrapper.text()).toContain('sel')
    expect(wrapper.find('.cook-mode-nav.prev').exists()).toBe(false)
  })

  it('navigates to the next step with the chevron button and back with prev', async () => {
    const wrapper = mountCookMode(baseRecipe())
    await wrapper.find('.cook-mode-nav.next').trigger('click')
    expect(wrapper.text()).toContain('Étape 2 / 2')
    expect(wrapper.text()).toContain('Servir chaud.')

    await wrapper.find('.cook-mode-nav.prev').trigger('click')
    expect(wrapper.text()).toContain('Étape 1 / 2')
  })

  it('exits cook mode when "next" is pressed on the last step', async () => {
    const wrapper = mountCookMode(baseRecipe())
    await wrapper.find('.cook-mode-nav.next').trigger('click')
    expect(wrapper.text()).toContain('Étape 2 / 2')

    await wrapper.find('.cook-mode-nav.next').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('navigates between steps with a swipe gesture', async () => {
    const wrapper = mountCookMode(baseRecipe())
    const body = wrapper.find('.cook-mode-body')

    await body.trigger('touchstart', { touches: [touch(300, 100)] })
    await body.trigger('touchend', { changedTouches: [touch(50, 100)] })
    expect(wrapper.text()).toContain('Étape 2 / 2')

    await body.trigger('touchstart', { touches: [touch(50, 100)] })
    await body.trigger('touchend', { changedTouches: [touch(300, 100)] })
    expect(wrapper.text()).toContain('Étape 1 / 2')
  })

  it('ignores a short or mostly-vertical touch move', async () => {
    const wrapper = mountCookMode(baseRecipe())
    const body = wrapper.find('.cook-mode-body')

    await body.trigger('touchstart', { touches: [touch(300, 100)] })
    await body.trigger('touchend', { changedTouches: [touch(280, 100)] })
    expect(wrapper.text()).toContain('Étape 1 / 2')

    await body.trigger('touchstart', { touches: [touch(300, 100)] })
    await body.trigger('touchend', { changedTouches: [touch(100, 400)] })
    expect(wrapper.text()).toContain('Étape 1 / 2')
  })

  it('opens a popover with the quantity when an ingredient mention is clicked', async () => {
    const wrapper = mountCookMode(baseRecipe())
    expect(wrapper.find('.ingredient-popover').exists()).toBe(false)

    await wrapper.find('button.ingredient-mention').trigger('click')
    expect(wrapper.find('.ingredient-popover').exists()).toBe(true)
    expect(wrapper.text()).toContain('2 pincées')

    await wrapper.find('button.ingredient-mention').trigger('click')
    expect(wrapper.find('.ingredient-popover').exists()).toBe(false)
  })

  it('shows the popover on mouseenter and hides it on mouseleave', async () => {
    const wrapper = mountCookMode(baseRecipe())
    const wrap = wrapper.find('.ingredient-mention-wrap')

    await wrap.trigger('mouseenter')
    expect(wrapper.find('.ingredient-popover').exists()).toBe(true)

    await wrap.trigger('mouseleave')
    expect(wrapper.find('.ingredient-popover').exists()).toBe(false)
  })

  it('closes a clicked (pinned) popover when clicking outside it', async () => {
    const wrapper = mountCookMode(baseRecipe())
    await wrapper.find('button.ingredient-mention').trigger('click')
    expect(wrapper.find('.ingredient-popover').exists()).toBe(true)

    document.body.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.ingredient-popover').exists()).toBe(false)
  })

  it('toggles the ingredients panel', async () => {
    const wrapper = mountCookMode(baseRecipe())
    const panel = wrapper.find('.cook-mode-ingredients')
    expect(panel.classes()).not.toContain('open')

    await wrapper.find('[aria-label="Voir les ingrédients"]').trigger('click')
    expect(panel.classes()).toContain('open')
    expect(panel.text()).toContain('sel')
  })

  it('closes the ingredients panel when clicking outside it', async () => {
    const wrapper = mountCookMode(baseRecipe())
    await wrapper.find('[aria-label="Voir les ingrédients"]').trigger('click')
    expect(wrapper.find('.cook-mode-ingredients').classes()).toContain('open')

    await wrapper.find('.cook-mode-backdrop').trigger('click')
    expect(wrapper.find('.cook-mode-ingredients').classes()).not.toContain('open')
  })

  it('closes the ingredients panel on Escape before closing cook mode', async () => {
    const wrapper = mountCookMode(baseRecipe())
    await wrapper.find('[aria-label="Voir les ingrédients"]').trigger('click')

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.cook-mode-ingredients').classes()).not.toContain('open')
    expect(wrapper.emitted('close')).toBeUndefined()

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('emits close when the close button is clicked', async () => {
    const wrapper = mountCookMode(baseRecipe())
    await wrapper.find('[aria-label="Fermer"]').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('shows a discreet link to the YouTube video when the recipe has one', () => {
    const withVideo = mountCookMode(baseRecipe({ youtube_id: 'abc123' }))
    const link = withVideo.find('.cook-mode-video-link')
    expect(link.exists()).toBe(true)
    expect(link.attributes('href')).toBe('https://www.youtube.com/watch?v=abc123')
    expect(link.attributes('target')).toBe('_blank')

    const withoutVideo = mountCookMode(baseRecipe())
    expect(withoutVideo.find('.cook-mode-video-link').exists()).toBe(false)
  })
})

describe('RecipeCookMode timer dock', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const recipeWithTimer = () =>
    baseRecipe({
      steps: [
        step({ id: 1, order: 0, instruction: 'Laisser reposer ~{2%minutes}.' }),
        step({ id: 2, order: 1, instruction: 'Servir chaud.' }),
      ],
    })

  it('keeps a started timer running and visible in the dock after navigating away and back', async () => {
    const wrapper = mountCookMode(recipeWithTimer())
    expect(wrapper.find('.cook-mode-timer-dock').exists()).toBe(false)

    await wrapper.find('.timer-chip').trigger('click')
    expect(wrapper.find('.cook-mode-timer-dock-row').exists()).toBe(true)
    expect(wrapper.find('.cook-mode-timer-dock-clock').text()).toBe('2:00')

    await wrapper.find('.cook-mode-nav.next').trigger('click')
    expect(wrapper.text()).toContain('Servir chaud.')
    expect(wrapper.find('.cook-mode-timer-dock-row').exists()).toBe(true)

    await vi.advanceTimersByTimeAsync(3000)
    expect(wrapper.find('.cook-mode-timer-dock-clock').text()).toBe('1:57')

    await wrapper.find('.cook-mode-nav.prev').trigger('click')
    expect(wrapper.find('[role="timer"]').text()).toContain('1:57')
  })

  it('pausing and resetting from the dock is reflected on the inline chip', async () => {
    const wrapper = mountCookMode(recipeWithTimer())
    await wrapper.find('.timer-chip').trigger('click')

    await wrapper.find('.cook-mode-timer-dock-row [aria-label="Mettre en pause"]').trigger('click')
    expect(wrapper.find('[role="timer"] [aria-label="Reprendre"]').exists()).toBe(true)

    await wrapper.find('.cook-mode-timer-dock-row [aria-label="Réinitialiser"]').trigger('click')
    expect(wrapper.find('.cook-mode-timer-dock').exists()).toBe(false)
    expect(wrapper.find('[role="timer"]').exists()).toBe(false)
  })

  it('shows one dock row per simultaneously active timer', async () => {
    const wrapper = mountCookMode(
      baseRecipe({
        steps: [step({ id: 1, order: 0, instruction: 'Cuire ~{2%minutes} puis attendre ~{5%minutes}.' })],
      }),
    )

    const chips = wrapper.findAll('.timer-chip')
    await chips[0].trigger('click')
    await chips[1].trigger('click')

    expect(wrapper.findAll('.cook-mode-timer-dock-row')).toHaveLength(2)
  })

  it('highlights a #cookware mention with an emoji and lists the cookware in the side panel', () => {
    const wrapper = mountCookMode(
      baseRecipe({
        cookware: [{ id: 3, name: 'Poêle', slug: 'poele' }],
        steps: [step({ id: 1, order: 0, instruction: 'Faire fondre le @sel dans la #poêle{}.' })],
      }),
    )

    const mention = wrapper.find('.cook-mode-step-text .cookware-mention')
    expect(mention.text()).toBe('🍳poêle')
    expect(wrapper.find('.cook-mode-step-text').text()).not.toContain('#')
    expect(wrapper.find('.cook-mode-ingredients').text()).toContain('🍳Poêle')
  })

  it("uses the cookware's own emoji, or its photo in the side panel", () => {
    const wrapper = mountCookMode(
      baseRecipe({
        cookware: [
          { id: 3, name: 'Wok', slug: 'wok', emoji: '🥘' },
          { id: 4, name: 'Four', slug: 'four', emoji: '', image: '/media/cookware/four.jpg' },
        ],
        steps: [step({ id: 1, order: 0, instruction: 'Sauter au #wok{}.' })],
      }),
    )

    expect(wrapper.find('.cook-mode-step-text .cookware-mention').text()).toBe('🥘wok')
    // Sans photo, l'emoji ; avec une photo, la photo remplace l'emoji dans la pastille.
    expect(wrapper.find('.cook-mode-step-text .cookware-mention img').exists()).toBe(false)
    expect(wrapper.find('.cook-mode-ingredients img.cookware-image').attributes('src')).toBe('/media/cookware/four.jpg')
  })

  it('opens the cookware photo with its credit from a step mention, and Escape only closes it', async () => {
    const wrapper = mountCookMode(
      baseRecipe({
        cookware: [
          {
            id: 3,
            name: 'Wok',
            slug: 'wok',
            emoji: '🥘',
            image: '/media/cookware/wok.jpg',
            image_license: 'cc_by',
            image_credit_author: 'Marie',
            image_credit_source_url: 'https://commons.wikimedia.org/wiki/File:Wok.jpg',
          },
        ],
        steps: [step({ id: 1, order: 0, instruction: 'Sauter au #wok{}.' })],
      }),
    )

    const pill = wrapper.find('.cook-mode-step-text button.cookware-mention')
    expect(pill.find('img.cookware-pill-image').attributes('src')).toBe('/media/cookware/wok.jpg')
    expect(pill.find('.cookware-emoji').exists()).toBe(false)
    expect(pill.text()).toBe('wok')
    await pill.trigger('click')
    expect(wrapper.find('.base-modal h2').text()).toBe('Wok')
    expect(wrapper.find('.base-modal').text()).toContain('Photo : Marie')
    // Pas de lien vers la liste des recettes : il ferait quitter le mode cuisine.
    expect(wrapper.find('.base-modal').text()).not.toContain('Voir les recettes')

    window.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.base-modal').exists()).toBe(false)
    expect(wrapper.emitted('close')).toBeUndefined()
  })
})

describe('RecipeCookMode alternatives', () => {
  const oat = { id: 20, name: "lait d'avoine" }

  function recipeWithAlternative() {
    const recipe = baseRecipe()
    recipe.ingredients[0].alternatives = [
      { id: 7, ingredient: oat, quantity: 3, unit: 'pinch', tag: 'vegan', note: '', order: 0 },
    ] as never
    return recipe
  }

  function mountWithSwaps(recipe: Recipe) {
    const swaps = useIngredientSwaps()
    const wrapper = mount(RecipeCookMode, { props: { recipe, swaps }, global: { plugins: [i18n] } })
    return { wrapper, swaps }
  }

  it('lets the cook pick an alternative from the ingredients panel, and shows the line as replaced', async () => {
    const { wrapper } = mountWithSwaps(recipeWithAlternative())
    const panel = wrapper.find('.cook-mode-ingredients')
    expect(panel.find('.swap-chip').text()).toBe('1 alternative')
    expect(panel.find('li.ingredient-row').classes()).not.toContain('swapped')

    await panel.findAll('.swap-options button')[1].trigger('click')

    const line = panel.find('li.ingredient-row')
    expect(line.classes()).toContain('swapped')
    expect(line.find('.ingredient-name').text()).toBe("lait d'avoine")
    expect(line.find('.ingredient-qty').text()).toContain('3')
    expect(line.find('.swap-reset').text()).toContain('sel')
  })

  it('shows a choice made on the recipe page, and names the alternative in the step text', async () => {
    const recipe = recipeWithAlternative()
    const { wrapper, swaps } = mountWithSwaps(recipe)
    expect(wrapper.find('.cook-mode-step-text .ingredient-mention').text()).toBe('sel')

    swaps.choose(recipe.ingredients[0], recipe.ingredients[0].alternatives![0])
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.cook-mode-ingredients li.ingredient-row').classes()).toContain('swapped')
    expect(wrapper.find('.cook-mode-step-text .ingredient-mention').text()).toBe("lait d'avoine")
  })

  it('tells in the popover which ingredient the alternative replaces', async () => {
    const recipe = recipeWithAlternative()
    const { wrapper, swaps } = mountWithSwaps(recipe)
    swaps.choose(recipe.ingredients[0], recipe.ingredients[0].alternatives![0])
    await wrapper.vm.$nextTick()

    await wrapper.find('.ingredient-mention').trigger('click')

    expect(wrapper.find('.ingredient-popover').text()).toContain('à la place de sel')
  })

  it('goes back to the original ingredient from the struck-through line', async () => {
    const recipe = recipeWithAlternative()
    const { wrapper, swaps } = mountWithSwaps(recipe)
    swaps.choose(recipe.ingredients[0], recipe.ingredients[0].alternatives![0])
    await wrapper.vm.$nextTick()

    await wrapper.find('.cook-mode-ingredients .swap-reset').trigger('click')

    expect(wrapper.find('.cook-mode-ingredients li.ingredient-row').classes()).not.toContain('swapped')
    expect(wrapper.find('.cook-mode-step-text .ingredient-mention').text()).toBe('sel')
  })

  it('shows no swap control without shared swaps, as before', () => {
    const wrapper = mountCookMode(recipeWithAlternative())

    expect(wrapper.find('.swap-chip').exists()).toBe(false)
  })
})
