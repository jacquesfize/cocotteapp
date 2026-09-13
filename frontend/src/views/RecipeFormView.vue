<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import CooklangStepInput from '../components/CooklangStepInput.vue'
import IngredientPicker from '../components/IngredientPicker.vue'
import { createRecipe, getRecipe, updateRecipe, uploadRecipeImage } from '../api/recipes'
import type { RecipeInput } from '../types/models'
import type { DietType, Ingredient, Unit } from '../types/models'

const props = defineProps<{
  id?: string | number | null
}>()
const { t } = useI18n()
const router = useRouter()
const isEditing = Boolean(props.id)

const form = ref<Omit<RecipeInput, 'ingredients' | 'steps'>>({
  title: '',
  description: '',
  servings: 4,
  prep_time_minutes: 10,
  cook_time_minutes: 20,
  diet_type: 'omnivore' as DietType,
  is_public: true,
  source_url: '',
  video_url: '',
  image_url: '',
})

interface IngredientRow {
  ingredient: Ingredient | null
  quantity: string | number
  unit: Unit
  group_name: string
  order: number
}

interface StepRow {
  instruction: string
  order: number
}

const ingredientRows = ref<IngredientRow[]>([
  { ingredient: null, quantity: '', unit: 'g', group_name: '', order: 1 },
])
const stepRows = ref<StepRow[]>([{ instruction: '', order: 1 }])

// Noms des ingrédients déjà ajoutés à la recette : utilisés pour l'auto-complétion
// "@ingrédient" dans les étapes, et pour repérer une mention qui n'y correspond à rien.
const knownIngredientNames = computed(() =>
  ingredientRows.value.filter((row) => row.ingredient).map((row) => row.ingredient!.name),
)

const imageFile = ref<File | null>(null)
const currentImageUrl = ref('')
const error = ref('')
const isSubmitting = ref(false)

function handleImageFileChange(event: Event) {
  imageFile.value = (event.target as HTMLInputElement).files?.[0] || null
}

const UNITS: Unit[] = ['g', 'kg', 'ml', 'l', 'piece', 'tbsp', 'tsp', 'pinch']

