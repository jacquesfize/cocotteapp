<script setup lang="ts">
import { AtSign, CookingPot, TriangleAlert, Timer } from '@lucide/vue'
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import IngredientEditModal from './IngredientEditModal.vue'
import { useDebouncedSearch } from '../../composables/useDebouncedSearch'
import { createCookware, listCookware } from '../../api/cookware'
import { listIngredients } from '../../api/ingredients'
import {
  findOrphanCookwareMentions,
  findOrphanMentions,
  toCookwareToken,
  toMentionToken,
} from '../../utils/cooklangMentions'
import type { Cookware, Ingredient } from '../../types/models'

const { t } = useI18n()

const props = defineProps<{
  modelValue: string
  ingredientNames: string[]
  // Matériel déjà sélectionné pour la recette (mentions "#matériel").
  cookwareNames?: string[]
  id?: string
}>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
  'add-ingredient': [ingredient: Ingredient]
  'add-cookware': [cookware: Cookware]
}>()

// "@" mentionne un ingrédient, "#" un matériel : même mécanique d'auto-complétion, seules la
// source des suggestions et la création à la volée changent.
type MentionKind = 'ingredient' | 'cookware'

const textareaEl = ref<HTMLTextAreaElement | null>(null)
const isOpen = ref(false)
const mentionStart = ref<number | null>(null)
const mentionQuery = ref('')
const mentionKind = ref<MentionKind>('ingredient')
const showCreateModal = ref(false)
const createError = ref('')
const { results: dbSuggestions, search, cancel } = useDebouncedSearch<Ingredient | Cookware>(
  async (value) => {
    const query = value.replace(/_/g, ' ')
    if (mentionKind.value === 'cookware') return listCookware(query ? { search: query } : {})
    return (await listIngredients({ search: query })).results
  },
  { onResults: () => { isOpen.value = true } },
)

// Ce qui suit le "@" tel que l'utilisateur le tape (underscores compris), converti en nom
// lisible pour la recherche et l'affichage — ex. "creme_fraiche" -> "creme fraiche".
const mentionQueryDisplay = computed(() => mentionQuery.value.replace(/_/g, ' '))

const exactMatch = computed(() =>
  dbSuggestions.value.some((i) => i.name.toLowerCase() === mentionQueryDisplay.value.toLowerCase()),
)

// Position (du "@" ou du "#") de la mention en cours de saisie, curseur encore dessus : on ne
// l'avertit pas comme inconnue tant que l'utilisateur n'a pas fini de la taper (ex. "@len" en
// route vers "@lentilles"). Remise à null dès que le curseur quitte le mot (espace, ponctuation,
// clic ailleurs), à la sélection d'une suggestion ou à la perte du focus.
const pendingMentionStart = ref<number | null>(null)

const orphanMentions = computed(() =>
  findOrphanMentions(props.modelValue, props.ingredientNames).filter(
    (mention) => mention.start !== pendingMentionStart.value,
  ),
)
const orphanCookware = computed(() =>
  findOrphanCookwareMentions(props.modelValue, props.cookwareNames ?? []).filter(
    (mention) => mention.start !== pendingMentionStart.value,
  ),
)

// Navigation clavier dans la liste : les suggestions puis, le cas échéant, l'option "Créer…".
const listboxId = computed(() => `${props.id ?? 'cooklang-step'}-suggestions`)
const activeIndex = ref(0)
const showCreateOption = computed(() => !exactMatch.value && Boolean(mentionQueryDisplay.value.trim()))
const optionCount = computed(() => dbSuggestions.value.length + (showCreateOption.value ? 1 : 0))
const activeOptionId = computed(() =>
  isOpen.value && optionCount.value ? `${listboxId.value}-${activeIndex.value}` : undefined,
)

watch([isOpen, dbSuggestions], () => {
  activeIndex.value = 0
})

watch([mentionQuery, mentionKind], ([value]) => {
  if (!value) {
    cancel()
    dbSuggestions.value = []
    isOpen.value = false
    return
  }
  search(value)
})

function detectMention(text: string, cursor: number) {
  const upToCursor = text.slice(0, cursor)
  const at = Math.max(upToCursor.lastIndexOf('@'), upToCursor.lastIndexOf('#'))
  if (at === -1) return null
  const between = upToCursor.slice(at + 1)
  if (/\s/.test(between)) return null
  const kind: MentionKind = upToCursor[at] === '#' ? 'cookware' : 'ingredient'
  // "étape #2" n'est pas une mention de matériel (cf. COOKWARE_RE dans cooklangMentions.ts).
  if (kind === 'cookware' && /^\d/.test(between)) return null
  return { start: at, query: between, kind }
}

