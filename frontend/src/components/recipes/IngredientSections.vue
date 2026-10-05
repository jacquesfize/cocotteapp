<script setup lang="ts">
import { Pencil, Plus, Trash2 } from '@lucide/vue'
import { nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseModal from '../shared/BaseModal.vue'
import IngredientPicker from './IngredientPicker.vue'
import { formatQuantity, formatUnit } from '../../utils/format'
import { orderRowsBySection, sectionNamesOf } from '../../utils/ingredientSections'
import { INGREDIENT_UNITS } from '../../types/recipeForm'
import type { IngredientFormRow } from '../../types/recipeForm'
import type { Ingredient, Unit } from '../../types/models'

// Ingrédients d'une recette, rangés en sections (blocs bordés). Chaque ingrédient s'ajoute ou se
// modifie dans une modale ; les lignes déjà saisies s'affichent en liste compacte. Une section
// n'existe côté données que par le `group_name` de ses lignes : la section sans nom ('') est
// toujours là, les autres se créent ici. Le parent garde la liste à plat (`v-model`) et la
// validation (erreurs indexées par position de ligne, voir RecipeFormView.collectFieldErrors).
const props = defineProps<{
  modelValue: IngredientFormRow[]
  fieldErrors: Record<string, string>
}>()
const emit = defineEmits<{ 'update:modelValue': [rows: IngredientFormRow[]] }>()
const { t } = useI18n()

interface Section {
  key: number
  // null : section créée mais pas encore nommée (elle ne peut recevoir aucune ligne).
  name: string | null
  // Valeur en cours de saisie dans le champ de nom ; `name` n'est mis à jour que si elle est valide.
  draft: string
  error: string
}

let nextKey = 1
const sections = ref<Section[]>([{ key: 0, name: '', draft: '', error: '' }])

// Les lignes peuvent arriver d'ailleurs (chargement d'une recette, import, mention dans une
// étape) : on aligne les sections sur elles.
watch(
  () => props.modelValue.map((row) => row.group_name),
  () => {
    const rows = props.modelValue
    const first = sections.value[0]
    // Section de départ encore vide et sans nom : elle prend le nom de la première section des
    // lignes reçues (sinon elle resterait en tête, vide, devant les vraies sections).
    if (sections.value.length === 1 && first.name === '' && rows.length && !rows.some((row) => row.group_name === '')) {
      first.name = first.draft = rows[0].group_name
    }
    // Une ligne sans section (ajoutée par une mention dans une étape) rejoint la première section
    // quand celle-ci porte un nom et qu'aucune autre n'est sans nom.
    if (first.name && !sections.value.some((section) => section.name === '') && rows.some((row) => row.group_name === '')) {
      commit(rows.map((row) => (row.group_name === '' ? { ...row, group_name: first.name as string } : row)))
      return
    }
    for (const name of sectionNamesOf(rows)) {
      if (!sections.value.some((section) => section.name === name)) {
        sections.value.push({ key: nextKey++, name, draft: name, error: '' })
      }
    }
    // Les lignes restent regroupées par section, dans l'ordre des sections (sinon l'ordre
    // enregistré ne serait pas celui de l'écran).
    const names = sections.value.flatMap((section) => (section.name === null ? [] : [section.name]))
    const ordered = orderRowsBySection(rows, names)
    if (ordered.some((row, index) => row.group_name !== rows[index].group_name)) commit(rows)
  },
  { immediate: true },
)

function commit(rows: IngredientFormRow[]) {
  const names = sections.value.flatMap((section) => (section.name === null ? [] : [section.name]))
  emit('update:modelValue', orderRowsBySection(rows, names))
}

function entriesOf(section: Section) {
  return props.modelValue
    .map((row, index) => ({ row, index }))
    .filter((entry) => entry.row.group_name === section.name)
}

function rowName(row: IngredientFormRow) {
  return row.ingredient?.name || row.raw_line || t('recipes.ingredient')
}

// --- Sections ---------------------------------------------------------------------------------

async function addSection() {
  const section: Section = { key: nextKey++, name: null, draft: '', error: '' }
  sections.value.push(section)
  await nextTick()
  document.getElementById(`section-name-${section.key}`)?.focus()
}

function renameSection(section: Section, value: string) {
  section.draft = value
  const name = value.trim()
  // La première section peut rester sans nom ; les autres en ont besoin d'un pour être retrouvées.
  if (!name && section !== sections.value[0]) {
    section.error = t('recipes.sectionNameRequired')
    return
  }
  if (sections.value.some((other) => other !== section && other.name === name)) {
    section.error = t('recipes.sectionNameTaken')
    return
  }
  section.error = ''
  const previous = section.name
  section.name = name
  commit(props.modelValue.map((row) => (row.group_name === previous ? { ...row, group_name: name } : row)))
}

// Un nom invalide n'est jamais appliqué : en quittant le champ, on revient au dernier nom valide.
// Une section neuve qui n'a jamais reçu de nom valide est simplement retirée.
function settleSectionName(section: Section) {
  if (!section.error) return
  if (section.name === null) {
    sections.value = sections.value.filter((other) => other !== section)
    return
  }
  section.draft = section.name
  section.error = ''
}

function isNamed(section: Section) {
  return section.name !== null
}

function removeSection(section: Section) {
  const count = entriesOf(section).length
  if (count && !confirm(t('recipes.removeSectionConfirm', { name: section.name ?? '', count }))) return
  sections.value = sections.value.filter((other) => other !== section)
  commit(props.modelValue.filter((row) => row.group_name !== section.name))
}

// --- Ajout / modification d'un ingrédient (modale) --------------------------------------------

interface Draft {
  ingredient: Ingredient | null
  // `<input type="number">` + v-model renvoie un nombre dès qu'une valeur est saisie ('' sinon).
  quantity: string | number
  unit: Unit
  sectionKey: number
}

const modal = ref<{ mode: 'add' | 'edit'; index: number } | null>(null)
const draft = ref<Draft>({ ingredient: null, quantity: '', unit: 'g', sectionKey: 0 })
const modalErrors = ref<{ ingredient?: string; quantity?: string }>({})
let trigger: HTMLElement | null = null

function sectionByKey(key: number) {
  return sections.value.find((section) => section.key === key) ?? sections.value[0]
}

async function openAdd(section: Section) {
  trigger = document.activeElement as HTMLElement | null
  draft.value = { ingredient: null, quantity: '', unit: 'g', sectionKey: section.key }
  modalErrors.value = {}
  modal.value = { mode: 'add', index: -1 }
  await focusPicker()
}

async function openEdit(index: number) {
  trigger = document.activeElement as HTMLElement | null
  const row = props.modelValue[index]
  const section = sections.value.find((item) => item.name === row.group_name) ?? sections.value[0]
  draft.value = {
    ingredient: row.ingredient,
    quantity: row.quantity === null ? '' : String(row.quantity),
    unit: row.unit,
    sectionKey: section.key,
  }
  modalErrors.value = {}
  modal.value = { mode: 'edit', index }
  await focusPicker()
}

async function focusPicker() {
  await nextTick()
  document.getElementById('row-modal-ingredient')?.focus()
}

function closeModal() {
  modal.value = null
  // Le déclencheur peut avoir disparu (ligne supprimée) : on ne redonne le focus que s'il existe encore.
  nextTick(() => {
    if (trigger?.isConnected) trigger.focus()
    trigger = null
  })
}

// Choisir un ingrédient propose son unité habituelle, tant qu'on ajoute une ligne neuve.
watch(
  () => draft.value.ingredient,
  (ingredient) => {
    if (ingredient && modal.value?.mode === 'add') draft.value.unit = ingredient.default_unit
  },
)

function validateDraft(): boolean {
  const errors: { ingredient?: string; quantity?: string } = {}
  if (!draft.value.ingredient) errors.ingredient = t('recipes.missingIngredient')
  const numeric = Number(draft.value.quantity)
  if (String(draft.value.quantity).trim() === '' || !Number.isFinite(numeric) || numeric < 0) {
    errors.quantity = t('recipes.invalidQuantity')
  }
  modalErrors.value = errors
  if (errors.ingredient) document.getElementById('row-modal-ingredient')?.focus()
  else if (errors.quantity) document.getElementById('row-modal-quantity')?.focus()
  return !errors.ingredient && !errors.quantity
}

async function confirmModal(keepOpen: boolean) {
  if (!modal.value || !validateDraft()) return
  const section = sectionByKey(draft.value.sectionKey)
  const base = {
    ingredient: draft.value.ingredient,
    quantity: draft.value.quantity,
    unit: draft.value.unit,
    group_name: section.name ?? '',
  }
  if (modal.value.mode === 'edit') {
    const index = modal.value.index
    commit(
      props.modelValue.map((row, i) =>
        // La ligne est désormais rapprochée d'un ingrédient du catalogue : plus de badge « introuvable ».
        i === index ? { ...row, ...base, unmatched: false } : row,
      ),
    )
    closeModal()
    return
  }
  commit([...props.modelValue, { ...base, order: props.modelValue.length + 1 }])
  if (keepOpen) {
    draft.value = { ingredient: null, quantity: '', unit: draft.value.unit, sectionKey: section.key }
    modalErrors.value = {}
    await focusPicker()
  } else {
    closeModal()
  }
}

function removeRow(index: number) {
  commit(props.modelValue.filter((_, i) => i !== index))
}

function errorIds(index: number) {
  return [`ingredient-${index}-error`, `quantity-${index}-error`]
    .filter((id) => props.fieldErrors[id.replace('-error', '')])
    .join(' ')
}
</script>

<template>
  <div class="ingredient-sections">
    <section
      v-for="section in sections"
      :key="section.key"
      class="ingredient-section"
      :aria-labelledby="`section-title-${section.key}`"
    >
      <header v-if="sections.length === 1" class="visually-hidden">
        <h3 :id="`section-title-${section.key}`">{{ $t('recipes.ingredients') }}</h3>
      </header>
      <header v-else class="ingredient-section-header">
        <span :id="`section-title-${section.key}`" class="visually-hidden">{{ $t('recipes.sectionName') }}</span>
        <div class="section-name-field">
          <input
            :id="`section-name-${section.key}`"
            :value="section.draft"
            type="text"
            maxlength="60"
            class="section-name"
            :placeholder="section === sections[0] ? $t('recipes.noSection') : $t('recipes.sectionNamePlaceholder')"
            :aria-label="$t('recipes.sectionName')"
            :aria-invalid="section.error ? 'true' : undefined"
            :aria-describedby="section.error ? `section-name-${section.key}-error` : undefined"
            @input="renameSection(section, ($event.target as HTMLInputElement).value)"
            @blur="settleSectionName(section)"
            @keydown.enter.prevent="($event.target as HTMLInputElement).blur()"
          />
          <p v-if="section.error" :id="`section-name-${section.key}-error`" class="field-error">{{ section.error }}</p>
        </div>
        <button
          type="button"
          class="secondary icon-btn"
          :aria-label="$t('recipes.removeSection', { name: section.draft || $t('recipes.noSection') })"
          @click="removeSection(section)"
        >
          <Trash2 :size="16" />
        </button>
      </header>

      <ul v-if="entriesOf(section).length" class="ingredient-items">
        <li
          v-for="entry in entriesOf(section)"
          :id="`quantity-${entry.index}`"
          :key="entry.index"
          tabindex="-1"
          class="ingredient-item"
          :class="{ invalid: fieldErrors[`ingredient-${entry.index}`] || fieldErrors[`quantity-${entry.index}`] }"
        >
          <span class="ingredient-item-qty">
            <template v-if="entry.row.quantity !== '' && entry.row.quantity !== null">
              {{ formatQuantity(entry.row.quantity, entry.row.unit) }} {{ formatUnit(entry.row.unit, entry.row.quantity) }}
            </template>
            <span v-else class="muted">{{ $t('recipes.quantityToFill') }}</span>
          </span>
          <span class="ingredient-item-name">
            <template v-if="entry.row.ingredient">{{ entry.row.ingredient.name }}</template>
            <template v-else>
              <span class="not-found-badge">{{ $t('recipes.importNotFound') }}</span>
              <template v-if="entry.row.raw_line"> « {{ entry.row.raw_line }} »</template>
            </template>
          </span>
          <button
            :id="`ingredient-${entry.index}`"
            type="button"
            class="secondary icon-btn"
            :aria-label="$t('recipes.editIngredientRow', { name: rowName(entry.row) })"
            :aria-describedby="errorIds(entry.index) || undefined"
            @click="openEdit(entry.index)"
          >
            <Pencil :size="16" />
          </button>
          <button
            type="button"
            class="secondary icon-btn"
            :aria-label="$t('recipes.removeIngredientRow', { name: rowName(entry.row) })"
            @click="removeRow(entry.index)"
          >
            <Trash2 :size="16" />
          </button>
          <p
            v-if="fieldErrors[`ingredient-${entry.index}`]"
            :id="`ingredient-${entry.index}-error`"
            class="field-error ingredient-item-error"
          >
            {{ fieldErrors[`ingredient-${entry.index}`] }}
          </p>
          <p
            v-if="fieldErrors[`quantity-${entry.index}`]"
            :id="`quantity-${entry.index}-error`"
            class="field-error ingredient-item-error"
          >
            {{ fieldErrors[`quantity-${entry.index}`] }}
          </p>
        </li>
      </ul>
      <p v-else class="muted ingredient-section-empty">
        {{ isNamed(section) ? $t('recipes.sectionEmpty') : $t('recipes.sectionNeedsName') }}
      </p>

      <button
        type="button"
        class="secondary ingredient-add"
        :disabled="!isNamed(section) || !!section.error"
        @click="openAdd(section)"
      >
        <Plus :size="16" />{{ $t('recipes.addIngredient') }}
      </button>
    </section>

    <button type="button" class="secondary" @click="addSection">
      <Plus :size="16" />{{ $t('recipes.addSection') }}
    </button>

    <BaseModal
      v-if="modal"
      :title="modal.mode === 'add' ? $t('recipes.addIngredient') : $t('recipes.editIngredientTitle')"
      @close="closeModal"
    >
      <div class="field">
        <label for="row-modal-ingredient">{{ $t('recipes.ingredient') }}</label>
        <IngredientPicker
          id="row-modal-ingredient"
          v-model="draft.ingredient"
          :class="{ invalid: modalErrors.ingredient }"
        />
        <p v-if="modalErrors.ingredient" class="field-error">{{ modalErrors.ingredient }}</p>
      </div>
      <div class="row modal-quantity-row">
        <div class="field">
          <label for="row-modal-quantity">{{ $t('recipes.quantity') }}</label>
          <input
            id="row-modal-quantity"
            v-model="draft.quantity"
            type="number"
            step="any"
            min="0"
            :aria-invalid="modalErrors.quantity ? 'true' : undefined"
            @keydown.enter.prevent="confirmModal(false)"
          />
          <p v-if="modalErrors.quantity" class="field-error">{{ modalErrors.quantity }}</p>
        </div>
        <div class="field">
          <label for="row-modal-unit">{{ $t('recipes.unit') }}</label>
          <select id="row-modal-unit" v-model="draft.unit">
            <option v-for="unit in INGREDIENT_UNITS" :key="unit" :value="unit">{{ formatUnit(unit) }}</option>
          </select>
        </div>
      </div>
      <div v-if="sections.length > 1" class="field">
        <label for="row-modal-section">{{ $t('recipes.sectionLabel') }}</label>
        <select id="row-modal-section" v-model="draft.sectionKey">
          <option
            v-for="section in sections.filter(isNamed)"
            :key="section.key"
            :value="section.key"
          >
            {{ section.name || $t('recipes.noSection') }}
          </option>
        </select>
      </div>
      <div class="row modal-actions">
        <button type="button" class="secondary" @click="closeModal">{{ $t('common.cancel') }}</button>
        <button
          v-if="modal.mode === 'add'"
          type="button"
          class="secondary"
          @click="confirmModal(true)"
        >
          {{ $t('recipes.addAndContinue') }}
        </button>
        <button type="button" @click="confirmModal(false)">
          {{ modal.mode === 'add' ? $t('common.add') : $t('common.save') }}
        </button>
      </div>
    </BaseModal>
  </div>
</template>

<style scoped>
.ingredient-sections {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.75rem;
}

.ingredient-section {
  align-self: stretch;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 14px;
}

.ingredient-section-header {
  align-self: stretch;
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
}

.ingredient-section-header h3 {
  margin: 0;
  font-size: 1rem;
}

.section-name-field {
  flex: 1;
  min-width: 0;
}

.section-name {
  width: 100%;
  box-sizing: border-box;
  font-weight: 600;
}

.ingredient-items {
  align-self: stretch;
  list-style: none;
  margin: 0;
  padding: 0;
}

.ingredient-item {
  display: grid;
  grid-template-columns: 7rem minmax(0, 1fr) auto auto;
  align-items: center;
  gap: 0.5rem;
  padding: 0.35rem 0;
  border-bottom: 1px solid var(--color-border);
}

.ingredient-item:last-child {
  border-bottom: 0;
}

.ingredient-item.invalid {
  padding-left: 0.5rem;
  border-left: 3px solid var(--color-danger);
}

.ingredient-item-qty {
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.ingredient-item-name {
  overflow-wrap: anywhere;
}

.ingredient-item-error {
  grid-column: 1 / -1;
  margin: 0;
}

.ingredient-section-empty {
  margin: 0;
}

.modal-quantity-row > .field {
  flex: 1;
  min-width: 120px;
}

.modal-actions {
  justify-content: flex-end;
  margin-top: 0.5rem;
}

@media (max-width: 640px) {
  /* Quantité et nom restent sur une ligne : le nom passe à la ligne s'il est long. */
  .ingredient-item {
    grid-template-columns: 4.75rem minmax(0, 1fr) auto auto;
  }
}
</style>
