<script setup lang="ts">
import {
  Bold,
  Heading2,
  Heading3,
  ImagePlus,
  Italic,
  Link,
  List,
  ListOrdered,
  Quote,
  Redo2,
  Underline,
  Undo2,
  Utensils,
} from '@lucide/vue'
import Image from '@tiptap/extension-image'
import StarterKit from '@tiptap/starter-kit'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import BaseModal from '../shared/BaseModal.vue'
import RecipePicker from '../recipes/RecipePicker.vue'
import { uploadBlogImage } from '../../api/blog'
import { useEmbedAutoHeight } from '../../composables/useEmbedAutoHeight'
import type { Recipe } from '../../types/models'
import { RecipeEmbed } from './recipeEmbed'

const props = defineProps<{
  modelValue: string
}>()
const emit = defineEmits<{
  'update:modelValue': [html: string]
}>()

const { t } = useI18n()

const showRecipePicker = ref(false)
const imageInput = ref<HTMLInputElement | null>(null)
const editorRoot = ref<HTMLElement | null>(null)
useEmbedAutoHeight(editorRoot)
const isUploading = ref(false)
const uploadError = ref('')

const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)
const recipeShortcutLabel = computed(() => (isMac ? '⌘ ⌥ R' : 'Ctrl+Alt+R'))

const editor = useEditor({
  content: props.modelValue,
  extensions: [
    StarterKit.configure({
      heading: { levels: [2, 3] },
      link: { openOnClick: false, autolink: true },
    }),
    Image,
    RecipeEmbed.configure({
      onRequestInsert: () => {
        showRecipePicker.value = true
      },
    }),
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  },
})

// The form view loads an existing post asynchronously, after the editor is created.
watch(
  () => props.modelValue,
  (value) => {
    if (editor.value && value !== editor.value.getHTML()) {
      editor.value.commands.setContent(value, { emitUpdate: false })
    }
  },
)

onBeforeUnmount(() => editor.value?.destroy())

function setLink() {
  if (!editor.value) return
  const previous = editor.value.getAttributes('link').href as string | undefined
  const url = window.prompt(t('blog.editor.linkPrompt'), previous ?? 'https://')
  if (url === null) return
  if (!url || url === 'https://') {
    editor.value.chain().focus().extendMarkRange('link').unsetLink().run()
    return
  }
  editor.value.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
}

function pickImage() {
  uploadError.value = ''
  imageInput.value?.click()
}

async function handleImageSelected(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || !editor.value) return
  isUploading.value = true
  uploadError.value = ''
  try {
    const uploaded = await uploadBlogImage(file)
    editor.value.chain().focus().setImage({ src: uploaded.image, alt: '' }).run()
  } catch {
    uploadError.value = t('blog.editor.imageUploadError')
  } finally {
    isUploading.value = false
  }
}

function insertRecipe(recipe: Recipe) {
  showRecipePicker.value = false
  editor.value?.chain().focus().insertRecipeEmbed({ recipeId: recipe.id, title: recipe.title }).run()
}

function closeRecipePicker() {
  showRecipePicker.value = false
  editor.value?.commands.focus()
}
</script>

