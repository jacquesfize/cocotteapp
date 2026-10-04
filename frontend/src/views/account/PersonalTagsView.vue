<script setup lang="ts">
import { Plus, Tags, Trash2 } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import AsyncState from '../../components/shared/AsyncState.vue'
import BaseModal from '../../components/shared/BaseModal.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import PersonalTagChip from '../../components/recipes/PersonalTagChip.vue'
import SimilarTagsHint from '../../components/recipes/SimilarTagsHint.vue'
import TagColorPicker from '../../components/recipes/TagColorPicker.vue'
import {
  createPersonalTag,
  deletePersonalTag,
  findSimilarPersonalTags,
  listPersonalTags,
  updatePersonalTag,
} from '../../api/personalTags'
import { getErrorStatus } from '../../utils/apiError'
import type { PersonalTag, TagColor } from '../../types/models'

const { t } = useI18n()

const tags = ref<PersonalTag[]>([])
const isLoading = ref(false)
const message = ref('')
// Étiquette existante choisie depuis les suggestions « déjà proches » : mise en évidence dans la liste.
const highlightedId = ref<number | null>(null)

async function load() {
  isLoading.value = true
  try {
    tags.value = await listPersonalTags()
  } finally {
    isLoading.value = false
  }
}

onMounted(load)

const showModal = ref(false)
const editing = ref<PersonalTag | null>(null)
const form = ref<{ name: string; emoji: string; color: TagColor }>({ name: '', emoji: '', color: 'gray' })
const formError = ref('')
const isSubmitting = ref(false)
const similar = ref<PersonalTag[]>([])

function openForm(tag: PersonalTag | null) {
  editing.value = tag
  form.value = { name: tag?.name ?? '', emoji: tag?.emoji ?? '', color: tag?.color ?? 'gray' }
  formError.value = ''
  similar.value = []
  showModal.value = true
}

// Suggestions à la frappe : étiquettes existantes proches du nom tapé (hors celle qu'on renomme).
let similarTimer: ReturnType<typeof setTimeout> | undefined
let similarRequest = 0
watch(
  () => form.value.name,
  (name) => {
    clearTimeout(similarTimer)
    const trimmed = name.trim()
    if (!showModal.value || !trimmed || trimmed === editing.value?.name) {
      similar.value = []
      return
    }
    similarTimer = setTimeout(async () => {
      const requestId = ++similarRequest
      const matches = await findSimilarPersonalTags(trimmed, editing.value?.id).catch(() => [])
      if (requestId === similarRequest) similar.value = matches
    }, 300)
  },
)

onBeforeUnmount(() => clearTimeout(similarTimer))

function pickExisting(tag: PersonalTag) {
  showModal.value = false
  highlightedId.value = tag.id
}

async function handleSubmit() {
  formError.value = ''
  const name = form.value.name.trim()
  if (!name) {
    formError.value = t('personalTags.nameRequired')
    return
  }
  isSubmitting.value = true
  try {
    const payload = { name, emoji: form.value.emoji.trim(), color: form.value.color }
    const saved = editing.value ? await updatePersonalTag(editing.value.id, payload) : await createPersonalTag(payload)
    showModal.value = false
    highlightedId.value = saved.id
    await load()
  } catch (err) {
    formError.value = t(getErrorStatus(err) === 400 ? 'personalTags.duplicate' : 'personalTags.saveError')
  } finally {
    isSubmitting.value = false
  }
}

async function handleDelete(tag: PersonalTag) {
  message.value = ''
  if (!confirm(t('personalTags.deleteConfirm', { name: tag.name }))) return
  try {
    await deletePersonalTag(tag.id)
  } catch {
    message.value = t('personalTags.deleteError')
    return
  }
  await load()
}
</script>

<template>
  <div>
    <div class="row page-header">
      <div>
        <PageHeader :icon="Tags" :title="$t('personalTags.title')" />
        <p class="muted">{{ $t('personalTags.subtitle') }}</p>
      </div>
      <button type="button" @click="openForm(null)">
        <Plus :size="16" />{{ $t('personalTags.addButton') }}
      </button>
    </div>

    <p v-if="message" class="error" role="alert">{{ message }}</p>
    <AsyncState
      v-if="isLoading || !tags.length"
      :loading="isLoading"
      :loading-text="$t('common.loading')"
      :empty-text="$t('personalTags.empty')"
    />

    <ul v-else class="card tag-list">
      <li v-for="tag in tags" :key="tag.id" :class="{ 'is-highlighted': tag.id === highlightedId }">
        <PersonalTagChip :tag="tag" class="tag-name" />
        <RouterLink
          :to="{ name: 'recipes', query: { personal_tags: String(tag.id) } }"
          class="recipes-link"
        >
          {{ $t('personalTags.recipesCount', { count: tag.recipes_count ?? 0 }) }}
        </RouterLink>
        <div class="actions">
          <button class="secondary" @click="openForm(tag)">{{ $t('common.edit') }}</button>
          <button
            class="danger icon-btn"
            :aria-label="$t('personalTags.deleteButton', { name: tag.name })"
            @click="handleDelete(tag)"
          >
            <Trash2 :size="16" />
          </button>
        </div>
      </li>
    </ul>

    <BaseModal
      v-if="showModal"
      :title="$t(editing ? 'personalTags.editTitle' : 'personalTags.newTitle')"
      @close="showModal = false"
    >
      <form novalidate @submit.prevent="handleSubmit">
        <div class="row">
          <div class="field" style="flex: 1; min-width: 180px">
            <label for="personal-tag-name">{{ $t('personalTags.name') }}</label>
            <input id="personal-tag-name" v-model="form.name" required maxlength="60" autofocus />
          </div>
          <div class="field" style="width: 100px">
            <label for="personal-tag-emoji">{{ $t('personalTags.emoji') }}</label>
            <input id="personal-tag-emoji" v-model="form.emoji" placeholder="🎂" maxlength="8" />
          </div>
        </div>
        <SimilarTagsHint v-if="similar.length" :tags="similar" @pick="pickExisting" />
        <div class="field">
          <span class="label">{{ $t('personalTags.color') }}</span>
          <TagColorPicker v-model="form.color" name="personal-tag-color" />
        </div>
        <div class="field">
          <span class="label">{{ $t('personalTags.preview') }}</span>
          <div>
            <PersonalTagChip :tag="{ name: form.name.trim() || $t('personalTags.name'), emoji: form.emoji, color: form.color }" />
          </div>
        </div>
        <p v-if="formError" class="error">{{ formError }}</p>
        <div class="row" style="margin-top: 1rem; justify-content: flex-end">
          <button type="button" class="secondary" @click="showModal = false">{{ $t('common.cancel') }}</button>
          <button type="submit" :disabled="isSubmitting">{{ $t('common.save') }}</button>
        </div>
      </form>
    </BaseModal>
  </div>
</template>

<style scoped>
.page-header {
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.tag-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.tag-list li {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
}

.tag-list li:not(:last-child) {
  border-bottom: 1px solid var(--color-border);
}

.tag-list li.is-highlighted {
  background: var(--color-primary-soft);
}

.tag-name {
  font-size: 0.9rem;
}

.recipes-link {
  font-size: 0.9rem;
}

.actions {
  display: flex;
  gap: 0.5rem;
  margin-left: auto;
}

/* Même apparence qu'un `.field label` (base.css), pour les champs sans <input> unique. */
.label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-muted);
}
</style>
