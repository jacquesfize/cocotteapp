<script setup lang="ts">
import { ChefHat, Plus, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import CooklangStepInput from '../components/CooklangStepInput.vue'
import ImageUploadWithCredit from '../components/ImageUploadWithCredit.vue'
import IngredientPicker from '../components/IngredientPicker.vue'
import PageHeader from '../components/PageHeader.vue'
import {
  createRecipe,
  getRecipe,
  importRecipeFromCooklang,
  updateRecipe,
  uploadRecipeImage,
  uploadStepImage,
} from '../api/recipes'
import { formatUnit } from '../utils/format'
import { imageCreditDomain } from '../utils/imageCredit'
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

function validateCooklangForm(): string {
  if (!cooklangForm.value.title.trim()) return t('recipes.missingTitle')
  if (!Number.isFinite(cooklangForm.value.servings) || cooklangForm.value.servings < 1) {
    return t('recipes.invalidServings')
  }
  if (!cooklangForm.value.raw_cooklang.trim()) return t('recipes.cooklangTextRequired')
  return ''
}

async function handleCooklangSubmit() {
  cooklangError.value = ''
  const validationError = validateCooklangForm()
  if (validationError) {
    cooklangError.value = validationError
    return
  }
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
  content_publicly_licensed: false,
  source_url: '',
  video_url: '',
  image_url: '',
  image_license: '',
  image_credit_author: '',
  image_credit_source_url: '',
  image_credit_license_url: '',
  image_credit_note: '',
})
// Valeur de `image_url` telle que chargée depuis l'API (ou vide pour une nouvelle recette) :
// sert à ImageUploadWithCredit pour ne réclamer une licence/crédit que si l'image change
// réellement (voir CLAUDE.md "grandfathering" — modifier le reste d'une recette existante ne
// doit jamais réclamer un crédit pour une image déjà en place avant cette fonctionnalité).
const originalImageUrl = ref('')

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
  id?: number
  instruction: string
  order: number
  // Photo de l'étape en cours d'édition : soit un fichier à téléverser après la sauvegarde de la
  // recette (une fois l'id réel de l'étape connu), soit une URL directe.
  imageFile: File | null
  imageUrl: string
  // Aperçu de l'image déjà enregistrée côté serveur (relative /media/...), pour l'affichage.
  currentImage: string
  // Valeur de `imageUrl` telle que chargée depuis l'API, pour la détection de changement (voir
  // `originalImageUrl` ci-dessus, même logique par étape).
  originalImageUrl: string
  image_license: string
  image_credit_author: string
  image_credit_source_url: string
  image_credit_license_url: string
  image_credit_note: string
  // L'image d'étape est facultative : le formulaire crédit/licence ne s'affiche qu'à la demande
  // (bouton "Ajouter une image"), sauf si l'étape en a déjà une au chargement.
  showImageForm: boolean
}

function emptyStepRow(order: number): StepRow {
  return {
    instruction: '',
    order,
    imageFile: null,
    imageUrl: '',
    currentImage: '',
    originalImageUrl: '',
    image_license: '',
    image_credit_author: '',
    image_credit_source_url: '',
    image_credit_license_url: '',
    image_credit_note: '',
    showImageForm: false,
  }
}

const ingredientRows = ref<IngredientRow[]>([
  { ingredient: null, quantity: '', unit: 'g', group_name: '', order: 1 },
])
const stepRows = ref<StepRow[]>([emptyStepRow(1)])

// Noms des ingrédients déjà ajoutés à la recette : utilisés pour l'auto-complétion
// "@ingrédient" dans les étapes, et pour repérer une mention qui n'y correspond à rien.
const knownIngredientNames = computed(() =>
  ingredientRows.value.filter((row) => row.ingredient).map((row) => row.ingredient!.name),
)

const imageFile = ref<File | null>(null)
const currentImageUrl = ref('')
const error = ref('')
const isSubmitting = ref(false)

type ImageUploadWithCreditInstance = InstanceType<typeof ImageUploadWithCredit>
const mainImageRef = ref<ImageUploadWithCreditInstance | null>(null)
const stepImageRefs = ref<(ImageUploadWithCreditInstance | null)[]>([])

