<script setup lang="ts">
import { ImagePlus, Newspaper, ShieldAlert, Trash2 } from '@lucide/vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import BlogEditor from '../../components/blog/BlogEditor.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import { createBlogPost, deleteBlogCover, getBlogPost, updateBlogPost, uploadBlogCover } from '../../api/blog'
import type { BlogPostInput } from '../../types/models'

const props = defineProps<{
  id?: string | number
}>()
const { t } = useI18n()
const router = useRouter()

const isEdit = computed(() => props.id !== undefined)
const form = ref<BlogPostInput>({ title: '', content: '', comments_enabled: true })
// Asked again on every save, edits included: the rules apply to whatever is being published.
const acceptedGuidelines = ref(false)
const error = ref('')
const isSaving = ref(false)

// Cover image: uploaded separately (multipart) once the post itself is saved.
const savedCover = ref<string | null>(null)
const coverFile = ref<File | null>(null)
const coverPreview = ref<string | null>(null)
const coverInput = ref<HTMLInputElement | null>(null)
let previewObjectUrl: string | null = null

function revokePreview() {
  if (previewObjectUrl) URL.revokeObjectURL(previewObjectUrl)
  previewObjectUrl = null
}

function handleCoverSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  revokePreview()
  coverFile.value = file
  previewObjectUrl = URL.createObjectURL(file)
  coverPreview.value = previewObjectUrl
}

function removeCover() {
  revokePreview()
  coverFile.value = null
  coverPreview.value = null
}

onBeforeUnmount(revokePreview)

onMounted(async () => {
  if (!isEdit.value) return
  try {
    const post = await getBlogPost(props.id!)
    form.value = { title: post.title, content: post.content, comments_enabled: post.comments_enabled }
    savedCover.value = post.cover_image
    coverPreview.value = post.cover_image
  } catch {
    error.value = t('blog.loadError')
  }
})

function hasContent(html: string): boolean {
  if (/<(img|iframe)\b/i.test(html)) return true
  return html.replace(/<[^>]*>/g, '').trim().length > 0
}

async function handleSubmit() {
  error.value = ''
  if (!hasContent(form.value.content)) {
    error.value = t('blog.form.emptyContent')
    return
  }
  if (!acceptedGuidelines.value) {
    error.value = t('blog.form.guidelinesRequired')
    return
  }
  isSaving.value = true
  try {
    const saved = isEdit.value
      ? await updateBlogPost(props.id!, form.value)
      : await createBlogPost(form.value)
    if (coverFile.value) {
      await uploadBlogCover(saved.id, coverFile.value)
    } else if (savedCover.value && !coverPreview.value) {
      await deleteBlogCover(saved.id)
    }
    router.push({ name: 'blog-detail', params: { id: saved.id } })
  } catch {
    error.value = t('blog.form.saveError')
  } finally {
    isSaving.value = false
  }
}
</script>

<template>
  <div>
    <PageHeader :icon="Newspaper" :title="isEdit ? $t('blog.form.editTitle') : $t('blog.form.newTitle')" />

    <form class="card" @submit.prevent="handleSubmit">
      <div class="field">
        <label for="blog-title">{{ $t('blog.form.title') }}</label>
        <input id="blog-title" v-model="form.title" type="text" required maxlength="200" />
      </div>

      <div class="field">
        <span class="field-label">{{ $t('blog.form.cover') }}</span>
        <div v-if="coverPreview" class="cover-preview">
          <img :src="coverPreview" alt="" data-testid="blog-cover-preview" />
        </div>
        <div class="row cover-actions">
          <button type="button" class="secondary" @click="coverInput?.click()">
            <ImagePlus :size="16" />{{ coverPreview ? $t('blog.form.changeCover') : $t('blog.form.addCover') }}
          </button>
          <button v-if="coverPreview" type="button" class="secondary" data-testid="blog-cover-remove" @click="removeCover">
            <Trash2 :size="16" />{{ $t('blog.form.removeCover') }}
          </button>
        </div>
        <p class="muted cover-hint">{{ $t('blog.form.coverHint') }}</p>
        <input
          id="blog-cover"
          ref="coverInput"
          type="file"
          accept="image/*"
          class="cover-file-input"
          @change="handleCoverSelected"
        />
      </div>

      <div class="field">
        <label>{{ $t('blog.form.content') }}</label>
        <BlogEditor v-model="form.content" />
      </div>

      <label class="checkbox-row">
        <input id="blog-comments-enabled" v-model="form.comments_enabled" type="checkbox" />
        {{ $t('blog.form.commentsEnabled') }}
      </label>

      <div class="guidelines" role="note" data-testid="blog-guidelines">
        <p class="guidelines-title"><ShieldAlert :size="18" />{{ $t('blog.form.guidelinesTitle') }}</p>
        <ul>
          <li>{{ $t('blog.form.guidelinesRespect') }}</li>
          <li>{{ $t('blog.form.guidelinesCopyright') }}</li>
        </ul>
      </div>
      <label class="checkbox-row">
        <input id="blog-accept-guidelines" v-model="acceptedGuidelines" type="checkbox" />
        {{ $t('blog.form.acceptGuidelines') }}
      </label>

      <p v-if="error" class="error">{{ error }}</p>
      <div class="row form-actions">
        <button type="submit" :disabled="isSaving">{{ $t('blog.form.publish') }}</button>
        <button type="button" class="secondary" @click="router.back()">{{ $t('common.cancel') }}</button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.checkbox-row {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin: 0.5rem 0 0.85rem;
}

.guidelines {
  padding: 0.85rem 1rem;
  border: 1px solid var(--color-primary-soft);
  border-radius: 0;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.guidelines-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0 0 0.35rem;
  font-weight: 700;
}

.guidelines ul {
  margin: 0;
  padding-left: 1.25rem;
}

.field-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--color-muted);
}

.cover-preview img {
  display: block;
  width: 100%;
  max-height: 260px;
  object-fit: cover;
  border-radius: 0;
}

.cover-actions {
  gap: 0.5rem;
}

.cover-hint {
  margin: 0;
  font-size: 0.8rem;
}

.cover-file-input {
  display: none;
}

.form-actions {
  margin-top: 0.5rem;
}
</style>
