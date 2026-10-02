<script setup lang="ts">
import { Clock, Compass, Leaf, Link2, Users } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import BaseModal from '../components/BaseModal.vue'
import HomeWeekStrip from '../components/HomeWeekStrip.vue'
import ImageWithCredit from '../components/ImageWithCredit.vue'
import RecipeCard from '../components/RecipeCard.vue'
import { previewImportFromUrl } from '../api/importer'
import { listRecipes } from '../api/recipes'
import { listThematicPages } from '../api/thematicPages'
import { useAuthStore } from '../stores/auth'
import { formatDuration } from '../utils/format'
import { setPendingImportDraft } from '../utils/pendingImportDraft'
import type { Recipe, ThematicPage } from '../types/models'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

// Hero spotlight, cycling through the 5 latest recipes — auto-advances like the old
// HomeCarousel.vue (git history) did, plus dots to jump directly to one.
const latestRecipes = ref<Recipe[]>([])
const thematicPages = ref<ThematicPage[]>([])
const seasonalRecipes = ref<Recipe[]>([])

const isLoading = ref(true)
const loadError = ref(false)

const activeIndex = ref(0)
const heroRecipe = computed(() => latestRecipes.value[activeIndex.value] ?? null)

const prefersReducedMotion =
  typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
let autoAdvanceTimer: ReturnType<typeof setInterval> | undefined

function stopAutoAdvance() {
  clearInterval(autoAdvanceTimer)
  autoAdvanceTimer = undefined
}

function startAutoAdvance() {
  stopAutoAdvance()
  if (prefersReducedMotion || latestRecipes.value.length < 2) return
  autoAdvanceTimer = setInterval(() => {
    activeIndex.value = (activeIndex.value + 1) % latestRecipes.value.length
  }, 6000)
}

function goToSlide(index: number) {
  activeIndex.value = index
  startAutoAdvance()
}

// Swipe support (mobile): the hero becomes a full-bleed photo card below 760px, where
// dots are the only other way to change slides.
const SWIPE_THRESHOLD_PX = 40
const touchStartX = ref<number | null>(null)
const touchStartY = ref<number | null>(null)

function onHeroTouchStart(event: TouchEvent) {
  touchStartX.value = event.touches[0].clientX
  touchStartY.value = event.touches[0].clientY
  stopAutoAdvance()
}

function onHeroTouchEnd(event: TouchEvent) {
  const startX = touchStartX.value
  const startY = touchStartY.value
  touchStartX.value = null
  touchStartY.value = null
  if (startX === null || startY === null) return

  const touch = event.changedTouches[0]
  const deltaX = touch.clientX - startX
  const deltaY = touch.clientY - startY
  const length = latestRecipes.value.length
  if (length > 1 && Math.abs(deltaX) > SWIPE_THRESHOLD_PX && Math.abs(deltaX) > Math.abs(deltaY)) {
    const direction = deltaX < 0 ? 1 : -1
    goToSlide((activeIndex.value + direction + length) % length)
  } else {
    startAutoAdvance()
  }
}

const greetingKey = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'home.greetingMorning'
  if (hour < 18) return 'home.greetingAfternoon'
  return 'home.greetingEvening'
})
const heroEyebrow = computed(() => {
  const greeting = t(greetingKey.value)
  return authStore.user
    ? t('home.heroEyebrowAuth', { greeting, name: authStore.user.username })
    : t('home.heroEyebrowGuest', { greeting })
})

onMounted(async () => {
  const [recipesRes, pagesRes, seasonRes] = await Promise.allSettled([
    listRecipes(),
    listThematicPages(),
    listRecipes({ in_season: true }),
  ])
  if (recipesRes.status === 'fulfilled') {
    latestRecipes.value = recipesRes.value.results.slice(0, 5)
    startAutoAdvance()
  } else {
    loadError.value = true
  }
  if (pagesRes.status === 'fulfilled') thematicPages.value = pagesRes.value
  if (seasonRes.status === 'fulfilled') {
    // Skip recipes already reachable from the hero so the same card never appears twice.
    const shown = new Set(latestRecipes.value.map((recipe) => recipe.id))
    seasonalRecipes.value = seasonRes.value.results.filter((recipe) => !shown.has(recipe.id)).slice(0, 4)
  }
  isLoading.value = false
})

