<script setup lang="ts">
import { Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import CooklangStepInput from '../components/CooklangStepInput.vue'
import IngredientPicker from '../components/IngredientPicker.vue'
import {
  createRecipe,
  getRecipe,
  importRecipeFromCooklang,
  updateRecipe,
  uploadRecipeImage,
} from '../api/recipes'
import { formatUnit } from '../utils/format'
import type { RecipeInput } from '../types/models'
import type { DietType, Ingredient, Unit } from '../types/models'
import { takePendingImportDraft } from '../utils/pendingImportDraft'

const props = defineProps<{
  id?: string | number | null
}>()
const { t } = useI18n()
const router = useRouter()
const isEditing = Boolean(props.id)

// Nouvelle recette uniquement : saisie manuelle (formulaire habituel) ou collage direct
// de markup Cooklang, parsé côté serveur pour pré-remplir ingrédients/étapes. La recette
// créée est ensuite ouverte en édition pour vérifier/corriger le résultat de l'auto-parsing
// (unités par défaut, quantités non reconnues).
const creationMode = ref<'manual' | 'cooklang'>('manual')
const cooklangForm = ref({ title: '', servings: 4, raw_cooklang: '' })
const cooklangError = ref('')
const isImportingCooklang = ref(false)

async function handleCooklangSubmit() {
  cooklangError.value = ''
  isImportingCooklang.value = true
  try {
    const recipe = await importRecipeFromCooklang({
      title: cooklangForm.value.title,
      servings: cooklangForm.value.servings,
      raw_cooklang: cooklangForm.value.raw_cooklang,
    })
    router.push({ name: 'recipe-edit', params: { id: recipe.id } })
  } catch {
    cooklangError.value = t('recipes.cooklangImportError')
  } finally {
    isImportingCooklang.value = false
  }
}

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
  // Ligne importée depuis une recette scrapée dont l'ingrédient n'a pas pu être rapproché
  // automatiquement du catalogue (voir apps/importer/services.py::find_matching_ingredient) :
  // affiche un badge (+ le texte d'origine pour aider) tant qu'aucun ingrédient n'a été
  // choisi/créé ici.
  unmatched?: boolean
  raw_line?: string
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
  if (isEditing && props.id) {
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
    return
  }

  // Recette pré-remplie depuis un import d'URL (voir RecipeListView.vue::handleImport) : les
  // ingrédients déjà rapprochés du catalogue arrivent avec leur Ingredient, les autres arrivent
  // vides et marqués `unmatched` pour que l'utilisateur les choisisse ou les crée ici même
  // (IngredientPicker gère déjà recherche + création, et la soumission reste bloquée tant qu'une
  // ligne n'a pas d'ingrédient — pas besoin d'un écran de vérification séparé).
  const draft = takePendingImportDraft()
  if (!draft) return

  form.value = {
    ...form.value,
    title: draft.title,
    servings: draft.servings,
    cook_time_minutes: draft.cook_time_minutes,
    source_url: draft.source_url,
    image_url: draft.image_url,
  }
  ingredientRows.value = draft.ingredients.map((item, index) => ({
    ingredient: item.ingredient,
    unmatched: !item.ingredient,
    raw_line: item.raw_line,
    quantity: item.quantity,
    unit: item.unit,
    group_name: '',
    order: index + 1,
  }))
  stepRows.value = draft.steps.map((step) => ({ instruction: step.instruction, order: step.order }))
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

// L'unité "piece" ne se compte qu'en entier (pas de "1.5 pièce") : on arrondit toute
// quantité déjà saisie lorsqu'on bascule sur cette unité.
function onUnitChange(row: IngredientRow) {
  if (row.unit !== 'piece') return
  const numeric = Number(row.quantity)
  if (!Number.isFinite(numeric)) return
  row.quantity = Math.round(numeric)
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

    <div v-if="!isEditing" class="row mode-toggle" role="tablist">
      <button
        type="button"
        role="tab"
        :aria-selected="creationMode === 'manual'"
        :class="creationMode === 'manual' ? '' : 'secondary'"
        @click="creationMode = 'manual'"
      >
        {{ $t('recipes.modeManual') }}
      </button>
      <button
        type="button"
        role="tab"
        :aria-selected="creationMode === 'cooklang'"
        :class="creationMode === 'cooklang' ? '' : 'secondary'"
        @click="creationMode = 'cooklang'"
      >
        {{ $t('recipes.modeCooklang') }}
      </button>
    </div>

    <form v-if="!isEditing && creationMode === 'cooklang'" class="card" @submit.prevent="handleCooklangSubmit">
      <div class="field">
        <label for="cooklang-title">{{ $t('recipes.formTitle') }}</label>
        <input id="cooklang-title" v-model="cooklangForm.title" required />
      </div>
      <div class="field" style="width: 140px">
        <label for="cooklang-servings">{{ $t('planning.servings') }}</label>
        <input id="cooklang-servings" v-model.number="cooklangForm.servings" type="number" min="1" required />
      </div>
      <div class="field">
        <label for="cooklang-text">{{ $t('recipes.cooklangText') }}</label>
        <p class="muted cooklang-hint">{{ $t('recipes.cooklangHint') }}</p>
        <textarea
          id="cooklang-text"
          v-model="cooklangForm.raw_cooklang"
          rows="10"
          required
          :placeholder="$t('recipes.cooklangPlaceholder')"
        />
      </div>
      <p v-if="cooklangError" class="error">{{ cooklangError }}</p>
      <div class="row" style="margin-top: 1rem">
        <button type="submit" :disabled="isImportingCooklang">{{ $t('recipes.cooklangImportButton') }}</button>
      </div>
    </form>

    <form v-else @submit.prevent="handleSubmit">
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
        <template v-for="(row, index) in ingredientRows" :key="index">
        <div class="row ingredient-row">
          <div class="field" style="flex: 2; min-width: 220px">
            <label :for="`ingredient-${index}`">{{ $t('recipes.ingredient') }}</label>
            <IngredientPicker :id="`ingredient-${index}`" v-model="row.ingredient" />
          </div>
          <div class="field" style="width: 100px">
            <label :for="`quantity-${index}`">{{ $t('recipes.quantity') }}</label>
            <input
              :id="`quantity-${index}`"
              v-model="row.quantity"
              type="number"
              :step="row.unit === 'piece' ? 1 : 0.01"
              min="0"
              required
            />
          </div>
          <div class="field" style="width: 110px">
            <label :for="`unit-${index}`">{{ $t('recipes.unit') }}</label>
            <select :id="`unit-${index}`" v-model="row.unit" @change="onUnitChange(row)">
              <option v-for="unit in UNITS" :key="unit" :value="unit">{{ formatUnit(unit) }}</option>
            </select>
          </div>
          <button
            type="button"
            class="secondary icon-btn ingredient-remove"
            :aria-label="$t('common.remove')"
            @click="removeIngredientRow(index)"
          >
            <Trash2 :size="16" />
          </button>
        </div>
        <span v-if="row.unmatched && !row.ingredient" class="not-found-badge">
          {{ $t('recipes.importNotFound') }}
          <template v-if="row.raw_line">— « {{ row.raw_line }} »</template>
        </span>
        </template>
        <button type="button" class="secondary" @click="addIngredientRow">
          <Plus :size="16" />{{ $t('recipes.addIngredient') }}
        </button>
      </div>

      <div class="card" style="margin-top: 1rem">
        <h2>{{ $t('recipes.steps') }}</h2>
        <div v-for="(step, index) in stepRows" :key="index" class="row" style="align-items: flex-end">
          <div class="field" style="flex: 1; min-width: 0">
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
.mode-toggle {
  margin-bottom: 1rem;
}

.cooklang-hint {
  margin: 0 0 0.35rem;
  font-size: 0.85rem;
}

.current-image {
  max-width: 220px;
  max-height: 140px;
  object-fit: cover;
  border-radius: 14px;
  margin: 0.25rem 0 1rem;
}

.ingredient-row {
  align-items: flex-end;
}

/* Les .field ont un margin-bottom (0.85rem) que le bouton n'a pas : on le compense pour que le
   bouton soit sur la même ligne que les inputs. */
.ingredient-remove {
  margin-bottom: 0.85rem;
  flex-shrink: 0;
}

.not-found-badge {
  display: inline-block;
  margin-top: 0.35rem;
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: 0.75rem;
  font-weight: 600;
}
</style>