// Ferme la liste et oublie la mention en cours : annule aussi une recherche encore en attente,
// qui sinon pourrait se résoudre après coup et rouvrir la liste (via `onResults`) alors que
// l'utilisateur a déjà tapé un espace et continue sa phrase.
function closeSuggestions() {
  cancel()
  isOpen.value = false
  pendingMentionStart.value = null
  // Sans cette remise à zéro, retaper la même mention plus loin ne relancerait pas la recherche
  // (le `watch` sur `mentionQuery` ne se déclencherait pas, la valeur n'ayant pas changé).
  mentionQuery.value = ''
}

function handleInput(event: Event) {
  const target = event.target as HTMLTextAreaElement
  emit('update:modelValue', target.value)

  const mention = detectMention(target.value, target.selectionStart)
  if (mention) {
    mentionStart.value = mention.start
    mentionKind.value = mention.kind
    mentionQuery.value = mention.query
    pendingMentionStart.value = mention.start
  } else {
    closeSuggestions()
  }
}

// Le curseur a bougé sans frappe (clic, flèches gauche/droite...) : s'il a quitté la mention en
// cours, elle est considérée comme terminée (et avertie si inconnue).
function syncCaret() {
  const el = textareaEl.value
  if (!el || pendingMentionStart.value === null) return
  const mention = detectMention(el.value, el.selectionStart)
  if (!mention || mention.start !== pendingMentionStart.value) closeSuggestions()
}

function selectActiveOption() {
  const index = activeIndex.value
  if (index < dbSuggestions.value.length) selectSuggestion(dbSuggestions.value[index])
  else openCreateModal()
}

function handleKeydown(event: KeyboardEvent) {
  if (event.isComposing) return
  if (!isOpen.value || !optionCount.value) {
    if (event.key === 'Escape' && isOpen.value) closeSuggestions()
    return
  }
  switch (event.key) {
    case 'ArrowDown':
      event.preventDefault()
      activeIndex.value = (activeIndex.value + 1) % optionCount.value
      break
    case 'ArrowUp':
      event.preventDefault()
      activeIndex.value = (activeIndex.value - 1 + optionCount.value) % optionCount.value
      break
    case 'Enter':
      // Shift+Entrée garde un retour à la ligne.
      if (event.shiftKey) return
      event.preventDefault()
      selectActiveOption()
      break
    case 'Tab':
      // Tab complète avec une suggestion, mais n'ouvre jamais la création d'ingrédient (ni ne
      // retient le focus) : sinon, la liste ferme et la navigation clavier reprend normalement.
      if (!event.shiftKey && activeIndex.value < dbSuggestions.value.length) {
        event.preventDefault()
        selectActiveOption()
      } else {
        closeSuggestions()
      }
      break
    case 'Escape':
      // Ne ferme que la liste (pas une éventuelle modale parente) ; la mention tapée reste telle
      // quelle et sera avertie si elle ne correspond à aucun ingrédient de la recette.
      event.preventDefault()
      event.stopPropagation()
      closeSuggestions()
      break
  }
}

// Remplace la mention en cours de saisie (de "@" jusqu'au curseur) par le token complet,
// sans dépendre de la position du curseur au moment de l'appel (le focus a pu bouger
// entre-temps, ex. le temps de remplir la modale de création d'ingrédient).
function insertToken(name: string) {
  if (mentionStart.value === null) return
  const start = mentionStart.value
  const end = start + 1 + mentionQuery.value.length
  const toToken = mentionKind.value === 'cookware' ? toCookwareToken : toMentionToken
  const token = `${toToken(name)} `
  const next = props.modelValue.slice(0, start) + token + props.modelValue.slice(end)
  emit('update:modelValue', next)
  // Annule une recherche en cours (lancée par la frappe précédente, pas encore résolue) : sinon
  // elle peut se résoudre après la sélection et rouvrir le menu via `onResults`, reproduisant le
  // même bug que la réouverture pilotée par un `watch` sur une resélection programmatique.
  closeSuggestions()

  const caret = start + token.length
  nextTick(() => {
    textareaEl.value?.focus()
    textareaEl.value?.setSelectionRange(caret, caret)
  })
}