<template>
  <div ref="editorRoot" class="blog-editor">
    <div v-if="editor" class="toolbar" role="toolbar" :aria-label="t('blog.editor.toolbar')">
      <button
        type="button"
        class="secondary icon-btn"
        :class="{ 'is-active': editor.isActive('bold') }"
        :aria-label="t('blog.editor.bold')"
        :title="t('blog.editor.bold')"
        @click="editor.chain().focus().toggleBold().run()"
      >
        <Bold :size="16" />
      </button>
      <button
        type="button"
        class="secondary icon-btn"
        :class="{ 'is-active': editor.isActive('italic') }"
        :aria-label="t('blog.editor.italic')"
        :title="t('blog.editor.italic')"
        @click="editor.chain().focus().toggleItalic().run()"
      >
        <Italic :size="16" />
      </button>
      <button
        type="button"
        class="secondary icon-btn"
        :class="{ 'is-active': editor.isActive('underline') }"
        :aria-label="t('blog.editor.underline')"
        :title="t('blog.editor.underline')"
        @click="editor.chain().focus().toggleUnderline().run()"
      >
        <Underline :size="16" />
      </button>
      <span class="toolbar-separator" />
      <button
        type="button"
        class="secondary icon-btn"
        :class="{ 'is-active': editor.isActive('heading', { level: 2 }) }"
        :aria-label="t('blog.editor.heading2')"
        :title="t('blog.editor.heading2')"
        @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
      >
        <Heading2 :size="16" />
      </button>
      <button
        type="button"
        class="secondary icon-btn"
        :class="{ 'is-active': editor.isActive('heading', { level: 3 }) }"
        :aria-label="t('blog.editor.heading3')"
        :title="t('blog.editor.heading3')"
        @click="editor.chain().focus().toggleHeading({ level: 3 }).run()"
      >
        <Heading3 :size="16" />
      </button>
      <button
        type="button"
        class="secondary icon-btn"
        :class="{ 'is-active': editor.isActive('bulletList') }"
        :aria-label="t('blog.editor.bulletList')"
        :title="t('blog.editor.bulletList')"
        @click="editor.chain().focus().toggleBulletList().run()"
      >
        <List :size="16" />
      </button>
      <button
        type="button"
        class="secondary icon-btn"
        :class="{ 'is-active': editor.isActive('orderedList') }"
        :aria-label="t('blog.editor.orderedList')"
        :title="t('blog.editor.orderedList')"
        @click="editor.chain().focus().toggleOrderedList().run()"
      >
        <ListOrdered :size="16" />
      </button>
      <button
        type="button"
        class="secondary icon-btn"
        :class="{ 'is-active': editor.isActive('blockquote') }"
        :aria-label="t('blog.editor.quote')"
        :title="t('blog.editor.quote')"
        @click="editor.chain().focus().toggleBlockquote().run()"
      >
        <Quote :size="16" />
      </button>
      <span class="toolbar-separator" />
      <button
        type="button"
        class="secondary icon-btn"
        :class="{ 'is-active': editor.isActive('link') }"
        :aria-label="t('blog.editor.link')"
        :title="t('blog.editor.link')"
        @click="setLink"
      >
        <Link :size="16" />
      </button>
      <button
        type="button"
        class="secondary icon-btn"
        :disabled="isUploading"
        :aria-label="t('blog.editor.image')"
        :title="t('blog.editor.image')"
        data-testid="blog-insert-image"
        @click="pickImage"
      >
        <ImagePlus :size="16" />
      </button>
      <button
        type="button"
        class="secondary insert-recipe"
        :title="t('blog.editor.recipeShortcut', { shortcut: recipeShortcutLabel })"
        data-testid="blog-insert-recipe"
        @click="showRecipePicker = true"
      >
        <Utensils :size="16" />
        <span>{{ t('blog.editor.recipe') }}</span>
      </button>
      <span class="toolbar-separator" />
      <button
        type="button"
        class="secondary icon-btn"
        :disabled="!editor.can().undo()"
        :aria-label="t('blog.editor.undo')"
        :title="t('blog.editor.undo')"
        @click="editor.chain().focus().undo().run()"
      >
        <Undo2 :size="16" />
      </button>
      <button
        type="button"
        class="secondary icon-btn"
        :disabled="!editor.can().redo()"
        :aria-label="t('blog.editor.redo')"
        :title="t('blog.editor.redo')"
        @click="editor.chain().focus().redo().run()"
      >
        <Redo2 :size="16" />
      </button>
      <input
        ref="imageInput"
        type="file"
        accept="image/*"
        class="visually-hidden-input"
        tabindex="-1"
        aria-hidden="true"
        @change="handleImageSelected"
      />
    </div>

    <EditorContent :editor="editor" class="blog-editor-content blog-prose" />

    <p class="muted editor-hint">
      {{ t('blog.editor.recipeShortcut', { shortcut: recipeShortcutLabel }) }}
    </p>
    <p v-if="isUploading" class="muted">{{ t('blog.editor.imageUploading') }}</p>
    <p v-if="uploadError" class="error">{{ uploadError }}</p>

    <BaseModal v-if="showRecipePicker" :title="t('blog.editor.recipeModalTitle')" @close="closeRecipePicker">
      <div class="field">
        <label for="blog-recipe-picker">{{ t('blog.editor.recipeModalLabel') }}</label>
        <RecipePicker id="blog-recipe-picker" @update:model-value="insertRecipe" />
      </div>
    </BaseModal>
  </div>
</template>

<style scoped>
.blog-editor {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.3rem;
  padding: 0.4rem;
  border: 1px solid var(--color-border);
  border-radius: 0;
  background: var(--color-surface-muted);
}

.toolbar .is-active {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.toolbar-separator {
  width: 1px;
  align-self: stretch;
  background: var(--color-border);
  margin: 0 0.15rem;
}

.insert-recipe {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}

.visually-hidden-input {
  display: none;
}

.blog-editor-content :deep(.tiptap) {
  min-height: 16rem;
  padding: 0.75rem 1rem;
  border: 1px solid var(--color-border);
  border-radius: 0;
  background: var(--color-surface);
  outline: none;
}

.blog-editor-content :deep(.tiptap:focus) {
  border-color: var(--color-primary);
}

/* The embedded recipe is a live preview: let clicks select the node instead of the iframe. */
.blog-editor-content :deep(iframe[data-cocotte-recipe]) {
  pointer-events: none;
}

.blog-editor-content :deep(.ProseMirror-selectednode) {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.editor-hint {
  margin: 0;
  font-size: 0.8rem;
}
</style>
