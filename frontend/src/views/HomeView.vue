<script setup lang="ts">
import { ChevronDown, Clock, Link2, Pencil, Plus, Users } from '@lucide/vue'
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

// Hero spotlight (the most recent recipe) + a couple of "up next" teasers — see HomeCarousel.vue
// (git history) for the previous all-5 carousel. Only 3 of the latest recipes are reachable
// from the homepage now; the rest remain one click away via "Recipes".
const latestRecipes = ref<Recipe[]>([])
const thematicPages = ref<ThematicPage[]>([])
const seasonalRecipes = ref<Recipe[]>([])

const isLoading = ref(true)
const loadError = ref(false)

const heroRecipe = computed(() => latestRecipes.value[0] ?? null)
const upNextRecipes = computed(() => latestRecipes.value.slice(1))

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
  if (recipesRes.status === 'fulfilled') latestRecipes.value = recipesRes.value.results.slice(0, 3)
  else loadError.value = true
  if (pagesRes.status === 'fulfilled') thematicPages.value = pagesRes.value
  if (seasonRes.status === 'fulfilled') {
    // Skip recipes already shown in the hero/"up next" so the same card never appears twice.
    const shown = new Set(latestRecipes.value.map((recipe) => recipe.id))
    seasonalRecipes.value = seasonRes.value.results.filter((recipe) => !shown.has(recipe.id)).slice(0, 4)
  }
  isLoading.value = false
})

const importUrl = ref('')
const importError = ref('')
const isImporting = ref(false)
const showImportForm = ref(false)

const showCreateMenu = ref(false)
const createMenuEl = ref<HTMLElement | null>(null)

function closeCreateMenu() {
  showCreateMenu.value = false
}

function openImportForm() {
  closeCreateMenu()
  showImportForm.value = true
}

function handleCreateMenuOutsideClick(event: MouseEvent) {
  if (showCreateMenu.value && createMenuEl.value && !createMenuEl.value.contains(event.target as Node)) {
    closeCreateMenu()
  }
}

function handleCreateMenuKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') closeCreateMenu()
}

onMounted(() => {
  document.addEventListener('click', handleCreateMenuOutsideClick)
  document.addEventListener('keydown', handleCreateMenuKeydown)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleCreateMenuOutsideClick)
  document.removeEventListener('keydown', handleCreateMenuKeydown)
})

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
      <div class="row hero-top" :aria-label="$t('home.quickActions')">
        <div v-if="authStore.isAuthenticated" ref="createMenuEl" class="create-menu">
          <button
            class="create-toggle"
            type="button"
            :aria-expanded="showCreateMenu"
            aria-controls="home-create-panel"
            @click="showCreateMenu = !showCreateMenu"
          >
            <Plus :size="16" />{{ $t('recipes.newRecipe') }}<ChevronDown :size="16" />
          </button>
          <div id="home-create-panel" class="create-panel" :class="{ 'is-open': showCreateMenu }">
            <RouterLink :to="{ name: 'recipe-new' }" class="create-link" @click="closeCreateMenu">
              <Pencil :size="16" /><span>{{ $t('recipes.createManually') }}</span>
            </RouterLink>
            <button type="button" class="create-link" @click="openImportForm">
              <Link2 :size="16" /><span>{{ $t('recipes.importFromUrl') }}</span>
            </button>
          </div>
        </div>
        <RouterLink v-else :to="{ name: 'register' }">
          <button class="secondary">{{ $t('nav.register') }}</button>
        </RouterLink>
      </div>

      <div v-if="isLoading" class="hero-skeleton" aria-hidden="true">
        <div class="hero-skeleton-copy" />
        <div class="hero-skeleton-visual" />
      </div>
      <p v-else-if="loadError" class="muted">{{ $t('home.fetchError') }}</p>
      <div v-else-if="heroRecipe" class="hero-spotlight">
        <div class="hero-copy">
          <span class="hero-eyebrow">{{ heroEyebrow }}</span>
          <h2 class="hero-title">{{ heroRecipe.title }}</h2>
          <div class="row hero-meta">
            <span class="hero-diet" :class="`diet-${heroRecipe.diet_type}`">{{ $t(`diet.${heroRecipe.diet_type}`) }}</span>
            <span class="hero-meta-item"><Clock :size="14" />{{ formatDuration(heroRecipe.total_time_minutes) }}</span>
            <span v-if="heroRecipe.servings" class="hero-meta-item">
              <Users :size="14" />{{ heroRecipe.servings }} {{ $t('recipes.servings') }}
            </span>
          </div>
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
            </RouterLink>
          </div>

          <div v-if="upNextRecipes.length" class="hero-upnext">
            <RouterLink
              v-for="recipe in upNextRecipes"
              :key="recipe.id"
              :to="{ name: 'recipe-detail', params: { id: recipe.id } }"
              class="hero-upnext-card"
            >
              <span class="hero-upnext-label">{{ $t('home.upNext') }}</span>
              <span class="hero-upnext-title">{{ recipe.title }}</span>
            </RouterLink>
          </div>
        </div>
      </div>
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

    <HomeWeekStrip v-if="authStore.isAuthenticated" />

    <section v-if="thematicPages.length" class="home-section">
      <h2>{{ $t('home.thematicPages') }}</h2>
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

    <section v-if="seasonalRecipes.length" class="home-section">
      <div class="row season-header">
        <h2>{{ $t('home.inSeason') }}</h2>
        <RouterLink
          :to="{ name: 'recipes', query: { in_season: 'true' } }"
          class="see-all-btn"
          :aria-label="$t('home.seeAll')"
          :title="$t('home.seeAll')"
        >+</RouterLink>
      </div>
      <div class="recipe-grid">
        <RecipeCard v-for="recipe in seasonalRecipes" :key="recipe.id" :recipe="recipe" variant="tile" />
      </div>
    </section>
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