onBeforeUnmount(stopAutoAdvance)

const importUrl = ref('')
const importError = ref('')
const isImporting = ref(false)
const showImportForm = ref(false)

function openImportForm() {
  showImportForm.value = true
}

async function handleImport() {
  importError.value = ''
  isImporting.value = true
  try {
    const preview = await previewImportFromUrl(importUrl.value)
    setPendingImportDraft({
      title: preview.title,
      servings: preview.servings,
      cook_time_minutes: preview.cook_time_minutes,
      image_url: preview.image_url,
      source_url: preview.source_url,
      steps: preview.steps,
      ingredients: preview.ingredients.map((item) => ({
        ingredient: item.ingredient,
        quantity: item.quantity,
        unit: item.unit,
        raw_line: item.raw_line,
      })),
    })
    router.push({ name: 'recipe-new' })
  } catch {
    importError.value = t('recipes.importError')
  } finally {
    isImporting.value = false
  }
}
</script>

<template>
  <div>
    <h1 class="sr-only">{{ $t('home.title') }}</h1>

    <div class="hero-card">
      <div v-if="!authStore.isAuthenticated" class="row hero-top" :aria-label="$t('home.quickActions')">
        <RouterLink :to="{ name: 'register' }">
          <button class="secondary">{{ $t('nav.register') }}</button>
        </RouterLink>
      </div>

      <div v-if="isLoading" class="hero-skeleton" aria-hidden="true">
        <div class="hero-skeleton-copy" />
        <div class="hero-skeleton-visual" />
      </div>
      <p v-else-if="loadError" class="muted">{{ $t('home.fetchError') }}</p>
      <template v-else-if="heroRecipe">
        <span class="hero-eyebrow">{{ heroEyebrow }}</span>
        <div
          class="hero-spotlight"
          @mouseenter="stopAutoAdvance"
          @mouseleave="startAutoAdvance"
          @touchstart.passive="onHeroTouchStart"
          @touchend.passive="onHeroTouchEnd"
        >
          <div class="hero-copy">
            <Transition name="hero-fade" mode="out-in">
              <div :key="heroRecipe.id" class="hero-copy-face">
                <h2 class="hero-title">{{ heroRecipe.title }}</h2>
                <div class="row hero-meta">
                  <span class="hero-diet" :class="`diet-${heroRecipe.diet_type}`">{{ $t(`diet.${heroRecipe.diet_type}`) }}</span>
                  <span class="hero-meta-item"><Clock :size="14" />{{ formatDuration(heroRecipe.total_time_minutes) }}</span>
                  <span v-if="heroRecipe.servings" class="hero-meta-item">
                    <Users :size="14" />{{ heroRecipe.servings }} {{ $t('recipes.servings') }}
                  </span>
                </div>
              </div>
            </Transition>
            <div class="row hero-ctas">
              <RouterLink :to="{ name: 'recipe-detail', params: { id: heroRecipe.id } }">
                <button>{{ $t('home.viewRecipe') }}</button>
              </RouterLink>
              <RouterLink :to="{ name: 'planning' }">
                <button class="secondary">{{ $t('home.planForLater') }}</button>
              </RouterLink>
            </div>
          </div>

          <div class="hero-visual">
            <div class="hero-deck">
              <div class="hero-deck-back hero-deck-back-1" aria-hidden="true" />
              <div class="hero-deck-back hero-deck-back-2" aria-hidden="true" />
              <RouterLink :to="{ name: 'recipe-detail', params: { id: heroRecipe.id } }" class="hero-deck-front">
                <Transition name="hero-deck-fade">
                  <div :key="heroRecipe.id" class="hero-deck-face">
                    <template v-if="heroRecipe.image || heroRecipe.image_url">
                      <ImageWithCredit
                        class="hero-deck-image"
                        :image-url="heroRecipe.image || heroRecipe.image_url"
                        :source-url="heroRecipe.image ? null : heroRecipe.source_url"
                        :license="heroRecipe.image_license"
                        :credit-author="heroRecipe.image_credit_author"
                        :credit-source-url="heroRecipe.image_credit_source_url"
                        :credit-license-url="heroRecipe.image_credit_license_url"
                        :credit-note="heroRecipe.image_credit_note"
                        overlay
                        overlay-align="right"
                      />
                      <div class="hero-deck-scrim" />
                      <span class="hero-deck-title hero-deck-title-light">{{ heroRecipe.title }}</span>
                    </template>
                    <template v-else>
                      <div class="hero-deck-placeholder" aria-hidden="true">🍲</div>
                      <span class="hero-deck-title hero-deck-title-dark">{{ heroRecipe.title }}</span>
                    </template>
                  </div>
                </Transition>
              </RouterLink>
            </div>
          </div>
        </div>

        <div v-if="latestRecipes.length > 1" class="hero-dots" role="tablist">
          <button
            v-for="(recipe, index) in latestRecipes"
            :key="recipe.id"
            type="button"
            role="tab"
            class="hero-dot"
            :class="{ active: index === activeIndex }"
            :aria-selected="index === activeIndex"
            :aria-label="recipe.title"
            @click="goToSlide(index)"
          />
        </div>
      </template>
      <p v-else class="muted">{{ $t('home.noRecipes') }}</p>
    </div>

    <BaseModal v-if="showImportForm" :title="$t('recipes.importFromUrl')" @close="showImportForm = false">
      <form class="row" style="align-items: flex-end" @submit.prevent="handleImport">
        <div class="field" style="flex: 1; min-width: 220px">
          <label for="home-import-url">{{ $t('recipes.importFromUrl') }}</label>
          <input id="home-import-url" v-model="importUrl" type="url" placeholder="https://..." required autofocus />
        </div>
        <button type="submit" :disabled="isImporting">
          <Link2 :size="16" />{{ isImporting ? $t('common.loading') : $t('recipes.importButton') }}
        </button>
      </form>
      <p v-if="importError" class="muted">{{ importError }}</p>
    </BaseModal>

    <HomeWeekStrip v-if="authStore.isAuthenticated" @open-import="openImportForm" />

    <div v-if="thematicPages.length || seasonalRecipes.length" class="home-panel-row">
      <section v-if="thematicPages.length" class="card home-panel">
        <div class="row home-panel-header">
          <h2><Compass :size="20" class="home-panel-icon" aria-hidden="true" />{{ $t('home.thematicPages') }}</h2>
        </div>
        <div class="thematic-row">
          <RouterLink
            v-for="page in thematicPages"
            :key="page.id"
            class="thematic-avatar"
            :to="{ name: 'recipes', query: page.filters }"
          >
            <span class="thematic-avatar-circle">
              <img v-if="page.image" :src="page.image" alt="" />
              <span v-else-if="page.icon" class="thematic-avatar-icon">{{ page.icon }}</span>
            </span>
            <span class="thematic-avatar-label">{{ page.title }}</span>
          </RouterLink>
        </div>
      </section>

      <section v-if="seasonalRecipes.length" class="card home-panel">
        <div class="row home-panel-header">
          <h2><Leaf :size="20" class="home-panel-icon" aria-hidden="true" />{{ $t('home.inSeason') }}</h2>
          <RouterLink
            :to="{ name: 'recipes', query: { in_season: 'true' } }"
            class="home-panel-see-all"
            :aria-label="$t('home.seeAll')"
            :title="$t('home.seeAll')"
          >+</RouterLink>
        </div>
        <div class="recipe-grid">
          <RecipeCard v-for="recipe in seasonalRecipes" :key="recipe.id" :recipe="recipe" variant="tile" />
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.hero-card {
  padding: 1.5rem 1.5rem 2.75rem;
  margin-bottom: 1.5rem;
  border-radius: 24px;
  background: linear-gradient(180deg, var(--color-surface) 0%, var(--color-surface-muted) 100%);
}

