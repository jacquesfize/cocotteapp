<script setup lang="ts">
import { GitFork, Pencil, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AddToPlanForm from '../components/AddToPlanForm.vue'
import RecipeSummary from '../components/RecipeSummary.vue'
import { deleteRecipe, forkRecipe, getRecipe } from '../api/recipes'
import { useAuthStore } from '../stores/auth'
import type { Recipe } from '../types/models'

const props = defineProps<{
  id: string | number
}>()
const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const recipe = ref<Recipe | null>(null)
const deleteError = ref('')

const showForkForm = ref(false)
const forkLabel = ref('')
const forkError = ref('')
const forking = ref(false)

const isOwner = computed(
  () => Boolean(authStore.user) && recipe.value?.author_id === authStore.user?.id,
)

async function load() {
  recipe.value = await getRecipe(props.id)
}

onMounted(load)

async function handleDelete() {
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
  } catch {
    forkError.value = t('recipes.forkError')
  } finally {
    forking.value = false
  }
}
</script>

<template>
  <div v-if="recipe">
    <div class="row page-header">
      <h1>{{ recipe.title }}</h1>
      <div class="row">
        <template v-if="isOwner">
          <RouterLink :to="{ name: 'recipe-edit', params: { id: recipe.id } }">
            <button class="secondary"><Pencil :size="16" />{{ $t('common.edit') }}</button>
          </RouterLink>
          <button class="danger" @click="handleDelete"><Trash2 :size="16" />{{ $t('common.delete') }}</button>
        </template>
        <button
          v-if="authStore.isAuthenticated && !showForkForm"
          class="secondary"
          @click="showForkForm = true"
        >
          <GitFork :size="16" />{{ $t('recipes.createVariant') }}
        </button>
      </div>
    </div>
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

    <RecipeSummary :recipe="recipe" />
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
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
}

.fork-form {
  align-items: center;
}

.versions-section {
  margin-top: 2rem;
}
</style>
