<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import IngredientPicker from '../components/IngredientPicker.vue'
import { createRecipe, getRecipe, updateRecipe } from '../api/recipes'

const props = defineProps({
  id: { type: [String, Number], default: null },
})
const router = useRouter()
const isEditing = Boolean(props.id)

const form = ref({
  title: '',
  description: '',
  servings: 4,
  prep_time_minutes: 10,
  cook_time_minutes: 20,
  diet_type: 'omnivore',
  is_public: true,
})

const ingredientRows = ref([{ ingredient: null, quantity: '', unit: 'g', group_name: '', order: 1 }])
const stepRows = ref([{ instruction: '', order: 1 }])
const error = ref('')
const isSubmitting = ref(false)

const UNITS = ['g', 'kg', 'ml', 'l', 'piece', 'tbsp', 'tsp', 'pinch']

onMounted(async () => {
  if (!isEditing) return
  const recipe = await getRecipe(props.id)
  form.value = {
    title: recipe.title,
    description: recipe.description,
    servings: recipe.servings,
    prep_time_minutes: recipe.prep_time_minutes,
    cook_time_minutes: recipe.cook_time_minutes,
    diet_type: recipe.diet_type,
    is_public: recipe.is_public,
  }
  ingredientRows.value = recipe.ingredients.map((item) => ({
    ingredient: item.ingredient,
    quantity: item.quantity,
    unit: item.unit,
    group_name: item.group_name,
    order: item.order,
  }))
  stepRows.value = recipe.steps.map((step) => ({ instruction: step.instruction, order: step.order }))
})

function addIngredientRow() {
  ingredientRows.value.push({
    ingredient: null,
    quantity: '',
    unit: 'g',
    group_name: '',
    order: ingredientRows.value.length + 1,
  })
}

function removeIngredientRow(index) {
  ingredientRows.value.splice(index, 1)
}

function addStepRow() {
  stepRows.value.push({ instruction: '', order: stepRows.value.length + 1 })
}

function removeStepRow(index) {
  stepRows.value.splice(index, 1)
}

async function handleSubmit() {
  error.value = ''
  const missingIngredient = ingredientRows.value.some((row) => !row.ingredient)
  if (missingIngredient) {
    error.value = 'Sélectionnez un ingrédient pour chaque ligne (ou supprimez la ligne).'
    return
  }

  const payload = {
    ...form.value,
    ingredients: ingredientRows.value.map((row, index) => ({
      ingredient_id: row.ingredient.id,
      quantity: row.quantity,
      unit: row.unit,
      group_name: row.group_name,
      order: index + 1,
    })),
    steps: stepRows.value
      .filter((step) => step.instruction.trim())
      .map((step, index) => ({ instruction: step.instruction, order: index + 1 })),
  }

  isSubmitting.value = true
  try {
    const recipe = isEditing ? await updateRecipe(props.id, payload) : await createRecipe(payload)
    router.push({ name: 'recipe-detail', params: { id: recipe.id } })
  } catch {
    error.value = "Impossible d'enregistrer la recette."
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div>
    <h1>{{ isEditing ? 'Modifier la recette' : 'Nouvelle recette' }}</h1>
    <form @submit.prevent="handleSubmit">
      <div class="card">
        <div class="field">
          <label for="title">Titre</label>
          <input id="title" v-model="form.title" required />
        </div>
        <div class="field">
          <label for="description">Description</label>
          <textarea id="description" v-model="form.description" rows="3" />
        </div>
        <div class="row">
          <div class="field">
            <label for="servings">Portions</label>
            <input id="servings" v-model.number="form.servings" type="number" min="1" required />
          </div>
          <div class="field">
            <label for="prep">Prépa (min)</label>
            <input id="prep" v-model.number="form.prep_time_minutes" type="number" min="0" required />
          </div>
          <div class="field">
            <label for="cook">Cuisson (min)</label>
            <input id="cook" v-model.number="form.cook_time_minutes" type="number" min="0" required />
          </div>
          <div class="field">
            <label for="diet_type">Régime</label>
            <select id="diet_type" v-model="form.diet_type">
              <option value="omnivore">Omnivore</option>
              <option value="vegetarian">Végétarien</option>
              <option value="vegan">Végan</option>
            </select>
          </div>
        </div>
      </div>

      <div class="card" style="margin-top: 1rem">
        <h2>Ingrédients</h2>
        <div v-for="(row, index) in ingredientRows" :key="index" class="row" style="align-items: flex-end">
          <div class="field" style="flex: 2; min-width: 220px">
            <label :for="`ingredient-${index}`">Ingrédient</label>
            <IngredientPicker :id="`ingredient-${index}`" v-model="row.ingredient" />
          </div>
          <div class="field" style="width: 100px">
            <label :for="`quantity-${index}`">Quantité</label>
            <input :id="`quantity-${index}`" v-model="row.quantity" type="number" step="0.01" min="0" required />
          </div>
          <div class="field" style="width: 110px">
            <label :for="`unit-${index}`">Unité</label>
            <select :id="`unit-${index}`" v-model="row.unit">
              <option v-for="unit in UNITS" :key="unit" :value="unit">{{ unit }}</option>
            </select>
          </div>
          <button type="button" class="secondary" @click="removeIngredientRow(index)">Retirer</button>
        </div>
        <button type="button" class="secondary" @click="addIngredientRow">+ Ajouter un ingrédient</button>
      </div>

      <div class="card" style="margin-top: 1rem">
        <h2>Étapes</h2>
        <div v-for="(step, index) in stepRows" :key="index" class="row" style="align-items: flex-end">
          <div class="field" style="flex: 1">
            <label :for="`step-${index}`">Étape {{ index + 1 }}</label>
            <textarea :id="`step-${index}`" v-model="step.instruction" rows="2" />
          </div>
          <button type="button" class="secondary" @click="removeStepRow(index)">Retirer</button>
        </div>
        <button type="button" class="secondary" @click="addStepRow">+ Ajouter une étape</button>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
      <div class="row" style="margin-top: 1rem">
        <button type="submit" :disabled="isSubmitting">Enregistrer</button>
      </div>
    </form>
  </div>
</template>
