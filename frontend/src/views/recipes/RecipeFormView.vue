<script setup lang="ts">
import { ChefHat, Image as ImageIcon, Info, Plus, Scale, Trash2 } from '@lucide/vue'
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import CooklangStepInput from '../../components/recipes/CooklangStepInput.vue'
import CookwarePicker from '../../components/recipes/CookwarePicker.vue'
import FreeImageSuggestions from '../../components/recipes/FreeImageSuggestions.vue'
import ImageUploadWithCredit from '../../components/shared/ImageUploadWithCredit.vue'
import IngredientSections from '../../components/recipes/IngredientSections.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import {
  createRecipe,
  getRecipe,
  previewRecipeFromCooklang,
  updateRecipe,
  uploadRecipeImage,
  uploadStepImage,
} from '../../api/recipes'
import { orderRowsBySection } from '../../utils/ingredientSections'
import { recipeImageUrl } from '../../utils/recipeImageUrl'
import type { FreeImageSuggestion, RecipeInput } from '../../types/models'
import type { Cookware, DietType, Ingredient } from '../../types/models'
import type { IngredientFormRow } from '../../types/recipeForm'
import { takePendingImportDraft, type PendingImportDraft } from '../../utils/pendingImportDraft'

const props = defineProps<{
  id?: string | number | null
}>()
const { t } = useI18n()
const router = useRouter()
const isEditing = Boolean(props.id)

// Nouvelle recette uniquement : saisie manuelle (formulaire habituel) ou collage direct
// de markup Cooklang, parsé côté serveur (sans rien créer) pour pré-remplir le formulaire
// manuel : l'utilisateur y vérifie/corrige le résultat de l'auto-parsing (unités par défaut,
// quantités non reconnues, ingrédients non rapprochés) avant d'enregistrer.
const creationMode = ref<'manual' | 'cooklang'>('manual')
// Titre et portions facultatifs : laissés vides, le serveur les lit dans les métadonnées du
// fichier Cooklang (front matter `title:` / `servings:`) ; renseignés, ils les remplacent.
const cooklangForm = ref<{ title: string; servings: number | ''; raw_cooklang: string }>({
  title: '',
  servings: '',
  raw_cooklang: '',
})
const cooklangError = ref('')
const isImportingCooklang = ref(false)

function validateCooklangForm(): string {
  const { servings } = cooklangForm.value
  if (servings !== '' && (!Number.isFinite(servings) || servings < 1)) {
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
    const { title, servings, raw_cooklang } = cooklangForm.value
    const preview = await previewRecipeFromCooklang({
      ...(title.trim() ? { title: title.trim() } : {}),
      ...(servings !== '' ? { servings } : {}),
      raw_cooklang,
    })
    applyImportDraft({
      title: preview.title,
      description: preview.description,
      servings: preview.servings ?? form.value.servings,
      prep_time_minutes: preview.prep_time_minutes ?? form.value.prep_time_minutes,
      cook_time_minutes: preview.cook_time_minutes ?? form.value.cook_time_minutes,
      source_url: preview.source_url,
      source_type: 'cooklang',
      steps: preview.steps,
      ingredients: preview.ingredients,
      cookware: preview.cookware,
    })
    creationMode.value = 'manual'
  } catch (error) {
    // 400 du serveur : texte Cooklang illisible.
    const status = (error as { response?: { status?: number } })?.response?.status
    cooklangError.value = t(status === 400 ? 'recipes.cooklangInvalid' : 'recipes.cooklangImportError')
  } finally {
    isImportingCooklang.value = false
  }
}