onMounted(async () => {
  if (!isEditing || !props.id) return
  const recipe = await getRecipe(props.id)
  form.value = {
    title: recipe.title,
    description: recipe.description,
    servings: recipe.servings,
    prep_time_minutes: recipe.prep_time_minutes,
    cook_time_minutes: recipe.cook_time_minutes,
    diet_type: recipe.diet_type,
    is_public: recipe.is_public,
    source_url: recipe.source_url,
    video_url: recipe.video_url,
    image_url: recipe.image_url,
  }
  currentImageUrl.value = recipe.image || ''
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

// Une mention "@ingrédient" dans une étape peut désigner un ingrédient qui existe déjà en
// base mais pas encore dans cette recette : on l'ajoute alors automatiquement à la liste
// (voir CooklangStepInput.vue), pour éviter à l'utilisateur de le rechercher deux fois.
function handleMentionIngredient(ingredient: Ingredient) {
  const alreadyAdded = ingredientRows.value.some((row) => row.ingredient?.id === ingredient.id)
  if (alreadyAdded) return
  ingredientRows.value.push({
    ingredient,
    quantity: '',
    unit: ingredient.default_unit,
    group_name: '',
    order: ingredientRows.value.length + 1,
  })
}

function removeIngredientRow(index: number) {
  ingredientRows.value.splice(index, 1)
}

function addStepRow() {
  stepRows.value.push({ instruction: '', order: stepRows.value.length + 1 })
}

function removeStepRow(index: number) {
  stepRows.value.splice(index, 1)
}

async function handleSubmit() {
  error.value = ''
  const missingIngredient = ingredientRows.value.some((row) => !row.ingredient)
  if (missingIngredient) {
    error.value = t('recipes.missingIngredient')
    return
  }

  const payload: RecipeInput = {
    ...form.value,
    ingredients: ingredientRows.value.map((row, index) => ({
      ingredient_id: (row.ingredient as Ingredient).id,
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
    const recipe =
      isEditing && props.id ? await updateRecipe(props.id, payload) : await createRecipe(payload)
    if (imageFile.value) {
      await uploadRecipeImage(recipe.id, imageFile.value)
    }
    router.push({ name: 'recipe-detail', params: { id: recipe.id } })
  } catch {
    error.value = t('recipes.saveError')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div>
    <h1>{{ isEditing ? $t('recipes.editTitle') : $t('recipes.newTitle') }}</h1>
    <form @submit.prevent="handleSubmit">
      <div class="card">
        <div class="field">
          <label for="title">{{ $t('recipes.formTitle') }}</label>
          <input id="title" v-model="form.title" required />
        </div>
        <div class="field">
          <label for="description">{{ $t('recipes.description') }}</label>
          <textarea id="description" v-model="form.description" rows="3" />
        </div>
        <div class="row">
          <div class="field">
            <label for="servings">{{ $t('planning.servings') }}</label>
            <input id="servings" v-model.number="form.servings" type="number" min="1" required />
          </div>
          <div class="field">
            <label for="prep">{{ $t('recipes.prepTime') }}</label>
            <input id="prep" v-model.number="form.prep_time_minutes" type="number" min="0" required />
          </div>
          <div class="field">
            <label for="cook">{{ $t('recipes.cookTime') }}</label>
            <input id="cook" v-model.number="form.cook_time_minutes" type="number" min="0" required />
          </div>
          <div class="field">
            <label for="diet_type">{{ $t('recipes.diet') }}</label>
            <select id="diet_type" v-model="form.diet_type">
              <option value="omnivore">{{ $t('diet.omnivore') }}</option>
              <option value="vegetarian">{{ $t('diet.vegetarian') }}</option>
              <option value="vegan">{{ $t('diet.vegan') }}</option>
            </select>
          </div>
        </div>
      </div>

      <div class="card" style="margin-top: 1rem">
        <h2>{{ $t('recipes.ingredients') }}</h2>
        <div v-for="(row, index) in ingredientRows" :key="index" class="row" style="align-items: flex-end">
          <div class="field" style="flex: 2; min-width: 220px">
            <label :for="`ingredient-${index}`">{{ $t('recipes.ingredient') }}</label>
            <IngredientPicker :id="`ingredient-${index}`" v-model="row.ingredient" />
          </div>
          <div class="field" style="width: 100px">
            <label :for="`quantity-${index}`">{{ $t('recipes.quantity') }}</label>
            <input :id="`quantity-${index}`" v-model="row.quantity" type="number" step="0.01" min="0" required />
          </div>
          <div class="field" style="width: 110px">
            <label :for="`unit-${index}`">{{ $t('recipes.unit') }}</label>
            <select :id="`unit-${index}`" v-model="row.unit">
              <option v-for="unit in UNITS" :key="unit" :value="unit">{{ unit }}</option>
            </select>
          </div>
          <button
            type="button"
            class="secondary icon-btn"
            :aria-label="$t('common.remove')"
            @click="removeIngredientRow(index)"
          >
            <Trash2 :size="16" />
          </button>
        </div>
        <button type="button" class="secondary" @click="addIngredientRow">
          <Plus :size="16" />{{ $t('recipes.addIngredient') }}
        </button>
      </div>

      <div class="card" style="margin-top: 1rem">
        <h2>{{ $t('recipes.steps') }}</h2>
        <div v-for="(step, index) in stepRows" :key="index" class="row" style="align-items: flex-end">
          <div class="field" style="flex: 1">
            <label :for="`step-${index}`">{{ $t('recipes.step', { n: index + 1 }) }}</label>
            <CooklangStepInput
              :id="`step-${index}`"
              v-model="step.instruction"
              :ingredient-names="knownIngredientNames"
              @add-ingredient="handleMentionIngredient"
            />
          </div>
          <button
            type="button"
            class="secondary icon-btn"
            :aria-label="$t('common.remove')"
            @click="removeStepRow(index)"
          >
            <Trash2 :size="16" />
          </button>
        </div>
        <button type="button" class="secondary" @click="addStepRow">
          <Plus :size="16" />{{ $t('recipes.addStep') }}
        </button>
      </div>

      <div class="card" style="margin-top: 1rem">
        <h2>{{ $t('recipes.media') }}</h2>
        <div class="row">
          <div class="field" style="flex: 1; min-width: 220px">
            <label for="image_url">{{ $t('recipes.imageUrl') }}</label>
            <input id="image_url" v-model="form.image_url" type="url" placeholder="https://..." />
          </div>
          <div class="field" style="flex: 1; min-width: 220px">
            <label for="image_file">{{ $t('recipes.imageFile') }}</label>
            <input id="image_file" type="file" accept="image/*" @change="handleImageFileChange" />
          </div>
        </div>
        <img v-if="currentImageUrl" :src="currentImageUrl" class="current-image" alt="" />
        <div class="row">
          <div class="field" style="flex: 1; min-width: 220px">
            <label for="source_url">{{ $t('recipes.sourceUrl') }}</label>
            <input id="source_url" v-model="form.source_url" type="url" placeholder="https://..." />
          </div>
          <div class="field" style="flex: 1; min-width: 220px">
            <label for="video_url">{{ $t('recipes.videoUrl') }}</label>
            <input
              id="video_url"
              v-model="form.video_url"
              type="url"
              placeholder="https://www.youtube.com/watch?v=..."
            />
          </div>
        </div>
      </div>

      <p v-if="error" class="error">{{ error }}</p>
      <div class="row" style="margin-top: 1rem">
        <button type="submit" :disabled="isSubmitting">{{ $t('common.save') }}</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.current-image {
  max-width: 220px;
  max-height: 140px;
  object-fit: cover;
  border-radius: 14px;
  margin: 0.25rem 0 1rem;
}
</style>
