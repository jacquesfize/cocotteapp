<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    page: number
    count: number
    pageSize?: number
  }>(),
  { pageSize: 20 },
)
const emit = defineEmits<{
  'update:page': [page: number]
}>()

const totalPages = computed(() => Math.max(1, Math.ceil(props.count / props.pageSize)))
</script>

<template>
  <div v-if="totalPages > 1" class="pagination">
    <button
      class="secondary icon-btn"
      type="button"
      :disabled="page <= 1"
      :aria-label="$t('common.previousPage')"
      @click="emit('update:page', page - 1)"
    >
      <ChevronLeft :size="18" />
    </button>
    <span class="muted">{{ $t('common.pageOf', { page, total: totalPages }) }}</span>
    <button
      class="secondary icon-btn"
      type="button"
      :disabled="page >= totalPages"
      :aria-label="$t('common.nextPage')"
      @click="emit('update:page', page + 1)"
    >
      <ChevronRight :size="18" />
    </button>
  </div>
</template>

<style scoped>
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 1.5rem;
}
</style>