const form = ref<Omit<RecipeInput, 'ingredients' | 'steps' | 'cookware_ids'>>({
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

// Texte des étapes telles que scrapées lors d'un import d'URL (vide sinon) : le texte d'une
// recette est protégé par le droit d'auteur de son auteur original, contrairement à la liste
// d'ingrédients et aux temps. Rendre public le contenu d'une recette importée exige donc d'en
// avoir réécrit les étapes : on bloque la soumission si l'une d'elles est restée telle quelle.
const importedStepTexts = ref<Set<string>>(new Set())

const showFreeImages = ref(false)

function applyFreeImage(suggestion: FreeImageSuggestion) {
  imageFile.value = null
  form.value.image_url = suggestion.url
  form.value.image_license = suggestion.image_license
  form.value.image_credit_author = suggestion.image_credit_author
  form.value.image_credit_source_url = suggestion.image_credit_source_url
  form.value.image_credit_license_url = suggestion.image_credit_license_url
  form.value.image_credit_note = ''
  showFreeImages.value = false
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

// Matériel de la recette, et noms de `#matériel` d'un Cooklang collé qui ne correspondent à rien
// dans la bibliothèque : proposés à la création (un clic) plutôt que créés d'office.
const selectedCookware = ref<Cookware[]>([])
const unmatchedCookwareNames = ref<string[]>([])
const cookwarePickerRef = ref<InstanceType<typeof CookwarePicker> | null>(null)
const knownCookwareNames = computed(() => selectedCookware.value.map((item) => item.name))

async function createUnmatchedCookware(name: string) {
  await cookwarePickerRef.value?.create(name)
  unmatchedCookwareNames.value = unmatchedCookwareNames.value.filter((item) => item !== name)
}

function handleMentionCookware(cookware: Cookware) {
  if (!selectedCookware.value.some((item) => item.id === cookware.id)) {
    selectedCookware.value = [...selectedCookware.value, cookware]
  }
}

const ingredientRows = ref<IngredientFormRow[]>([])
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
    selectedCookware.value = recipe.cookware ?? []
    currentImageUrl.value = recipe.image || ''
    originalImageUrl.value = recipe.image_url || ''
    ingredientRows.value = recipe.ingredients.map((item) => ({
      ingredient: item.ingredient,
      quantity: item.quantity,
      unit: item.unit,
      group_name: item.group_name,
      order: item.order,
      alternatives: (item.alternatives ?? []).map((alternative) => ({
        ingredient: alternative.ingredient,
        quantity: alternative.quantity,
        unit: alternative.unit,
        tag: alternative.tag,
        note: alternative.note,
      })),
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
      showImageForm: Boolean(recipeImageUrl(step)),
    }))
    return
  }

  // Recette pré-remplie depuis un import d'URL (voir RecipeListView.vue::handleImport).
  const draft = takePendingImportDraft()
  if (draft) applyImportDraft(draft)
})

// Pré-remplit le formulaire depuis un aperçu d'import (URL ou Cooklang collé) : les ingrédients
// déjà rapprochés du catalogue arrivent avec leur Ingredient, les autres arrivent vides et marqués
// `unmatched` pour que l'utilisateur les choisisse ou les crée ici même (IngredientPicker gère déjà
// recherche + création, et la soumission reste bloquée tant qu'une ligne n'a pas d'ingrédient —
// pas besoin d'un écran de vérification séparé).
function applyImportDraft(draft: PendingImportDraft) {
  form.value = {
    ...form.value,
    title: draft.title,
    description: draft.description ?? form.value.description,
    servings: draft.servings,
    prep_time_minutes: draft.prep_time_minutes ?? form.value.prep_time_minutes,
    cook_time_minutes: draft.cook_time_minutes,
    source_url: draft.source_url,
    ...(draft.source_type ? { source_type: draft.source_type } : {}),
  }
  // Pas de photo : celle du site source n'est jamais reprise (droit d'auteur du photographe),
  // l'utilisateur ajoute la sienne ou en choisit une libre de droits (FreeImageSuggestions).
  // Les étapes d'un Cooklang collé sont le texte de l'utilisateur : rien à réécrire.
  importedStepTexts.value =
    draft.source_type === 'cooklang' ? new Set() : new Set(draft.steps.map((step) => step.instruction.trim()))
  ingredientRows.value = draft.ingredients.map((item, index) => ({
    ingredient: item.ingredient,
    unmatched: !item.ingredient,
    raw_line: item.raw_line,
    quantity: item.quantity,
    unit: item.unit,
    group_name: item.group_name ?? '',
    order: index + 1,
  }))
  selectedCookware.value = (draft.cookware ?? []).flatMap((item) => (item.cookware ? [item.cookware] : []))
  unmatchedCookwareNames.value = (draft.cookware ?? []).filter((item) => !item.cookware).map((item) => item.name)
  stepRows.value = draft.steps.map((step) => ({ ...emptyStepRow(step.order), instruction: step.instruction }))
  if (!stepRows.value.length) stepRows.value = [emptyStepRow(1)]
}

