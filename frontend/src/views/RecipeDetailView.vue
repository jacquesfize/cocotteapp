<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import AddToPlanForm from '../components/AddToPlanForm.vue'
import RecipeSummary from '../components/RecipeSummary.vue'
import { deleteRecipe, getRecipe } from '../api/recipes'

const props = defineProps({
  id: { type: [String, Number], required: true },
})
const { t } = useI18n()
const router = useRouter()

const recipe = ref(null)

async function load() {
  recipe.value = await getRecipe(props.id)
}

onMounted(load)

async function handleDelete() {
  if (!confirm(t('recipes.deleteConfirm'))) return
  await deleteRecipe(props.id)
  router.push({ name: 'recipes' })
}
</script>

<template>
  <div v-if="recipe">
    <div class="row page-header">
      <h1>{{ recipe.title }}</h1>
      <div class="row">
        <RouterLink :to="{ name: 'recipe-edit', params: { id: recipe.id } }">
          <button class="secondary">{{ $t('common.edit') }}</button>
        </RouterLink>
        <button class="danger" @click="handleDelete">{{ $t('common.delete') }}</button>
      </div>
    </div>

    <RecipeSummary :recipe="recipe" />
    <AddToPlanForm :key="recipe.id" :recipe="recipe" />
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
}
</style>