function selectSuggestion(item: Ingredient | Cookware) {
  insertToken(item.name)
  const known = mentionKind.value === 'cookware' ? (props.cookwareNames ?? []) : props.ingredientNames
  const alreadyInRecipe = known.some((name) => name.toLowerCase() === item.name.toLowerCase())
  if (alreadyInRecipe) return
  if (mentionKind.value === 'cookware') emit('add-cookware', item as Cookware)
  else emit('add-ingredient', item as Ingredient)
}

async function openCreateModal() {
  cancel()
  isOpen.value = false
  createError.value = ''
  if (mentionKind.value === 'ingredient') {
    showCreateModal.value = true
    return
  }
  // Un matériel n'a qu'un nom : créé directement, sans formulaire.
  try {
    const cookware = await createCookware({ name: mentionQueryDisplay.value.trim() })
    insertToken(cookware.name)
    emit('add-cookware', cookware)
  } catch {
    createError.value = t('cookware.createError')
  }
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

async function insertMentionTemplate(kind: MentionKind = 'ingredient') {
  const at = insertAtCursor(kind === 'cookware' ? '#' : '@')
  mentionStart.value = at
  mentionKind.value = kind
  mentionQuery.value = ''
  pendingMentionStart.value = at
  await nextTick()
  cancel()
  dbSuggestions.value =
    kind === 'cookware' ? await listCookware() : (await listIngredients({ search: '' })).results
  isOpen.value = true
}

// Même syntaxe que cooklangTimers.ts : ~{quantité%unité}, "minutes" fait partie des unités reconnues.
const TIMER_TEMPLATE = '~{10%minutes}'

function insertTimerTemplate() {
  cancel()
  isOpen.value = false
  insertAtCursor(TIMER_TEMPLATE, [2, 4])
}

function closeSoon() {
  setTimeout(() => {
    // La modale de création d'ingrédient prend le focus : la mention reste « en cours » jusqu'à
    // l'insertion du nom créé (ou la fermeture de la modale).
    if (showCreateModal.value) return
    closeSuggestions()
  }, 150)
}

function closeCreateModal() {
  showCreateModal.value = false
  pendingMentionStart.value = null
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
        aria-autocomplete="list"
        :aria-expanded="isOpen"
        :aria-controls="isOpen ? listboxId : undefined"
        :aria-activedescendant="activeOptionId"
        @input="handleInput"
        @keydown="handleKeydown"
        @keyup="syncCaret"
        @click="syncCaret"
        @blur="closeSoon"
      />
      <div class="templates">
        <button
          type="button"
          class="secondary template-btn"
          data-testid="insert-ingredient"
          @mousedown.prevent
          @click="insertMentionTemplate('ingredient')"
        >
          <AtSign :size="14" />{{ t('recipes.insertIngredient') }}
        </button>
        <button
          type="button"
          class="secondary template-btn"
          data-testid="insert-cookware"
          @mousedown.prevent
          @click="insertMentionTemplate('cookware')"
        >
          <CookingPot :size="14" />{{ t('recipes.insertCookware') }}
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
    <ul v-if="isOpen" :id="listboxId" class="suggestions-dropdown" role="listbox">
      <li
        v-for="(item, index) in dbSuggestions"
        :id="`${listboxId}-${index}`"
        :key="item.id"
        role="option"
        :aria-selected="index === activeIndex"
        :class="{ active: index === activeIndex }"
        @mousedown.prevent="selectSuggestion(item)"
        @mouseenter="activeIndex = index"
      >
        {{ item.name }}
      </li>
      <li
        v-if="showCreateOption"
        :id="`${listboxId}-${dbSuggestions.length}`"
        role="option"
        :aria-selected="activeIndex === dbSuggestions.length"
        class="create"
        :class="{ active: activeIndex === dbSuggestions.length }"
        @mousedown.prevent="openCreateModal"
        @mouseenter="activeIndex = dbSuggestions.length"
      >
        {{ t('ingredientPicker.create', { name: mentionQueryDisplay }) }}
      </li>
    </ul>
    <p v-for="mention in orphanMentions" :key="mention.start" class="mention-warning">
      <TriangleAlert :size="14" />
      {{ t('recipes.mentionOrphan', { name: mention.displayName }) }}
    </p>
    <p v-for="mention in orphanCookware" :key="`cookware-${mention.start}`" class="mention-warning">
      <TriangleAlert :size="14" />
      {{ t('recipes.cookwareMentionOrphan', { name: mention.displayName }) }}
    </p>
    <p v-if="createError" class="mention-warning" role="alert">{{ createError }}</p>

    <IngredientEditModal
      v-if="showCreateModal"
      :initial-name="mentionQueryDisplay"
      @created="handleIngredientCreated"
      @close="closeCreateModal"
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
