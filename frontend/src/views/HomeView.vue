<script setup lang="ts">
import { ChevronDown, Link2, Pencil, Plus } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import BaseModal from '../components/BaseModal.vue'
import HomeCarousel from '../components/HomeCarousel.vue'
import HomeWeekStrip from '../components/HomeWeekStrip.vue'
import RecipeCard from '../components/RecipeCard.vue'
import { previewImportFromUrl } from '../api/importer'
import { listRecipes } from '../api/recipes'
import { listThematicPages } from '../api/thematicPages'
import { useAuthStore } from '../stores/auth'
import { setPendingImportDraft } from '../utils/pendingImportDraft'
import type { Recipe, ThematicPage } from '../types/models'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const latestRecipes = ref<Recipe[]>([])
const thematicPages = ref<ThematicPage[]>([])
const seasonalRecipes = ref<Recipe[]>([])

const isLoading = ref(true)
const loadError = ref(false)

onMounted(async () => {
  const [recipesRes, pagesRes, seasonRes] = await Promise.allSettled([
    listRecipes(),
    listThematicPages(),
    listRecipes({ in_season: true }),
  ])
  if (recipesRes.status === 'fulfilled') latestRecipes.value = recipesRes.value.results.slice(0, 5)
  else loadError.value = true
  if (pagesRes.status === 'fulfilled') thematicPages.value = pagesRes.value
  if (seasonRes.status === 'fulfilled') {
    // Skip recipes already shown in "latest" so the same card never appears twice.
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

    <div class="row quick-actions" :aria-label="$t('home.quickActions')">
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

    <div v-if="isLoading" class="carousel-skeleton" aria-hidden="true" />
    <p v-else-if="loadError" class="muted">{{ $t('home.fetchError') }}</p>
    <HomeCarousel v-else-if="latestRecipes.length" :recipes="latestRecipes" />
    <p v-else class="muted">{{ $t('home.noRecipes') }}</p>

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
      <div class="thematic-grid">
        <RouterLink
          v-for="page in thematicPages"
          :key="page.id"
          class="thematic-card card"
          :to="{ name: 'recipes', query: page.filters }"
        >
          <img v-if="page.image" :src="page.image" class="thematic-image" alt="" />
          <span v-else-if="page.icon" class="thematic-icon-badge">{{ page.icon }}</span>
          <div class="thematic-scrim" />
          <div class="thematic-body">
            <h3>{{ page.title }}</h3>
            <p v-if="page.description" class="thematic-description">{{ page.description }}</p>
          </div>
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
.quick-actions {
  margin-bottom: 1rem;
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

.carousel-skeleton {
  aspect-ratio: 16 / 7;
  min-height: 220px;
  margin-bottom: 1.5rem;
  border-radius: 20px;
  background: var(--color-surface-muted);
}

.skeleton-tile {
  flex: 0 0 min(260px, 75%);
  scroll-snap-align: start;
}

.carousel-btn {
  position: absolute;
  top: 40%;
  transform: translateY(-50%);
  z-index: 1;
  border-radius: 999px;
  box-shadow: 0 2px 8px rgba(36, 31, 29, 0.15);
}

.carousel-btn.prev {
  left: -0.75rem;
}

.carousel-btn.next {
  right: -0.75rem;
}

@media (max-width: 600px) {
  .carousel-btn {
    display: none;
  }
}

.skeleton-tile {
  aspect-ratio: 1 / 1;
  border-radius: 14px;
  background: var(--color-surface-muted);
}

.thematic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 1rem;
}

.thematic-card {
  position: relative;
  display: block;
  aspect-ratio: 1;
  overflow: hidden;
  padding: 0;
  margin-bottom: 0;
  border: 0;
  border-radius: 16px;
  text-decoration: none;
  color: #fff;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.thematic-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 8px rgba(36, 31, 29, 0.06), 0 12px 24px rgba(36, 31, 29, 0.08);
}

.thematic-image {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thematic-icon-badge {
  position: absolute;
  top: 0.85rem;
  left: 0.85rem;
  font-size: 2rem;
  line-height: 1;
}

.thematic-scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0) 60%);
}

.thematic-body {
  position: absolute;
  left: 0.85rem;
  right: 0.85rem;
  bottom: 0.75rem;
}

.thematic-card h3 {
  margin: 0 0 0.15rem;
  font-size: 1rem;
  line-height: 1.25;
  color: inherit;
}

.thematic-description {
  margin: 0;
  font-size: 0.8rem;
  opacity: 0.9;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>