.hero-eyebrow {
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
  border-radius: 999px;
  font-weight: 600;
  font-size: 0.8rem;
  background: var(--color-surface-muted);
  color: var(--color-text);
}

.hero-diet.diet-vegetarian {
  background: color-mix(in srgb, #3fa34d 15%, var(--color-surface));
  color: color-mix(in srgb, #3fa34d 75%, var(--color-text));
}

.hero-diet.diet-vegan {
  background: color-mix(in srgb, #2f8f5b 20%, var(--color-surface));
  color: color-mix(in srgb, #2f8f5b 80%, var(--color-text));
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
  color: #fff;
}

.hero-deck-title-dark {
  color: var(--color-text);
  bottom: 0.9rem;
}

.hero-upnext {
  display: flex;
  gap: 0.75rem;
  margin-top: 1rem;
}

.hero-upnext-card {
  flex: 1;
  padding: 0.65rem 0.85rem;
  border-radius: 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  text-decoration: none;
  color: var(--color-text);
}

.hero-upnext-label {
  display: block;
  font-size: 0.7rem;
  color: var(--color-muted);
  margin-bottom: 0.15rem;
}

.hero-upnext-title {
  display: block;
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1.3;
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
  .hero-spotlight,
  .hero-skeleton {
    flex-direction: column;
    align-items: stretch;
    gap: 1.5rem;
  }

  .hero-copy,
  .hero-skeleton-copy {
    flex-basis: auto;
    min-width: 0;
  }

  .hero-visual,
  .hero-skeleton-visual {
    width: 100%;
    flex-basis: auto;
  }

  .hero-title {
    font-size: 2rem;
  }
}

.create-menu {
  position: relative;
}

.create-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.create-panel {
  display: none;
  position: absolute;
  top: calc(100% + 0.5rem);
  left: 0;
  min-width: 220px;
  background: var(--color-surface);
  border-radius: 16px;
  box-shadow: var(--shadow-card);
  padding: 0.6rem;
  flex-direction: column;
  gap: 0.2rem;
  z-index: 20;
}

.create-panel.is-open {
  display: flex;
}

.create-link {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.6rem;
  margin: 0;
  padding: 0.55rem 0.6rem;
  border-radius: 10px;
  color: var(--color-text);
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  background: none;
  border: none;
  min-height: auto;
}

.create-link:hover {
  background: var(--color-surface-muted);
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
}

.home-section {
  margin-bottom: 2rem;
}

.home-section > h2 {
  margin-bottom: 1rem;
}

.page-header {
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
}

.page-header h2 {
  margin: 0;
}

.season-header {
  justify-content: flex-start;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.season-header h2 {
  margin: 0;
}

.see-all-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-size: 1.4rem;
  line-height: 1;
  text-decoration: none;
}

.see-all-btn:hover {
  background: var(--color-primary);
  color: #fff;
}

.recipe-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
}

/* Thematic pages as a horizontally-scrollable row of round "collection" avatars — a photo
   when the page has one, its emoji icon on a soft accent circle otherwise (never a flat
   saturated color card, which is what an icon-only page used to fall back to). Shape-distinct
   from the "In season" grid below so the two photo sections don't read as the same card
   repeated twice. */
.thematic-row {
  display: flex;
  gap: 1.25rem;
  overflow-x: auto;
  padding-bottom: 0.25rem;
}

.thematic-avatar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  flex-shrink: 0;
  width: 92px;
  text-decoration: none;
  color: var(--color-text);
}

.thematic-avatar-circle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 84px;
  height: 84px;
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
  font-size: 1.8rem;
  line-height: 1;
}

.thematic-avatar-label {
  font-size: 0.8rem;
  font-weight: 600;
  text-align: center;
  line-height: 1.25;
}
</style>
