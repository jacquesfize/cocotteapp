<script setup lang="ts">
import { ListFilter, RotateCcw, X } from '@lucide/vue'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import VueMultiselect from 'vue-multiselect'
import 'vue-multiselect/dist/vue-multiselect.css'
import { listBlogAuthors } from '../../api/blog'
import type { BlogAuthor } from '../../types/models'

const { t } = useI18n()

export interface BlogFilterValues {
  search: string
  // Id of the author, as a string (it comes from / goes to the URL query string).
  author: string
}

// Same layout and behaviour as RecipeFilters.vue: a sidebar always shown on desktop, folded
// behind a "Filters" button on mobile, with one removable chip per active filter. The parent
// view keeps the URL in sync and loads the posts.
const filters = defineModel<BlogFilterValues>({ required: true })

const isOpen = ref(false)

const activeCount = computed(() => Object.values(filters.value).filter((value) => value !== '').length)

function reset() {
  filters.value = { search: '', author: '' }
}

const authors = ref<BlogAuthor[]>([])
onMounted(async () => {
  authors.value = await listBlogAuthors().catch(() => [])
})

const selectedAuthor = computed<BlogAuthor | null>({
  get: () => {
    if (!filters.value.author) return null
    const id = Number(filters.value.author)
    return authors.value.find((author) => author.id === id) ?? { id, username: filters.value.author }
  },
  set: (author) => {
    filters.value.author = author ? String(author.id) : ''
  },
})

interface FilterChip {
  id: string
  label: string
  remove: () => void
}

const filterChips = computed<FilterChip[]>(() => {
  const chips: FilterChip[] = []
  if (filters.value.search) {
    chips.push({ id: 'search', label: filters.value.search, remove: () => { filters.value.search = '' } })
  }
  if (selectedAuthor.value) {
    chips.push({
      id: 'author',
      label: t('blog.filters.authorChip', { author: selectedAuthor.value.username }),
      remove: () => { filters.value.author = '' },
    })
  }
  return chips
})
</script>

<template>
  <div class="recipe-filters blog-filters">
    <button
      type="button"
      class="secondary toggle"
      :aria-expanded="isOpen"
      aria-controls="blog-filters-panel"
      @click="isOpen = !isOpen"
    >
      <ListFilter :size="16" />{{ $t('recipes.filters') }}
      <span
        v-if="activeCount"
        class="badge"
        data-testid="filters-badge"
        :aria-label="$t('recipes.activeFilters', { count: activeCount })"
      >{{ activeCount }}</span>
    </button>

    <ul
      v-if="filterChips.length"
      class="active-filters active-filters--mobile"
      :aria-label="$t('recipes.activeFiltersList')"
    >
      <li v-for="chip in filterChips" :key="chip.id">
        <button
          type="button"
          class="filter-chip"
          :aria-label="$t('recipes.removeFilterChip', { label: chip.label })"
          @click="chip.remove"
        >
          {{ chip.label }}
          <X :size="12" aria-hidden="true" />
        </button>
      </li>
    </ul>

    <aside
      id="blog-filters-panel"
      class="card panel"
      :class="{ 'is-open': isOpen }"
      :aria-label="$t('recipes.filters')"
    >
      <div class="panel-header">
        <strong class="panel-title">
          <ListFilter :size="16" aria-hidden="true" />{{ $t('recipes.filters') }}
          <span
            v-if="activeCount"
            class="badge header-badge"
            :aria-label="$t('recipes.activeFilters', { count: activeCount })"
          >{{ activeCount }}</span>
        </strong>
        <button type="button" class="secondary close" :aria-label="$t('common.close')" @click="isOpen = false">
          <X :size="16" />
        </button>
      </div>

      <ul
        v-if="filterChips.length"
        class="active-filters active-filters--desktop"
        :aria-label="$t('recipes.activeFiltersList')"
      >
        <li v-for="chip in filterChips" :key="chip.id">
          <button
            type="button"
            class="filter-chip"
            :aria-label="$t('recipes.removeFilterChip', { label: chip.label })"
            @click="chip.remove"
          >
            {{ chip.label }}
            <X :size="12" aria-hidden="true" />
          </button>
        </li>
      </ul>

      <div class="field">
        <label for="blog-search">{{ $t('blog.filters.search') }}</label>
        <input
          id="blog-search"
          v-model="filters.search"
          type="search"
          :placeholder="$t('blog.filters.searchPlaceholder')"
        />
      </div>

      <div class="field">
        <label for="blog-author">{{ $t('blog.filters.author') }}</label>
        <VueMultiselect
          id="blog-author"
          v-model="selectedAuthor"
          name="author"
          :options="authors"
          track-by="id"
          label="username"
          :show-labels="false"
          :placeholder="$t('blog.filters.allAuthors')"
        >
          <template #noResult>{{ $t('blog.filters.noAuthor') }}</template>
          <template #noOptions>{{ $t('blog.filters.noAuthor') }}</template>
        </VueMultiselect>
      </div>

      <div class="panel-footer">
        <button type="button" class="secondary reset" :disabled="!activeCount" @click="reset">
          <RotateCcw :size="16" />{{ $t('recipes.resetFilters') }}
        </button>
        <button type="button" class="apply" @click="isOpen = false">{{ $t('recipes.showResults') }}</button>
      </div>
    </aside>
  </div>
</template>

<style scoped>
/* Repris de RecipeFilters.vue (même rendu sur la liste des recettes et sur le blog). */
.toggle {
  display: none;
  align-items: center;
  gap: 0.4rem;
}
.badge {
  min-width: 1.35rem;
  height: 1.35rem;
  padding: 0 0.35rem;
  border-radius: 0;
  background: var(--color-primary);
  color: var(--color-on-primary);
  font-size: 0.75rem;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.active-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  padding: 0;
  list-style: none;
}
.active-filters--mobile {
  display: none;
  margin: 0.6rem 0 0;
}
.active-filters--desktop {
  margin: 0 0 1rem;
}
.filter-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  min-height: auto;
  padding: 0.3rem 0.6rem;
  border-radius: 0;
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
  font-size: 0.8rem;
  font-weight: 600;
}
.filter-chip:hover {
  background: var(--color-primary-soft-hover);
}

.panel {
  padding: 1.1rem;
}
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}
.panel-title {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
}
.close,
.apply {
  display: none;
}
.panel-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.25rem;
}
.panel-footer .reset {
  flex: 1;
}

@media (max-width: 600px) {
  .blog-filters {
    margin-bottom: 1rem;
  }
  .toggle {
    display: inline-flex;
  }
  .active-filters--mobile {
    display: flex;
  }
  .active-filters--desktop {
    display: none;
  }
  .panel {
    display: none;
    margin-top: 0.75rem;
  }
  .panel.is-open {
    display: block;
  }
  .header-badge {
    display: none;
  }
  .close,
  .apply {
    display: inline-flex;
  }
  .panel-footer {
    justify-content: space-between;
  }
  .panel-footer .reset {
    flex: 0 1 auto;
  }
}
</style>
