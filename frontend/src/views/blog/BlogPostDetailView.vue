<script setup lang="ts">
import { Newspaper, Pencil, Trash2 } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import BlogContent from '../../components/blog/BlogContent.vue'
import CommentThread from '../../components/shared/CommentThread.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import {
  createBlogPostComment,
  deleteBlogPost,
  getBlogPost,
  hideBlogPostComment,
  listBlogPostComments,
} from '../../api/blog'
import { usePageTitle } from '../../composables/usePageTitle'
import { useAuthStore } from '../../stores/auth'
import { formatLongDate } from '../../utils/dates'
import type { BlogPost } from '../../types/models'

const props = defineProps<{
  id: string | number
}>()
const { t, locale } = useI18n()
const router = useRouter()
const authStore = useAuthStore()

const post = ref<BlogPost | null>(null)
// Titre de l'onglet : celui de l'article une fois chargé.
usePageTitle(() => post.value?.title)
const loadError = ref('')
const deleteError = ref('')

const isOwner = computed(() => Boolean(authStore.user) && post.value?.author_id === authStore.user?.id)
const canManage = computed(() => isOwner.value || Boolean(authStore.user?.is_staff))
// `updated_at` is bumped on save; only mention it when the post was edited after publication.
const wasEdited = computed(
  () =>
    Boolean(post.value) &&
    new Date(post.value!.updated_at).getTime() - new Date(post.value!.created_at).getTime() > 60_000,
)

onMounted(async () => {
  try {
    post.value = await getBlogPost(props.id)
  } catch {
    loadError.value = t('blog.loadError')
  }
})

async function handleDelete() {
  if (!confirm(t('blog.deleteConfirm'))) return
  deleteError.value = ''
  try {
    await deleteBlogPost(props.id)
    router.push({ name: 'blog' })
  } catch {
    deleteError.value = t('blog.deleteError')
  }
}
</script>

<template>
  <div v-if="post">
    <article class="card blog-post">
      <img v-if="post.cover_image" :src="post.cover_image" alt="" class="blog-post-cover" />
      <PageHeader :icon="Newspaper">{{ post.title }}</PageHeader>
      <p class="muted blog-post-meta">
        {{ $t('blog.byline', { author: post.author, date: formatLongDate(post.created_at, locale) }) }}
        <template v-if="wasEdited">
          · {{ $t('blog.updatedOn', { date: formatLongDate(post.updated_at, locale) }) }}
        </template>
      </p>
      <div v-if="canManage" class="row blog-post-actions">
        <button type="button" class="secondary" @click="router.push({ name: 'blog-edit', params: { id: post.id } })">
          <Pencil :size="16" /><span>{{ $t('common.edit') }}</span>
        </button>
        <button type="button" class="danger" @click="handleDelete">
          <Trash2 :size="16" /><span>{{ $t('common.delete') }}</span>
        </button>
      </div>
      <p v-if="deleteError" class="error">{{ deleteError }}</p>
      <BlogContent :html="post.content" />
    </article>

    <CommentThread
      :key="post.id"
      :load="() => listBlogPostComments(post!.id)"
      :create="(payload) => createBlogPostComment(post!.id, payload)"
      :hide="(commentId) => hideBlogPostComment(post!.id, commentId)"
      :can-moderate="canManage"
      :closed="!post.comments_enabled"
      :placeholder="$t('blog.commentPlaceholder')"
    />
  </div>
  <p v-else-if="loadError" class="error">{{ loadError }}</p>
  <p v-else class="muted">{{ $t('common.loading') }}</p>
</template>

<style scoped>
.blog-post-cover {
  display: block;
  width: calc(100% + 2.5rem);
  max-height: 360px;
  margin: -1.25rem -1.25rem 1rem;
  object-fit: cover;
  border-radius: 0;
}

.blog-post-meta {
  margin-top: -0.5rem;
}

.blog-post-actions {
  margin-bottom: 1rem;
}
</style>
