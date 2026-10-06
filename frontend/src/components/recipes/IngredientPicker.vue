<script setup lang="ts">
import { Pencil } from '@lucide/vue'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import IngredientEditModal from './IngredientEditModal.vue'
import UnverifiedBadge from '../shared/UnverifiedBadge.vue'
import { useDebouncedSearch } from '../../composables/useDebouncedSearch'
import { listIngredients } from '../../api/ingredients'
import type { Ingredient } from '../../types/models'

const { t } = useI18n()

const props = defineProps<{
  modelValue?: Ingredient | null
  id?: string
  // Simple choix dans la bibliothèque, sans création ni modification (ex. cible d'une fusion).
  selectOnly?: boolean
}>()
const emit = defineEmits<{
  // `null` : l'ingrédient choisi vient d'être supprimé par son auteur.
  'update:modelValue': [ingredient: Ingredient | null]
}>()

const query = ref(props.modelValue?.name ?? '')
const { results: suggestions, search, cancel, clear } = useDebouncedSearch<Ingredient>(
  async (value) => (await listIngredients({ search: value })).results,
)
const isOpen = ref(false)

// `query` n'est initialisé qu'une fois à partir de `modelValue` : si le parent remplace la
// valeur après coup (ex. RecipeFormView qui charge la recette de manière asynchrone en mode
// édition), il faut resynchroniser l'affichage nous-mêmes.
watch(
  () => props.modelValue,
  (value) => {
    query.value = value?.name ?? ''
  },
)

// La recherche n'est déclenchée que par une saisie de l'utilisateur (événement `input`), pas par
// un changement programmatique de `query` (sélection, resynchronisation depuis le parent) : sinon
// la liste se rouvrirait juste après la sélection.
const activeIndex = ref(-1)

function onInput() {
  activeIndex.value = -1
  const value = query.value
  if (!value) {
    clear()
    isOpen.value = false
    return
  }
  isOpen.value = true
  search(value)
}

function close() {
  cancel()
  isOpen.value = false
  activeIndex.value = -1
}

function select(ingredient: Ingredient) {
  query.value = ingredient.name
  suggestions.value = []
  close()
  emit('update:modelValue', ingredient)
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    if (isOpen.value) {
      event.preventDefault()
      close()
    }
    return
  }
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    if (!isOpen.value || !suggestions.value.length) return
    event.preventDefault()
    const count = suggestions.value.length
    const delta = event.key === 'ArrowDown' ? 1 : -1
    activeIndex.value = (activeIndex.value + delta + count) % count
    return
  }
  if (event.key === 'Enter' && isOpen.value && activeIndex.value >= 0) {
    event.preventDefault()
    select(suggestions.value[activeIndex.value])
  }
}

const showCreateModal = ref(false)

function openCreateModal() {
  isOpen.value = false
  showCreateModal.value = true
}

function handleIngredientCreated(ingredient: Ingredient) {
  showCreateModal.value = false
  select(ingredient)
}

function closeSoon() {
  setTimeout(close, 150)
}

const exactMatch = () =>
  suggestions.value.some((i) => i.name.toLowerCase() === query.value.toLowerCase())

// Ingrédient choisi, tant que le champ affiche encore son nom (pas pendant une nouvelle saisie) :
// pastille « Non vérifié » et, si l'API l'autorise (`can_edit` : son auteur tant qu'il n'est pas
// vérifié, ou un admin), bouton pour le corriger ou le supprimer sans quitter la recette.
const selected = computed(() =>
  props.modelValue && props.modelValue.name === query.value ? props.modelValue : null,
)
const showEditModal = ref(false)

function handleIngredientUpdated(ingredient: Ingredient) {
  showEditModal.value = false
  query.value = ingredient.name
  emit('update:modelValue', ingredient)
}

function handleIngredientDeleted() {
  showEditModal.value = false
  query.value = ''
  emit('update:modelValue', null)
}

// Pastille « Non vérifié » et/ou bouton Modifier : affichés *dans* le champ (à droite), pour que
// la ligne d'ingrédient du formulaire de recette reste sur une seule ligne.
const hasMeta = computed(
  () => !!selected.value && (selected.value.is_verified === false || (selected.value.can_edit && !props.selectOnly)),
)
</script>

<template>
  <div class="picker">
    <input
      :id="id"
      v-model="query"
      :class="{ 'has-meta': hasMeta }"
      type="text"
      :placeholder="t('ingredientPicker.placeholder')"
      autocomplete="off"
      @input="onInput"
      @keydown="onKeydown"
      @blur="closeSoon"
    />
    <ul v-if="isOpen && query" class="suggestions-dropdown">
      <li
        v-for="(ingredient, i) in suggestions"
        :key="ingredient.id"
        :class="{ active: i === activeIndex }"
        @mousedown.prevent="select(ingredient)">
        {{ ingredient.name }}
        <UnverifiedBadge v-if="ingredient.is_verified === false" />
      </li>
      <li v-if="!selectOnly && !exactMatch()" class="create" @mousedown.prevent="openCreateModal">
        {{ t('ingredientPicker.create', { name: query }) }}
      </li>
    </ul>

    <div v-if="hasMeta && selected" class="picker-meta">
      <UnverifiedBadge v-if="selected.is_verified === false" />
      <button
        v-if="selected.can_edit && !selectOnly"
        type="button"
        class="secondary btn-sm picker-edit"
        :title="t('common.edit')"
        data-testid="ingredient-picker-edit"
        :aria-label="t('ingredientPicker.editLabel', { name: selected.name })"
        @click="showEditModal = true"
      >
        <Pencil :size="14" aria-hidden="true" />
      </button>
    </div>

    <IngredientEditModal
      v-if="showCreateModal"
      :initial-name="query"
      @created="handleIngredientCreated"
      @close="showCreateModal = false"
    />
    <IngredientEditModal
      v-if="showEditModal && selected"
      :ingredient="selected"
      deletable
      @updated="handleIngredientUpdated"
      @deleted="handleIngredientDeleted"
      @close="showEditModal = false"
    />
  </div>
</template>

<style scoped>
.picker {
  position: relative;
}

.picker input {
  width: 100%;
  box-sizing: border-box;
}

.picker-meta {
  position: absolute;
  top: 50%;
  right: 0.4rem;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

/* Réserve la place de la pastille / du bouton pour que le texte du champ ne passe pas dessous. */
input.has-meta {
  padding-right: 3rem;
}

.picker-edit {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 32px;
  min-height: 32px;
  padding: 0;
}
</style>