@media (max-width: 600px) {
  .hero-card {
    padding: 1.25rem 1.25rem 2.25rem;
  }
}

.hero-top {
  margin-bottom: 1.25rem;
}

.hero-spotlight {
  display: flex;
  align-items: center;
  gap: 3rem;
}

.hero-copy {
  flex: 1 1 360px;
  min-width: 280px;
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.hero-copy-face {
  display: flex;
  flex-direction: column;
  gap: 1.1rem;
}

.hero-fade-enter-active,
.hero-fade-leave-active {
  transition: opacity 0.2s ease;
}

.hero-fade-enter-from,
.hero-fade-leave-to {
  opacity: 0;
}

.hero-deck-fade-enter-active,
.hero-deck-fade-leave-active {
  transition: opacity 0.5s ease;
}

.hero-deck-fade-enter-from,
.hero-deck-fade-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .hero-fade-enter-active,
  .hero-fade-leave-active,
  .hero-deck-fade-enter-active,
  .hero-deck-fade-leave-active {
    transition: none;
  }
}

.hero-eyebrow {
  display: block;
  margin-bottom: 1.1rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--color-muted);
}

.hero-title {
  margin: 0;
  font-size: 2.6rem;
  line-height: 1.08;
  font-weight: 800;
  letter-spacing: -0.02em;
}

