<script setup lang="ts">
import { Download, EllipsisVertical, GitFork, Link2, Pencil, Trash2, Utensils } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { useClickOutside } from '../../composables/useClickOutside'
import AddToPlanForm from '../../components/planning/AddToPlanForm.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import PersonalTagsEditor from '../../components/recipes/PersonalTagsEditor.vue'
import RecipeComments from '../../components/recipes/RecipeComments.vue'
import RecipeRestrictedNotice from '../../components/recipes/RecipeRestrictedNotice.vue'
import RecipeSummary from '../../components/recipes/RecipeSummary.vue'
import { deleteRecipe, forkRecipe, getRecipe } from '../../api/recipes'
import type { RecipeRatingResult } from '../../api/recipes'
import { usePageTitle } from '../../composables/usePageTitle'
import { useAuthStore } from '../../stores/auth'
import { getErrorStatus } from '../../utils/apiError'
import { isImportedRecipe } from '../../utils/recipeOrigin'
import { recipeImageUrl } from '../../utils/recipeImageUrl'
import type { Recipe } from '../../types/models'

const props = defineProps<{
  id: string | number
}>()
const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const recipe = ref<Recipe | null>(null)
// Titre de l'onglet : celui de la recette une fois chargée.
usePageTitle(() => recipe.value?.title)
const deleteError = ref('')

const showForkForm = ref(false)
const forkLabel = ref('')
const forkError = ref('')
const forking = ref(false)

const showActionsMenu = ref(false)
const actionsEl = ref<HTMLElement | null>(null)

const isOwner = computed(
  () => Boolean(authStore.user) && recipe.value?.author_id === authStore.user?.id,
)
// Le staff peut modifier/supprimer n'importe quelle recette (l'API l'autorise déjà).
const canManage = computed(() => isOwner.value || Boolean(authStore.user?.is_staff))
const isImported = computed(() => Boolean(recipe.value) && isImportedRecipe(recipe.value!))
const authorLine = computed(() => {
  if (!recipe.value?.author) return null
  if (isImported.value) return t('recipes.importedBy', { author: recipe.value.author })
  return isOwner.value ? null : t('recipes.byAuthor', { author: recipe.value.author })
})
const canModerateComments = computed(() => isOwner.value || Boolean(authStore.user?.is_staff))
const canFork = computed(
  () => Boolean(recipe.value) && (!recipe.value?.content_restricted || canManage.value),
)
const hasActions = computed(() => canManage.value || canFork.value)

function handleRated(result: RecipeRatingResult) {
  if (!recipe.value) return
  recipe.value.average_rating = result.average_rating
  recipe.value.ratings_count = result.ratings_count
  recipe.value.my_rating = result.my_rating
}

function closeActionsMenu() {
  showActionsMenu.value = false
}

useClickOutside(actionsEl, closeActionsMenu)

async function load() {
  const loaded = await getRecipe(props.id)
  // Une réponse mise en cache hors ligne avant l'ajout des étiquettes personnelles n'a pas ce champ.
  loaded.my_tags ??= []
  recipe.value = loaded
}

onMounted(load)

async function handleDelete() {
  closeActionsMenu()
  if (!confirm(t('recipes.deleteConfirm'))) return
  deleteError.value = ''
  try {
    await deleteRecipe(props.id)
    router.push({ name: 'recipes' })
  } catch {
    deleteError.value = t('recipes.deleteError')
  }
}

function cancelFork() {
  showForkForm.value = false
  forkLabel.value = ''
  forkError.value = ''
}

async function handleFork() {
  if (!recipe.value || !forkLabel.value.trim()) return
  forkError.value = ''
  forking.value = true
  try {
    const created = await forkRecipe(recipe.value.id, forkLabel.value.trim())
    router.push({ name: 'recipe-edit', params: { id: created.id } })
  } catch (err) {
    const status = getErrorStatus(err)
    forkError.value = status === 403 ? t('recipes.restrictedForkError') : t('recipes.forkError')
  } finally {
    forking.value = false
  }
}
</script>

