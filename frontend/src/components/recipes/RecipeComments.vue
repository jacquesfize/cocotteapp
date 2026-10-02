<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { createRecipeComment, hideRecipeComment, listRecipeComments } from '../../api/recipes'
import type { RecipeComment } from '../../types/models'

const props = defineProps<{
  recipeId: number | string
  canModerate: boolean
}>()

const { t, locale } = useI18n()

const comments = ref<RecipeComment[]>([])
const isLoading = ref(false)
const loadError = ref('')

const authorName = ref('')
const body = ref('')
const submitError = ref('')
const isSubmitting = ref(false)

async function load() {
  isLoading.value = true
  loadError.value = ''
  try {
    const page = await listRecipeComments(props.recipeId)
    comments.value = page.results
  } catch {
    loadError.value = t('comments.loadError')
  } finally {
    isLoading.value = false
  }
}

onMounted(load)

async function handleSubmit() {
  submitError.value = ''
  isSubmitting.value = true
  try {
    const comment = await createRecipeComment(props.recipeId, {
      author_name: authorName.value.trim() || undefined,
      body: body.value,
    })
    comments.value = [comment, ...comments.value]
    body.value = ''
  } catch {
    submitError.value = t('comments.submitError')
  } finally {
    isSubmitting.value = false
  }
}

async function handleHide(comment: RecipeComment) {
  try {
    const updated = await hideRecipeComment(props.recipeId, comment.id)
    const index = comments.value.findIndex((c) => c.id === comment.id)
    if (index !== -1) {
      comments.value.splice(index, 1, updated)
    }
  } catch {
    submitError.value = t('comments.hideError')
  }
}

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(locale.value, {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}
</script>

<template>
  <div class="card" style="margin-top: 1rem">
    <h2>{{ $t('comments.title') }}</h2>

    <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>
    <p v-else-if="loadError" class="error">{{ loadError }}</p>
    <p v-else-if="!comments.length" class="muted">{{ $t('comments.empty') }}</p>
    <ul v-else class="comment-list">
      <li v-for="comment in comments" :key="comment.id" class="comment">
        <div class="row comment-header">
          <strong>{{ comment.author_name }}</strong>
          <span class="muted">{{ formatDate(comment.created_at) }}</span>
          <span v-if="comment.is_hidden" class="muted">({{ $t('comments.hiddenBadge') }})</span>
        </div>
        <p class="comment-body">{{ comment.body }}</p>
        <button v-if="canModerate" class="secondary" type="button" @click="handleHide(comment)">
          {{ comment.is_hidden ? $t('comments.unhide') : $t('comments.hide') }}
        </button>
      </li>
    </ul>

    <form class="comment-form" @submit.prevent="handleSubmit">
      <h3>{{ $t('comments.addTitle') }}</h3>
      <div class="field">
        <label for="comment-author-name">{{ $t('comments.name') }}</label>
        <input
          id="comment-author-name"
          v-model="authorName"
          type="text"
          maxlength="80"
          :placeholder="$t('comments.namePlaceholder')"
        />
      </div>
      <div class="field">
        <label for="comment-body">{{ $t('comments.comment') }}</label>
        <textarea
          id="comment-body"
          v-model="body"
          required
          maxlength="2000"
          rows="3"
          :placeholder="$t('comments.commentPlaceholder')"
        />
      </div>
      <p v-if="submitError" class="error">{{ submitError }}</p>
      <button type="submit" :disabled="isSubmitting">{{ $t('comments.submit') }}</button>
    </form>
  </div>
</template>

<style scoped>
.comment-list {
  list-style: none;
  margin: 0 0 1rem;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.comment {
  border-bottom: 1px solid var(--color-border, #e5e5e5);
  padding-bottom: 0.75rem;
}

.comment-header {
  align-items: baseline;
  gap: 0.5rem;
}

.comment-body {
  margin: 0.25rem 0 0.5rem;
  white-space: pre-wrap;
}

.comment-form {
  border-top: 1px solid var(--color-border, #e5e5e5);
  padding-top: 1rem;
}
</style>