.hero-meta {
  align-items: center;
  gap: 1rem;
}

.hero-diet {
  padding: 0.1rem 0.6rem;
  border-radius: var(--radius-pill);
  font-weight: 600;
  font-size: 0.8rem;
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.hero-diet.diet-vegetarian {
  background: color-mix(in srgb, var(--color-vegetarian) 15%, var(--color-surface));
  color: color-mix(in srgb, var(--color-vegetarian) 75%, var(--color-text));
}

.hero-diet.diet-vegan {
  background: color-mix(in srgb, var(--color-vegan) 20%, var(--color-surface));
  color: color-mix(in srgb, var(--color-vegan) 80%, var(--color-text));
}

.hero-meta-item {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.9rem;
  color: var(--color-muted);
}

.hero-ctas {
  margin-top: 0.25rem;
}

.hero-visual {
  flex: 0 0 340px;
  width: 340px;
}

.hero-deck {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
}

.hero-deck-back {
  position: absolute;
  inset: 0;
  border-radius: 24px;
}

.hero-deck-back-1 {
  transform: rotate(8deg) translate(14px, 8px);
  background: linear-gradient(135deg, var(--color-surface-muted), var(--color-border));
}

.hero-deck-back-2 {
  transform: rotate(-6deg) translate(-10px, 6px);
  background: linear-gradient(135deg, var(--color-primary-soft), var(--color-primary-soft-hover));
}

.hero-deck-front {
  position: absolute;
  inset: 0;
  display: block;
  overflow: hidden;
  border-radius: 24px;
  text-decoration: none;
  box-shadow: 0 20px 40px rgba(36, 31, 29, 0.18);
}

.hero-deck-face {
  position: absolute;
  inset: 0;
}

.hero-deck-image {
  position: absolute;
  inset: 0;
}

.hero-deck-image :deep(.image-with-credit-frame) {
  height: 100%;
}

.hero-deck-image :deep(img) {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hero-deck-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 3rem;
  background: var(--color-primary-soft);
}

.hero-deck-scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0) 55%);
}

.hero-deck-title {
  position: absolute;
  left: 1.25rem;
  right: 1.25rem;
  bottom: 1.1rem;
  font-weight: 700;
  font-size: 1.15rem;
  line-height: 1.25;
}

.hero-deck-title-light {
  color: var(--color-on-primary);
}

.hero-deck-title-dark {
  color: var(--color-text);
  bottom: 0.9rem;
}

.hero-dots {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 1rem;
}

.hero-dot {
  position: relative;
  width: 8px;
  height: 8px;
  min-height: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: var(--color-border);
  transition: background 0.2s ease;
}

/* Wider hit target without growing the visible dot. */
.hero-dot::before {
  content: '';
  position: absolute;
  inset: -10px -4px;
}