// Une mention "@ingrédient" dans une étape peut désigner un ingrédient qui existe déjà en
// base mais pas encore dans cette recette : on l'ajoute alors automatiquement à la liste
// (voir CooklangStepInput.vue), pour éviter à l'utilisateur de le rechercher deux fois.
function handleMentionIngredient(ingredient: Ingredient) {
  // Un même ingrédient peut servir dans plusieurs parties (beurre de la pâte et de la garniture) :
  // on n'ajoute une ligne que s'il n'y en a aucune, les suivantes se créent depuis la liste.
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
//
// Erreurs par champ, indexées par l'id de l'input concerné (dans l'ordre d'affichage) : affichées
// sous le champ (aria-invalid + aria-describedby), et le premier champ invalide reçoit le focus à
// la soumission — le message près du bouton Enregistrer ne suffit pas sur un long formulaire.
const fieldErrors = ref<Record<string, string>>({})
// Les erreurs par champ ne s'affichent (et ne se recalculent à chaque modification) qu'après une
// première tentative d'enregistrement, pour ne pas accueillir l'utilisateur avec du rouge.
const showFieldErrors = ref(false)

function collectFieldErrors(): Record<string, string> {
  const errors: Record<string, string> = {}
  if (!form.value.title.trim()) errors.title = t('recipes.missingTitle')
  if (!Number.isFinite(form.value.servings) || form.value.servings < 1) {
    errors.servings = t('recipes.invalidServings')
  }
  if (!Number.isFinite(form.value.prep_time_minutes) || form.value.prep_time_minutes < 0) {
    errors.prep = t('recipes.invalidPrepTime')
  }
  if (!Number.isFinite(form.value.cook_time_minutes) || form.value.cook_time_minutes < 0) {
    errors.cook = t('recipes.invalidCookTime')
  }
  ingredientRows.value.forEach((row, index) => {
    if (!row.ingredient) errors[`ingredient-${index}`] = t('recipes.missingIngredient')
    const numeric = Number(row.quantity)
    if (row.quantity === '' || row.quantity === null || !Number.isFinite(numeric) || numeric < 0) {
      errors[`quantity-${index}`] = t('recipes.invalidQuantity')
    }
  })
  return errors
}

watch(
  [form, ingredientRows],
  () => {
    if (showFieldErrors.value) fieldErrors.value = collectFieldErrors()
  },
  { deep: true },
)

// Message récapitulatif affiché près du bouton Enregistrer : la première erreur de champ, sinon
// une erreur globale (étapes non réécrites, crédit d'image, échec de l'enregistrement...).
const summaryError = computed(() => Object.values(fieldErrors.value)[0] || error.value)

function fieldErrorId(field: string) {
  return `${field}-error`
}

function focusField(field: string) {
  const el = document.getElementById(field)
  if (!el) return
  el.scrollIntoView?.({ behavior: 'smooth', block: 'center' })
  el.focus({ preventScroll: true })
}

function validateForm(): string {
  showFieldErrors.value = true
  fieldErrors.value = collectFieldErrors()
  const [firstField, firstMessage] = Object.entries(fieldErrors.value)[0] ?? []
  if (firstField) {
    nextTick(() => focusField(firstField))
    return firstMessage
  }
  if (
    form.value.content_publicly_licensed &&
    stepRows.value.some((step) => step.instruction.trim() && importedStepTexts.value.has(step.instruction.trim()))
  ) {
    return t('recipes.stepsNotRewritten')
  }
  return ''
}

async function handleSubmit() {
  error.value = ''
  // Les erreurs de champ s'affichent sous chaque champ (et dans `summaryError`) : `error` ne
  // porte que les erreurs globales.
  const validationError = validateForm()
  if (validationError) {
    if (!Object.keys(fieldErrors.value).length) error.value = validationError
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
    cookware_ids: selectedCookware.value.map((item) => item.id),
    // Les lignes ajoutées par une mention dans une étape arrivent en fin de liste, hors section :
    // on regroupe par section pour que l'ordre enregistré soit celui qu'on voit à l'écran.
    ingredients: orderRowsBySection(ingredientRows.value).map((row) => ({
      ingredient_id: (row.ingredient as Ingredient).id,
      quantity: row.quantity,
      unit: row.unit,
      group_name: row.group_name,
      order: row.order,
      alternatives: (row.alternatives ?? []).map((alternative, index) => ({
        ingredient_id: alternative.ingredient?.id ?? null,
        quantity: alternative.quantity,
        unit: alternative.unit,
        tag: alternative.tag,
        note: alternative.note,
        order: index,
      })),
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

function handleCancel() {
  if (isEditing && props.id) router.push({ name: 'recipe-detail', params: { id: props.id } })
  else router.push({ name: 'recipes' })
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
        <input id="cooklang-title" v-model="cooklangForm.title" :placeholder="$t('recipes.cooklangFromMetadata')" />
      </div>
      <div class="field" style="width: 140px">
        <label for="cooklang-servings">{{ $t('planning.servings') }}</label>
        <input
          id="cooklang-servings"
          v-model.number="cooklangForm.servings"
          type="number"
          min="1"
          :placeholder="$t('recipes.cooklangFromMetadata')"
        />
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
          <input
            id="title"
            v-model="form.title"
            required
            :aria-invalid="fieldErrors.title ? 'true' : undefined"
            :aria-describedby="fieldErrors.title ? fieldErrorId('title') : undefined"
          />
          <p v-if="fieldErrors.title" :id="fieldErrorId('title')" class="field-error">{{ fieldErrors.title }}</p>
        </div>
        <div class="field">
          <label for="description">{{ $t('recipes.description') }}</label>
          <textarea id="description" v-model="form.description" rows="3" />
        </div>
        <div class="row">
          <div class="field">
            <label for="servings">{{ $t('planning.servings') }}</label>
            <input
              id="servings"
              v-model.number="form.servings"
              type="number"
              min="1"
              required
              :aria-invalid="fieldErrors.servings ? 'true' : undefined"
              :aria-describedby="fieldErrors.servings ? fieldErrorId('servings') : undefined"
            />
            <p v-if="fieldErrors.servings" :id="fieldErrorId('servings')" class="field-error">{{ fieldErrors.servings }}</p>
          </div>
          <div class="field">
            <label for="prep">{{ $t('recipes.prepTime') }}</label>
            <input
              id="prep"
              v-model.number="form.prep_time_minutes"
              type="number"
              min="0"
              required
              :aria-invalid="fieldErrors.prep ? 'true' : undefined"
              :aria-describedby="fieldErrors.prep ? fieldErrorId('prep') : undefined"
            />
            <p v-if="fieldErrors.prep" :id="fieldErrorId('prep')" class="field-error">{{ fieldErrors.prep }}</p>
          </div>
          <div class="field">
            <label for="cook">{{ $t('recipes.cookTime') }}</label>
            <input
              id="cook"
              v-model.number="form.cook_time_minutes"
              type="number"
              min="0"
              required
              :aria-invalid="fieldErrors.cook ? 'true' : undefined"
              :aria-describedby="fieldErrors.cook ? fieldErrorId('cook') : undefined"
            />
            <p v-if="fieldErrors.cook" :id="fieldErrorId('cook')" class="field-error">{{ fieldErrors.cook }}</p>
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
        <IngredientSections v-model="ingredientRows" :field-errors="fieldErrors" />
      </div>

      <div class="card" style="margin-top: 1rem">
        <h2>{{ $t('cookware.title') }}</h2>
        <div class="field">
          <label for="cookware">{{ $t('cookware.label') }}</label>
          <CookwarePicker id="cookware" ref="cookwarePickerRef" v-model="selectedCookware" />
        </div>
        <div v-if="unmatchedCookwareNames.length" class="unmatched-cookware">
          <span class="not-found-badge">{{ $t('cookware.importNotFound') }}</span>
          <button
            v-for="name in unmatchedCookwareNames"
            :key="name"
            type="button"
            class="secondary"
            @click="createUnmatchedCookware(name)"
          >
            <Plus :size="14" />{{ $t('ingredientPicker.create', { name }) }}
          </button>
        </div>
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
                :cookware-names="knownCookwareNames"
                @add-ingredient="handleMentionIngredient"
                @add-cookware="handleMentionCookware"
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
        <button type="button" class="secondary free-images-button" @click="showFreeImages = true">
          <ImageIcon :size="16" />{{ $t('freeImages.open') }}
        </button>
        <FreeImageSuggestions
          v-if="showFreeImages"
          :initial-query="form.title"
          @select="applyFreeImage"
          @close="showFreeImages = false"
        />
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
        <div v-if="form.source_url" class="public-license-hint" role="note">
          <Info :size="18" />
          <p>{{ $t('recipes.publicLicenseHint') }}</p>
        </div>
        <div v-if="form.source_url && form.content_publicly_licensed" class="copyright-notice" role="note">
          <p class="copyright-notice-title"><Scale :size="18" />{{ $t('recipes.copyrightNoticeTitle') }}</p>
          <ul>
            <li>{{ $t('recipes.copyrightNoticeFacts') }}</li>
            <li>{{ $t('recipes.copyrightNoticeText') }}</li>
            <li>{{ $t('recipes.copyrightNoticeImage') }}</li>
          </ul>
        </div>
      </div>

      <!-- Barre d'enregistrement collée en bas de l'écran tant que le formulaire est visible : le
           formulaire est long, on ne doit pas avoir à le redescendre en entier pour enregistrer.
           Bouton Enregistrer unique (pas de doublon en haut de page). -->
      <div class="form-actions">
        <p v-if="summaryError" class="error" role="alert">{{ summaryError }}</p>
        <div class="form-actions-buttons">
          <button type="button" class="secondary" @click="handleCancel">{{ $t('common.cancel') }}</button>
          <button type="submit" :disabled="isSubmitting">{{ $t('common.save') }}</button>
        </div>
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

.step-row:not(:last-child) {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
}

.step-image-field {
  margin-top: 0.5rem;
}

.free-images-button {
  margin-bottom: 0.75rem;
}

.public-license-hint {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-top: 0.5rem;
  padding: 0.85rem 1rem;
  /* Gris neutre (les jetons --color-surface-muted/--color-border sont teintés chauds), dérivé de la
     surface pour rester lisible en thème sombre. */
  border: 1px solid color-mix(in srgb, #808080 22%, var(--color-surface));
  border-radius: 0;
  background: color-mix(in srgb, #808080 9%, var(--color-surface));
  color: var(--color-muted);
}

.public-license-hint svg {
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.public-license-hint p {
  margin: 0;
}

.copyright-notice {
  margin-top: 0.5rem;
  padding: 0.85rem 1rem;
  border: 1px solid var(--color-primary-soft);
  border-radius: 0;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.copyright-notice-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.35rem;
  font-weight: 700;
}

.copyright-notice ul {
  margin: 0;
  padding-left: 1.25rem;
}

.unmatched-cookware {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}

.unmatched-cookware .not-found-badge {
  margin-top: 0;
}

.field-error {
  margin: 0.3rem 0 0;
  color: var(--color-danger);
  font-size: 0.85rem;
}

.field input[aria-invalid='true'],
.invalid :deep(input) {
  border-color: var(--color-danger);
}

.form-actions {
  position: sticky;
  bottom: 0.75rem;
  /* Sous les listes d'auto-complétion du formulaire (.suggestions-dropdown, z-index 10). */
  z-index: 5;
  margin: 1rem 0 0;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0;
  background: var(--color-surface);
  box-shadow: var(--shadow-card);
}

.form-actions .error {
  margin: 0 0 0.5rem;
}

.form-actions-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

/* Mobile : la barre d'onglets (NavBar.vue, .tabbar) est fixée en bas de l'écran ; la barre
   d'enregistrement se colle juste au-dessus plutôt que dessous. */
@media (max-width: 600px) {
  .form-actions {
    bottom: calc(4rem + env(safe-area-inset-bottom, 0px));
  }

  .form-actions-buttons button {
    flex: 1;
  }
}

.not-found-badge {
  display: inline-block;
  margin-top: 0.35rem;
  padding: 0.2rem 0.55rem;
  border-radius: 0;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  font-size: 0.75rem;
  font-weight: 600;
}
</style>