function setStepImageRef(el: unknown, index: number) {
  stepImageRefs.value[index] = el as ImageUploadWithCreditInstance | null
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
      content_publicly_licensed: recipe.content_publicly_licensed,
      source_url: recipe.source_url,
      video_url: recipe.video_url,
      image_url: recipe.image_url,
      image_license: recipe.image_license,
      image_credit_author: recipe.image_credit_author,
      image_credit_source_url: recipe.image_credit_source_url,
      image_credit_license_url: recipe.image_credit_license_url,
      image_credit_note: recipe.image_credit_note,
    }
    currentImageUrl.value = recipe.image || ''
    originalImageUrl.value = recipe.image_url || ''
    ingredientRows.value = recipe.ingredients.map((item) => ({
      ingredient: item.ingredient,
      quantity: item.quantity,
      unit: item.unit,
      group_name: item.group_name,
      order: item.order,
    }))
    stepRows.value = recipe.steps.map((step) => ({
      id: step.id,
      instruction: step.instruction,
      order: step.order,
      imageFile: null,
      imageUrl: step.image_url || '',
      currentImage: step.image || '',
      originalImageUrl: step.image_url || '',
      image_license: step.image_license || '',
      image_credit_author: step.image_credit_author || '',
      image_credit_source_url: step.image_credit_source_url || '',
      image_credit_license_url: step.image_credit_license_url || '',
      image_credit_note: step.image_credit_note || '',
      showImageForm: Boolean(step.image || step.image_url),
    }))
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
  // L'image d'un import d'URL (og:image le plus souvent) n'a pas de licence connue : on
  // pré-remplit "Non précisée" + une note citant la source, éditable avant la sauvegarde
  // effective (rien n'est encore enregistré à ce stade, voir commentaire ci-dessus).
  if (draft.image_url) {
    const domain = imageCreditDomain(draft.source_url) || imageCreditDomain(draft.image_url)
    form.value.image_license = 'unknown'
    form.value.image_credit_note = domain ? t('recipes.importedImageCreditNote', { domain }) : ''
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
  stepRows.value = draft.steps.map((step) => ({ ...emptyStepRow(step.order), instruction: step.instruction }))
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
  stepRows.value.push(emptyStepRow(stepRows.value.length + 1))
}

function removeStepRow(index: number) {
  stepRows.value.splice(index, 1)
}

// Validations exprimées ici en JS plutôt que confiées aux seuls attributs HTML5
// (required/min/step) : sur mobile, la bulle de validation native du navigateur peut s'afficher
// hors écran ou derrière le clavier virtuel — voir docs/developer (mobile-validation). Le
// formulaire porte `novalidate` : ces vérifications sont donc la seule protection.
function validateForm(): string {
  if (!form.value.title.trim()) return t('recipes.missingTitle')
  if (!Number.isFinite(form.value.servings) || form.value.servings < 1) return t('recipes.invalidServings')
  if (!Number.isFinite(form.value.prep_time_minutes) || form.value.prep_time_minutes < 0) {
    return t('recipes.invalidPrepTime')
  }
  if (!Number.isFinite(form.value.cook_time_minutes) || form.value.cook_time_minutes < 0) {
    return t('recipes.invalidCookTime')
  }
  if (ingredientRows.value.some((row) => !row.ingredient)) return t('recipes.missingIngredient')
  const invalidQuantity = ingredientRows.value.some((row) => {
    if (row.quantity === '' || row.quantity === null) return true
    const numeric = Number(row.quantity)
    return !Number.isFinite(numeric) || numeric < 0
  })
  if (invalidQuantity) return t('recipes.invalidQuantity')
  return ''
}