.hero-dot:hover {
  background: var(--color-muted);
}

.hero-dot:active {
  transform: none;
}

.hero-dot.active {
  background: var(--color-muted);
}

.hero-skeleton {
  display: flex;
  align-items: center;
  gap: 3rem;
}

.hero-skeleton-copy {
  flex: 1 1 360px;
  height: 220px;
  border-radius: 16px;
  background: var(--color-surface-muted);
}

.hero-skeleton-visual {
  flex: 0 0 340px;
  width: 340px;
  aspect-ratio: 1;
  border-radius: 24px;
  background: var(--color-surface-muted);
}

@media (max-width: 760px) {
  /* Below desktop width, the hero becomes one photo card: the deck fills it edge to edge and
     the copy (eyebrow, title, meta, CTAs) overlays its bottom on the existing dark scrim,
     instead of sitting in its own text block above a separate, smaller photo. */
  .hero-spotlight {
    position: relative;
    display: block;
    min-height: 26rem;
    border-radius: 24px;
    overflow: hidden;
  }

  .hero-skeleton {
    flex-direction: column;
    align-items: stretch;
    gap: 1.5rem;
  }

  .hero-skeleton-copy {
    flex-basis: auto;
  }

  .hero-skeleton-visual {
    width: 100%;
    flex-basis: auto;
  }

  .hero-visual {
    position: absolute;
    inset: 0;
    z-index: 0;
    width: 100%;
  }

  .hero-deck {
    width: 100%;
    height: 100%;
  }

  .hero-deck-back {
    display: none;
  }

  .hero-deck-front {
    border-radius: 0;
    box-shadow: none;
  }

  /* The deck's own caption would otherwise duplicate the title .hero-copy now overlays. */
  .hero-deck-title {
    display: none;
  }

  .hero-copy {
    position: absolute;
    inset: 0;
    z-index: 1;
    justify-content: flex-end;
    padding: 1.5rem;
    gap: 0.75rem;
  }

  .hero-meta-item {
    color: rgba(255, 255, 255, 0.85);
  }

  .hero-title {
    font-size: 2rem;
    color: var(--color-on-primary);
  }
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

/* Explore and In season sit side by side as matching cards, echoing HomeWeekStrip's
   ".week-strip" card above them rather than the plain headed sections this replaced. */
.home-panel-row {
  display: flex;
  align-items: stretch;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.home-panel {
  flex: 1 1 0;
  min-width: 0;
}

@media (max-width: 760px) {
  .home-panel-row {
    flex-direction: column;
  }
}

.home-panel-header {
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.home-panel-header h2 {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0;
}

.home-panel-icon {
  color: var(--color-primary);
}

.home-panel-see-all {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 1.4rem;
  line-height: 1;
  text-decoration: none;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.home-panel-see-all:hover {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.recipe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
}

/* Thematic pages as a wrapping row of round "collection" avatars — a photo when the page has
   one, its emoji icon on a soft accent circle otherwise (never a flat saturated color card,
   which is what an icon-only page used to fall back to). Shape-distinct from the "In season"
   grid next to it so the two photo sections don't read as the same card repeated twice. Sized to
   fill the panel now that Explore and In season sit in matching half-width cards, rather than
   the smaller scroll-strip size that fit the old full-width row. */
.thematic-row {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
}

.thematic-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  width: 110px;
  text-decoration: none;
  color: var(--color-text);
}

.thematic-avatar-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  border-radius: 999px;
  overflow: hidden;
  background: var(--color-primary-soft);
  border: 3px solid var(--color-surface);
  box-shadow: var(--shadow-card);
  transition: transform 0.15s ease;
}

.thematic-avatar:hover .thematic-avatar-circle {
  transform: translateY(-3px);
}

.thematic-avatar-circle img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thematic-avatar-icon {
  font-size: 2.2rem;
  line-height: 1;
}

.thematic-avatar-label {
  font-size: 0.85rem;
  font-weight: 600;
  text-align: center;
  line-height: 1.25;
}
</style>