<template>
  <div v-if="recipe">
    <div class="row page-header">
      <div class="title-block">
        <PageHeader :icon="Utensils">{{ recipe.title }}</PageHeader>
        <p v-if="authorLine" class="byline muted" data-testid="recipe-byline">
          <Download v-if="isImported" :size="14" /><span>{{ authorLine }}</span>
        </p>
      </div>
      <div v-if="authStore.isAuthenticated && hasActions" ref="actionsEl" class="actions-menu">
        <button
          class="actions-toggle secondary"
          type="button"
          :aria-expanded="showActionsMenu"
          aria-controls="recipe-actions-panel"
          :aria-label="t('recipes.actions')"
          @click="showActionsMenu = !showActionsMenu"
        >
          <EllipsisVertical :size="18" />
        </button>

        <div id="recipe-actions-panel" class="actions-panel" :class="{ 'is-open': showActionsMenu }">
          <template v-if="canManage">
            <RouterLink
              :to="{ name: 'recipe-edit', params: { id: recipe.id } }"
              class="actions-link"
              @click="closeActionsMenu"
            >
              <Pencil :size="16" /><span>{{ $t('common.edit') }}</span>
            </RouterLink>
            <button class="actions-link actions-link-danger" @click="handleDelete">
              <Trash2 :size="16" /><span>{{ $t('common.delete') }}</span>
            </button>
          </template>
          <button
            v-if="!showForkForm && canFork"
            class="actions-link"
            @click="showForkForm = true; closeActionsMenu()"
          >
            <GitFork :size="16" /><span>{{ $t('recipes.createVariant') }}</span>
          </button>
        </div>
      </div>
    </div>
    <a
      v-if="recipe.source_url && !recipe.content_restricted && !recipeImageUrl(recipe)"
      :href="recipe.source_url"
      target="_blank"
      rel="noopener noreferrer"
      class="source-link"
    >
      <Link2 :size="18" /><span>{{ $t('recipes.source') }}</span>
    </a>
    <p v-if="deleteError" class="error">{{ deleteError }}</p>

    <div v-if="showForkForm" class="row fork-form">
      <input
        v-model="forkLabel"
        type="text"
        :placeholder="$t('recipes.versionLabelPlaceholder')"
        @keyup.enter="handleFork"
      />
      <button :disabled="forking || !forkLabel.trim()" @click="handleFork">
        {{ $t('recipes.confirmFork') }}
      </button>
      <button class="secondary" @click="cancelFork">
        {{ $t('common.cancel') }}
      </button>
    </div>
    <p v-if="forkError" class="error">{{ forkError }}</p>

    <RecipeSummary v-if="!recipe.content_restricted" :recipe="recipe" @rated="handleRated" />
    <RecipeRestrictedNotice v-else :recipe="recipe" @rated="handleRated" />
    <PersonalTagsEditor
      v-if="authStore.isAuthenticated"
      :key="recipe.id"
      v-model="recipe.my_tags"
      :recipe-id="recipe.id"
    />
    <AddToPlanForm v-if="authStore.isAuthenticated" :key="recipe.id" :recipe="recipe" />

    <div v-if="recipe.versions.length" class="versions-section">
      <h2>{{ $t('recipes.otherVersions') }}</h2>
      <ul>
        <li v-for="version in recipe.versions" :key="version.id">
          <RouterLink :to="{ name: 'recipe-detail', params: { id: version.id } }">
            {{ version.version_label || $t('recipes.originalVersion') }}
          </RouterLink>
          — {{ version.author }}
        </li>
      </ul>
    </div>

    <RecipeComments :key="recipe.id" :recipe-id="recipe.id" :can-moderate="canModerateComments" />
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: nowrap;
}

.title-block {
  flex: 1;
  min-width: 0;

  h1{
    margin-top: 0;
  }
}

.byline {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin: -0.5rem 0 1rem;
  font-size: 0.9rem;
}

.byline span::first-letter {
  text-transform: uppercase;
}


.source-link {
  display: flex;
  width: fit-content;
  align-items: center;
  gap: 0.5rem;
  margin: 0 auto 1.5rem;
  padding: 0.75rem 1.75rem;
  border-radius: 0;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
  font-size: 1rem;
  font-weight: 700;
  text-decoration: none;
}

.source-link:hover {
  background: var(--color-primary);
  color: var(--color-on-primary);
}

.actions-menu {
  position: relative;
  flex-shrink: 0;
}

.actions-toggle {
  width: 2.75rem;
  height: 2.75rem;
  min-height: auto;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.actions-panel {
  display: none;
  position: absolute;
  top: calc(100% + 0.5rem);
  right: 0;
  min-width: 200px;
  background: var(--color-surface);
  border-radius: 0;
  box-shadow: var(--shadow-card);
  padding: 0.6rem;
  flex-direction: column;
  gap: 0.2rem;
  z-index: 20;
}

.actions-panel.is-open {
  display: flex;
}

.actions-link {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 0.6rem;
  margin: 0;
  padding: 0.55rem 0.6rem;
  border-radius: 0;
  color: var(--color-text);
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  background: none;
  border: none;
  min-height: auto;
  width: 100%;
  text-align: left;
  cursor: pointer;
}

.actions-link:hover {
  background: var(--color-surface-muted);
}

.actions-link-danger {
  color: var(--color-danger);
}

.fork-form {
  align-items: center;
}

.versions-section {
  margin-top: 2rem;
}
</style>