async function handleSubmit() {
  error.value = ''
  const validationError = validateForm()
  if (validationError) {
    error.value = validationError
    return
  }

  const submittedStepRows = stepRows.value.filter((step) => step.instruction.trim())
  const mainImageValid = mainImageRef.value ? mainImageRef.value.validate() : true
  const stepImagesValid = stepImageRefs.value
    .slice(0, submittedStepRows.length)
    .every((ref) => !ref || ref.validate())
  if (!mainImageValid || !stepImagesValid) {
    error.value = t('imageCredit.formInvalid')
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
    steps: submittedStepRows.map((step, index) => ({
      id: step.id,
      instruction: step.instruction,
      order: index + 1,
      image_url: step.imageUrl,
      image_license: step.image_license,
      image_credit_author: step.image_credit_author,
      image_credit_source_url: step.image_credit_source_url,
      image_credit_license_url: step.image_credit_license_url,
      image_credit_note: step.image_credit_note,
    })),
  }

  isSubmitting.value = true
  try {
    const recipe =
      isEditing && props.id ? await updateRecipe(props.id, payload) : await createRecipe(payload)
    if (imageFile.value) {
      await uploadRecipeImage(recipe.id, imageFile.value, {
        image_license: form.value.image_license || '',
        image_credit_author: form.value.image_credit_author,
        image_credit_source_url: form.value.image_credit_source_url,
        image_credit_license_url: form.value.image_credit_license_url,
        image_credit_note: form.value.image_credit_note,
      })
    }
    // `recipe.steps` est renvoyé dans le même ordre que `payload.steps` (voir docstring de
    // l'endpoint) : on peut donc les associer par index pour retrouver l'id réel de chaque étape
    // (nouvellement créée ou existante) et y téléverser sa photo en attente.
    for (let index = 0; index < submittedStepRows.length; index += 1) {
      const row = submittedStepRows[index]
      const savedStep = recipe.steps[index]
      if (row.imageFile && savedStep) {
        await uploadStepImage(recipe.id, savedStep.id, row.imageFile, {
          image_license: row.image_license || '',
          image_credit_author: row.image_credit_author,
          image_credit_source_url: row.image_credit_source_url,
          image_credit_license_url: row.image_credit_license_url,
          image_credit_note: row.image_credit_note,
        })
      }
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
    <PageHeader :icon="ChefHat">{{ isEditing ? $t('recipes.editTitle') : $t('recipes.newTitle') }}</PageHeader>

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

    <form
      v-if="!isEditing && creationMode === 'cooklang'"
      class="card"
      novalidate
      @submit.prevent="handleCooklangSubmit"
    >
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

    <form v-else novalidate @submit.prevent="handleSubmit">
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
              step="any"
              min="0"
              required
            />
          </div>
          <div class="field" style="width: 110px">
            <label :for="`unit-${index}`">{{ $t('recipes.unit') }}</label>
            <select :id="`unit-${index}`" v-model="row.unit">
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
        <div v-for="(step, index) in stepRows" :key="index" class="step-row">
          <div class="row" style="align-items: flex-end">
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
          <div class="field step-image-field">
            <button
              v-if="!step.showImageForm"
              type="button"
              class="secondary"
              @click="step.showImageForm = true"
            >
              <Plus :size="16" />{{ $t('recipes.addStepImage') }}
            </button>
            <template v-else>
              <label>{{ $t('recipes.stepImage') }}</label>
              <ImageUploadWithCredit
                :ref="(el) => setStepImageRef(el, index)"
                v-model:file="step.imageFile"
                v-model:image-url="step.imageUrl"
                v-model:license="step.image_license"
                v-model:credit-author="step.image_credit_author"
                v-model:credit-source-url="step.image_credit_source_url"
                v-model:credit-license-url="step.image_credit_license_url"
                v-model:credit-note="step.image_credit_note"
                :current-image-url="step.currentImage"
                :original-image-url="step.originalImageUrl"
                compact
              />
            </template>
          </div>
        </div>
        <button type="button" class="secondary" @click="addStepRow">
          <Plus :size="16" />{{ $t('recipes.addStep') }}
        </button>
      </div>

      <div class="card" style="margin-top: 1rem">
        <h2>{{ $t('recipes.media') }}</h2>
        <ImageUploadWithCredit
          ref="mainImageRef"
          v-model:file="imageFile"
          v-model:image-url="form.image_url"
          v-model:license="form.image_license"
          v-model:credit-author="form.image_credit_author"
          v-model:credit-source-url="form.image_credit_source_url"
          v-model:credit-license-url="form.image_credit_license_url"
          v-model:credit-note="form.image_credit_note"
          :current-image-url="currentImageUrl"
          :original-image-url="originalImageUrl"
        />
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
        <label v-if="form.source_url" class="checkbox-field">
          <input type="checkbox" v-model="form.content_publicly_licensed" />
          {{ $t('recipes.publicLicenseOptIn') }}
        </label>
        <p v-if="form.source_url" class="muted">{{ $t('recipes.publicLicenseHint') }}</p>
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

.ingredient-row {
  align-items: flex-end;
}

.step-row:not(:last-child) {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.step-image-field {
  margin-top: 0.5rem;
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
