<script setup lang="ts">
import { Link2, Plus, X } from '@lucide/vue'
import { nextTick, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
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
const isLoading = ref(true)

onMounted(async () => {
  try {
    const [recipesData, pagesData] = await Promise.all([listRecipes(), listThematicPages()])
    latestRecipes.value = recipesData.results.slice(0, 6)
    thematicPages.value = pagesData
  } finally {
    isLoading.value = false
  }
})

const importUrl = ref('')
const importError = ref('')
const isImporting = ref(false)
const showImportForm = ref(false)
const importUrlInput = ref<HTMLInputElement | null>(null)

function toggleImportForm() {
  showImportForm.value = !showImportForm.value
  if (showImportForm.value) {
    nextTick(() => importUrlInput.value?.focus())
  }
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
    <section class="home-columns">
      <div class="card hero">
        <div class="hero-heading">
          <img src="/pwa-512.png" alt="Cocotte" class="hero-logo" />
          <h1>{{ $t('home.title') }}</h1>
        </div>
        <p class="muted">{{ $t('home.tagline') }}</p>
        <div class="row">
          <RouterLink :to="{ name: 'recipes' }"><button>{{ $t('home.browseRecipes') }}</button></RouterLink>
          <RouterLink v-if="authStore.isAuthenticated" :to="{ name: 'recipe-new' }">
            <button class="secondary"><Plus :size="16" />{{ $t('recipes.newRecipe') }}</button>
          </RouterLink>
          <button
            v-if="authStore.isAuthenticated"
            class="secondary"
            type="button"
            :aria-expanded="showImportForm"
            aria-controls="home-import-form"
            @click="toggleImportForm"
          >
            <component :is="showImportForm ? X : Link2" :size="16" />{{ $t('recipes.importButton') }}
          </button>
        </div>

        <div v-if="authStore.isAuthenticated && showImportForm" id="home-import-form" class="card" style="margin-top: 1rem">
          <form class="row" style="align-items: flex-end" @submit.prevent="handleImport">
            <div class="field" style="flex: 1; min-width: 220px">
              <label for="home-import-url">{{ $t('recipes.importFromUrl') }}</label>
              <input
                id="home-import-url"
                ref="importUrlInput"
                v-model="importUrl"
                type="url"
                placeholder="https://..."
                required
              />
            </div>
            <button type="submit" :disabled="isImporting">
              <Link2 :size="16" />{{ isImporting ? $t('common.loading') : $t('recipes.importButton') }}
            </button>
          </form>
          <p v-if="importError" class="muted">{{ importError }}</p>
        </div>
      </div>

      <div class="card latest-recipes">
        <div class="row page-header">
          <h2>{{ $t('home.latestRecipes') }}</h2>
          <RouterLink :to="{ name: 'recipes' }">{{ $t('home.seeAll') }}</RouterLink>
        </div>
        <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>
        <p v-else-if="!latestRecipes.length" class="muted">{{ $t('home.noRecipes') }}</p>
        <RecipeCard v-for="recipe in latestRecipes" :key="recipe.id" :recipe="recipe" />
      </div>
    </section>

    <section v-if="thematicPages.length" class="home-section">
      <h1 class="thematic-title">{{ $t('home.thematicPages') }}</h1>
      <div class="thematic-grid">
        <RouterLink
          v-for="page in thematicPages"
          :key="page.id"
          class="thematic-card card"
          :to="{ name: 'recipes', query: page.filters }"
        >
          <span v-if="page.icon" class="thematic-icon-badge">{{ page.icon }}</span>
          <h2>{{ page.title }}</h2>
          <p v-if="page.description" class="muted">{{ page.description }}</p>
        </RouterLink>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-columns {
  display: grid;
  grid-template-columns: minmax(280px, 1fr) minmax(280px, 1.4fr);
  align-items: stretch;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.hero,
.latest-recipes {
  display: flex;
  flex-direction: column;
  margin-bottom: 0;
}

.hero-heading {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.hero-logo {
  width: 48px;
  height: 48px;
  display: block;
  flex-shrink: 0;
}

.hero h1 {
  margin: 0;
}

.latest-recipes .page-header {
  margin-bottom: 1.25rem;
}

.home-section {
  margin-bottom: 2rem;
}

@media (max-width: 900px) {
  .home-columns {
    grid-template-columns: 1fr;
  }
}

.page-header {
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
}

.thematic-title {
  text-align: center;
  font-size: 2rem;
  margin-bottom: 1.5rem;
}

.thematic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 240px));
  justify-content: center;
  gap: 1rem;
}

.thematic-card {
  position: relative;
  overflow: hidden;
  text-decoration: none;
  color: inherit;
  display: block;
  border: 1px solid transparent;
  transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.thematic-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--color-primary);
}

.thematic-card:hover {
  transform: translateY(-3px);
  border-color: var(--color-primary-soft);
  box-shadow: 0 4px 8px rgba(36, 31, 29, 0.06), 0 12px 24px rgba(36, 31, 29, 0.08);
}

.thematic-icon-badge {
  width: 3rem;
  height: 3rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: var(--color-primary-soft);
  font-size: 1.5rem;
  margin-bottom: 0.6rem;
}

.thematic-card h2 {
  margin: 0 0 0.25rem;
}

.thematic-card p {
  margin: 0;
}
</style>
