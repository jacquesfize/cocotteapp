<script setup lang="ts">
import { AtSign, TriangleAlert, Timer } from '@lucide/vue'
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import IngredientEditModal from './IngredientEditModal.vue'
import { listIngredients } from '../api/ingredients'
import { findOrphanMentions, toMentionToken } from '../utils/cooklangMentions'
import type { Ingredient } from '../types/models'

const { t } = useI18n()

const props = defineProps<{
  modelValue: string
  ingredientNames: string[]
  id?: string
}>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
  'add-ingredient': [ingredient: Ingredient]
}>()

const textareaEl = ref<HTMLTextAreaElement | null>(null)
const isOpen = ref(false)
const mentionStart = ref<number | null>(null)
const mentionQuery = ref('')
const dbSuggestions = ref<Ingredient[]>([])
const showCreateModal = ref(false)
let debounceTimer: ReturnType<typeof setTimeout> | undefined

// Ce qui suit le "@" tel que l'utilisateur le tape (underscores compris), converti en nom
// lisible pour la recherche et l'affichage — ex. "creme_fraiche" -> "creme fraiche".
const mentionQueryDisplay = computed(() => mentionQuery.value.replace(/_/g, ' '))

const exactMatch = computed(() =>
  dbSuggestions.value.some((i) => i.name.toLowerCase() === mentionQueryDisplay.value.toLowerCase()),
)

const orphanMentions = computed(() => findOrphanMentions(props.modelValue, props.ingredientNames))

watch(mentionQuery, (value) => {
  clearTimeout(debounceTimer)
  if (!value) {
    dbSuggestions.value = []
    isOpen.value = false
    return
  }
  debounceTimer = setTimeout(async () => {
    const data = await listIngredients({ search: value.replace(/_/g, ' ') })
    dbSuggestions.value = data.results
    isOpen.value = true
  }, 250)
})

function detectMention(text: string, cursor: number) {
  const upToCursor = text.slice(0, cursor)
  const at = upToCursor.lastIndexOf('@')
  if (at === -1) return null
  const between = upToCursor.slice(at + 1)
  if (/\s/.test(between)) return null
  return { start: at, query: between }
}

function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)

  const mention = detectMention(target.value, target.selectionStart)
  if (mention) {
    mentionStart.value = mention.start
    mentionQuery.value = mention.query
  } else {
    isOpen.value = false
  }
}

// Remplace la mention en cours de saisie (de "@" jusqu'au curseur) par le token complet,
// sans dépendre de la position du curseur au moment de l'appel (le focus a pu bouger
// entre-temps, ex. le temps de remplir la modale de création d'ingrédient).
function insertToken(name: string) {
  if (mentionStart.value === null) return
  const start = mentionStart.value
  const end = start + 1 + mentionQuery.value.length
  const token = `${toMentionToken(name)} `
  const next = props.modelValue.slice(0, start) + token + props.modelValue.slice(end)
  emit('update:modelValue', next)
  isOpen.value = false

  const caret = start + token.length
  nextTick(() => {
    textareaEl.value?.focus()
    textareaEl.value?.setSelectionRange(caret, caret)
  })
}

function selectSuggestion(ingredient: Ingredient) {
  insertToken(ingredient.name)
  const alreadyInRecipe = props.ingredientNames.some(
    (name) => name.toLowerCase() === ingredient.name.toLowerCase(),
  )
  if (!alreadyInRecipe) {
    emit('add-ingredient', ingredient)
  }
}

function openCreateModal() {
  isOpen.value = false
  showCreateModal.value = true
}

function handleIngredientCreated(ingredient: Ingredient) {
  showCreateModal.value = false
  insertToken(ingredient.name)
  emit('add-ingredient', ingredient)
}

// Insère `text` à la position du curseur (ou remplace la sélection) et redonne le focus au
// textarea ; `select` ([début, fin] relatifs à `text`) permet de présélectionner une partie.
function insertAtCursor(text: string, select?: [number, number]) {
  const el = textareaEl.value
  const value = props.modelValue
  const from = el?.selectionStart ?? value.length
  const to = el?.selectionEnd ?? value.length
  emit('update:modelValue', value.slice(0, from) + text + value.slice(to))
  const [selStart, selEnd] = select ?? [text.length, text.length]
  nextTick(() => {
    textareaEl.value?.focus()
    textareaEl.value?.setSelectionRange(from + selStart, from + selEnd)
  })
  return from
}

async function insertMentionTemplate() {
  const at = insertAtCursor('@')
  mentionStart.value = at
  mentionQuery.value = ''
  await nextTick()
  clearTimeout(debounceTimer)
  const data = await listIngredients({ search: '' })
  dbSuggestions.value = data.results
  isOpen.value = true
}

// Même syntaxe que cooklangTimers.ts : ~{quantité%unité}, "minutes" fait partie des unités reconnues.
const TIMER_TEMPLATE = '~{10%minutes}'

function insertTimerTemplate() {
  isOpen.value = false
  insertAtCursor(TIMER_TEMPLATE, [2, 4])
}

function closeSoon() {
  setTimeout(() => {
    isOpen.value = false
  }, 150)
}
</script>

<template>
  <div class="cooklang-input">
    <div class="input-row">
      <textarea
        :id="id"
        ref="textareaEl"
        :value="modelValue"
        rows="2"
        :placeholder="t('recipes.stepPlaceholder')"
        @input="handleInput"
        @blur="closeSoon"
      />
      <div class="templates">
        <button
          type="button"
          class="secondary template-btn"
          data-testid="insert-ingredient"
          @mousedown.prevent
          @click="insertMentionTemplate"
        >
          <AtSign :size="14" />{{ t('recipes.insertIngredient') }}
        </button>
        <button
          type="button"
          class="secondary template-btn"
          data-testid="insert-timer"
          @mousedown.prevent
          @click="insertTimerTemplate"
        >
          <Timer :size="14" />{{ t('recipes.insertTimer') }}
        </button>
      </div>
    </div>
    <ul v-if="isOpen" class="suggestions-dropdown">
      <li
        v-for="ingredient in dbSuggestions"
        :key="ingredient.id"
        @mousedown.prevent="selectSuggestion(ingredient)"
      >
        {{ ingredient.name }}
      </li>
      <li v-if="!exactMatch" class="create" @mousedown.prevent="openCreateModal">
        {{ t('ingredientPicker.create', { name: mentionQueryDisplay }) }}
      </li>
    </ul>
    <p v-for="mention in orphanMentions" :key="mention.start" class="mention-warning">
      <TriangleAlert :size="14" />
      {{ t('recipes.mentionOrphan', { name: mention.displayName }) }}
    </p>

    <IngredientEditModal
      v-if="showCreateModal"
      :initial-name="mentionQueryDisplay"
      @created="handleIngredientCreated"
      @close="showCreateModal = false"
    />
  </div>
</template>

<style scoped>
.cooklang-input {
  position: relative;
  width: 100%;
  min-width: 0;
}

.input-row {
  display: flex;
  align-items: stretch;
  gap: 0.5rem;
}

.input-row textarea {
  flex: 1 1 auto;
  min-width: 0;
  width: auto;
}

.templates {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  flex: none;
}

.template-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  min-height: auto;
  padding: 0.3rem 0.6rem;
  font-size: 0.85rem;
  white-space: nowrap;
}

@media (max-width: 480px) {
  .input-row {
    flex-direction: column;
  }

  .templates {
    flex-direction: row;
  }
}

.mention-warning {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
  color: var(--color-danger);
}
</style>
