<script setup lang="ts">
import { Newspaper, PenLine } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter, type LocationQuery, type LocationQueryRaw } from 'vue-router'
import BlogFilters, { type BlogFilterValues } from '../../components/blog/BlogFilters.vue'
import BlogPostCard from '../../components/blog/BlogPostCard.vue'
import AsyncState from '../../components/shared/AsyncState.vue'
import PageHeader from '../../components/shared/PageHeader.vue'
import Pagination from '../../components/shared/Pagination.vue'
import { deleteBlogPost, listBlogPosts } from '../../api/blog'
import { useAuthStore } from '../../stores/auth'
import type { BlogPostListParams } from '../../types/api'
import type { BlogPostSummary } from '../../types/models'

// Same as BlogPostPagination.page_size (apps/blog/pagination.py).
const BLOG_PAGE_SIZE = 10

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const posts = ref<BlogPostSummary[]>([])
const count = ref(0)
const isLoading = ref(true)
const deleteError = ref('')

// Filters and page live in the URL, like the recipe list (RecipeListView.vue): a filtered
// blog list, e.g. one author's posts, is a shareable link.
function filtersFromQuery(query: LocationQuery): BlogFilterValues {
  return {
    search: (query.search as string) || '',
    author: (query.author as string) || '',
  }
}

const filters = ref<BlogFilterValues>(filtersFromQuery(route.query))
const page = ref(Number(route.query.page) || 1)

function queryMatches(current: LocationQuery, next: Record<string, unknown>) {
  const currentKeys = Object.keys(current).filter((key) => current[key] !== undefined && current[key] !== '')
  const nextKeys = Object.keys(next).filter((key) => next[key] !== undefined && next[key] !== '')
  if (currentKeys.length !== nextKeys.length) return false
  return currentKeys.every((key) => String(current[key]) === String(next[key]))
}

async function load() {
  isLoading.value = true
  try {
    const params: BlogPostListParams = {}
    if (filters.value.search) params.search = filters.value.search
    if (filters.value.author) params.author = Number(filters.value.author)
    if (page.value > 1) params.page = page.value
    const data = await listBlogPosts(params)
    posts.value = data.results
    count.value = data.count
    if (!queryMatches(route.query, params as Record<string, unknown>)) {
      router.replace({ query: params as unknown as LocationQueryRaw })
    }
  } finally {
    isLoading.value = false
  }
}

function goToPage(newPage: number) {
  page.value = newPage
  load()
}

let debounceTimer: ReturnType<typeof setTimeout> | undefined
watch(
  filters,
  () => {
    page.value = 1
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(load, 300)
  },
  { deep: true },
)
onBeforeUnmount(() => clearTimeout(debounceTimer))

// An internal link to /blog?author=… while already on the list only changes the query string.
watch(
  () => route.query,
  (query) => {
    const next = filtersFromQuery(query)
    if (next.search !== filters.value.search || next.author !== filters.value.author) filters.value = next
  },
)

onMounted(load)

async function handleDelete(post: BlogPostSummary) {
  if (!confirm(t('blog.deleteNamedConfirm', { title: post.title }))) return
  deleteError.value = ''
  try {
    await deleteBlogPost(post.id)
  } catch {
    deleteError.value = t('blog.deleteError')
    return
  }
  if (posts.value.length === 1 && page.value > 1) page.value -= 1
  await load()
}
</script>

<template>
  <div>
    <div class="row page-header blog-list-header">
      <PageHeader :icon="Newspaper" :title="$t('blog.title')" />
      <button
        v-if="authStore.isAuthenticated"
        type="button"
        class="new-post"
        @click="router.push({ name: 'blog-new' })"
      >
        <PenLine :size="16" />
        <span>{{ $t('blog.newPost') }}</span>
      </button>
    </div>
    <p class="muted intro">{{ $t('blog.intro') }}</p>

    <!-- Desktop : filtres en colonne latérale à gauche ; mobile : au-dessus de la liste. -->
    <div class="blog-layout">
      <BlogFilters v-model="filters" />

      <div class="blog-main">
        <p v-if="deleteError" class="error">{{ deleteError }}</p>
        <AsyncState
          v-if="isLoading || !posts.length"
          :loading="isLoading"
          :loading-text="$t('common.loading')"
          :empty-text="filters.search || filters.author ? $t('blog.noResults') : $t('blog.empty')"
        />
        <div v-else class="blog-posts">
          <BlogPostCard v-for="post in posts" :key="post.id" :post="post" manageable @delete="handleDelete" />
        </div>

        <Pagination :page="page" :count="count" :page-size="BLOG_PAGE_SIZE" @update:page="goToPage" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.blog-list-header {
  justify-content: space-between;
  align-items: center;
}

.new-post {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
}

.intro {
  margin-top: 0;
}

.blog-layout {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  gap: 1.25rem;
  align-items: start;
}

.blog-main {
  min-width: 0;
}

.blog-posts {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

@media (max-width: 600px) {
  .blog-layout {
    display: block;
  }
}
</style>
