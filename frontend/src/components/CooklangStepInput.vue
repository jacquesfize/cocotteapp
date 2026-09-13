<script setup lang="ts">
import { TriangleAlert } from '@lucide/vue'
import { computed, nextTick, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { findOrphanMentions, toMentionToken } from '../utils/cooklangMentions'

const { t } = useI18n()

const props = defineProps<{
  modelValue: string
  ingredientNames: string[]
  id?: string
}>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const textareaEl = ref<HTMLTextAreaElement | null>(null)
const isOpen = ref(false)
const mentionStart = ref<number | null>(null)
const mentionQuery = ref('')

const suggestions = computed(() => {
  const query = mentionQuery.value.replace(/_/g, ' ').toLowerCase()
  return props.ingredientNames.filter((name) => name.toLowerCase().includes(query))
})

const orphanMentions = computed(() => findOrphanMentions(props.modelValue, props.ingredientNames))

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
    isOpen.value = true
  } else {
    isOpen.value = false
  }
}

function selectSuggestion(name: string) {
  if (mentionStart.value === null || !textareaEl.value) return
  const text = props.modelValue
  const cursor = textareaEl.value.selectionStart
  const token = `${toMentionToken(name)} `
  const next = text.slice(0, mentionStart.value) + token + text.slice(cursor)
  emit('update:modelValue', next)
  isOpen.value = false

  const caret = mentionStart.value + token.length
  nextTick(() => {
    textareaEl.value?.focus()
    textareaEl.value?.setSelectionRange(caret, caret)
  })
}

function closeSoon() {
  setTimeout(() => {
    isOpen.value = false
  }, 150)
}
</script>

<template>
  <div class="cooklang-input">
    <textarea
      :id="id"
      ref="textareaEl"
      :value="modelValue"
      rows="2"
      :placeholder="t('recipes.stepPlaceholder')"
      @input="handleInput"
      @blur="closeSoon"
    />
    <ul v-if="isOpen && suggestions.length" class="suggestions">
      <li v-for="name in suggestions" :key="name" @mousedown.prevent="selectSuggestion(name)">
        {{ name }}
      </li>
    </ul>
    <p v-for="mention in orphanMentions" :key="mention.start" class="mention-warning">
      <TriangleAlert :size="14" />
      {{ t('recipes.mentionOrphan', { name: mention.displayName }) }}
    </p>
  </div>
</template>

<style scoped>
.cooklang-input {
  position: relative;
}

.suggestions {
  position: absolute;
  z-index: 10;
  top: 100%;
  left: 0;
  right: 0;
  margin: 0.35rem 0 0;
  padding: 0.35rem;
  list-style: none;
  background: var(--color-surface);
  border-radius: 16px;
  box-shadow: var(--shadow-card);
  max-height: 220px;
  overflow-y: auto;
}

.suggestions li {
  padding: 0.5rem 0.7rem;
  border-radius: 10px;
  cursor: pointer;
}

.suggestions li:hover {
  background: var(--color-surface-muted);
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
