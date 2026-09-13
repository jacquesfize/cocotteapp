<script setup>
import { Pencil, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AddToPlanForm from '../components/AddToPlanForm.vue'
import RecipeSummary from '../components/RecipeSummary.vue'
import { deleteRecipe, getRecipe } from '../api/recipes'
import { useAuthStore } from '../stores/auth'

const props = defineProps({
  id: { type: [String, Number], required: true },
})
const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const recipe = ref(null)
const deleteError = ref('')

const isOwner = computed(
  () => Boolean(authStore.user) && recipe.value?.author_id === authStore.user.id,
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
</script>

<template>
  <div v-if="recipe">
    <div class="row page-header">
      <h1>{{ recipe.title }}</h1>
      <div v-if="isOwner" class="row">
        <RouterLink :to="{ name: 'recipe-edit', params: { id: recipe.id } }">
          <button class="secondary"><Pencil :size="16" />{{ $t('common.edit') }}</button>
        </RouterLink>
        <button class="danger" @click="handleDelete"><Trash2 :size="16" />{{ $t('common.delete') }}</button>
      </div>
    </div>
    <p v-if="deleteError" class="error">{{ deleteError }}</p>

    <RecipeSummary :recipe="recipe" />
    <AddToPlanForm v-if="authStore.isAuthenticated" :key="recipe.id" :recipe="recipe" />
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
}
</style>
