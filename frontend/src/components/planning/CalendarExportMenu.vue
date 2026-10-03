<script setup lang="ts">
import { CalendarPlus } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useClickOutside } from '../../composables/useClickOutside'
import { useCopyFeedback } from '../../composables/useCopyFeedback'
import { downloadWeekIcs, getCalendarFeed, regenerateCalendarFeed } from '../../api/planning'
import type { CalendarFeed } from '../../api/planning'
import { downloadBlob } from '../../utils/download'
import type { MealPlanEntryListParams } from '../../types/api'

const props = defineProps<{ params: MealPlanEntryListParams }>()

const { t } = useI18n()
const open = ref(false)
const feed = ref<CalendarFeed | null>(null)
const error = ref(false)
const root = ref<HTMLElement | null>(null)
const { copied, copy } = useCopyFeedback()

useClickOutside(
  root,
  () => {
    open.value = false
  },
  { event: 'mousedown' },
)

const googleUrl = computed(() =>
  feed.value ? `https://calendar.google.com/calendar/render?cid=${encodeURIComponent(feed.value.webcal_url)}` : '',
)

async function toggle() {
  open.value = !open.value
  if (open.value && !feed.value) {
    try {
      feed.value = await getCalendarFeed()
      error.value = false
    } catch {
      error.value = true
    }
  }
}

async function handleDownload() {
  const blob = await downloadWeekIcs(props.params)
  downloadBlob(blob, `agenda-${props.params.date_after}-${props.params.date_before}.ics`)
}

async function handleCopy() {
  if (!feed.value) return
  await copy(feed.value.url)
}

async function handleRegenerate() {
  if (!window.confirm(t('calendarExport.regenerateConfirm'))) return
  feed.value = await regenerateCalendarFeed()
}
</script>

<template>
  <div ref="root" class="calendar-export">
    <button class="secondary" type="button" :aria-expanded="open" @click="toggle">
      <CalendarPlus :size="16" />{{ $t('calendarExport.button') }}
    </button>
    <div v-if="open" class="menu" role="menu">
      <button class="secondary" type="button" role="menuitem" @click="handleDownload">
        {{ $t('calendarExport.downloadIcs') }}
      </button>
      <p v-if="error" class="hint">{{ $t('calendarExport.error') }}</p>
      <template v-else-if="feed">
        <strong class="label">{{ $t('calendarExport.subscription') }}</strong>
        <button class="secondary" type="button" role="menuitem" @click="handleCopy">
          {{ copied ? $t('calendarExport.copied') : $t('calendarExport.copyUrl') }}
        </button>
        <a class="google" :href="googleUrl" target="_blank" rel="noopener" role="menuitem">
          <svg class="google-logo" viewBox="0 0 48 48" width="18" height="18" aria-hidden="true" focusable="false">
            <path fill="#fff" d="M13 13h22v22H13z" />
            <path fill="#1e88e5" d="M13 5h22v8H13z" />
            <path fill="#1565c0" d="M5 13h8v22H9a4 4 0 0 1-4-4z" />
            <path fill="#fbc02d" d="M13 35h22v8H13z" />
            <path fill="#4caf50" d="M35 35h8v4a4 4 0 0 1-4 4h-4z" />
            <path fill="#e53935" d="M35 35h8l-8 8z" />
            <path fill="#1e88e5" d="M35 13V9a4 4 0 0 1 4-4h0a4 4 0 0 1 4 4v4z" />
            <path fill="#1e88e5" d="M35 13h8v22h-8z" />
            <path fill="#1e88e5" d="M13 5H9a4 4 0 0 0-4 4v4h8z" />
            <path fill="#1e88e5" d="M25.6 30c-.9-.6-1.500-1.500-1.900-2.700l2.100-.9c.2.6.5 1.100.9 1.400.4.300.9.500 1.500.500s1.100-.2 1.500-.5.6-.8.6-1.300-.2-1-.6-1.300-1-.5-1.700-.5h-1.200v-2.100h1.100c.6 0 1.100-.1 1.500-.4s.6-.7.6-1.200-.2-.9-.5-1.100-.8-.4-1.300-.4-.9.100-1.200.4-.5.600-.7 1l-2.100-.9c.3-.8.800-1.400 1.500-1.900s1.600-.8 2.700-.8c1 0 1.800.2 2.400.6.700.4 1.200 1 1.500 1.600.3.700.5 1.400.5 2.200s-.2 1.600-.7 2.200-1 1-1.600 1.200v.1c.7.3 1.300.7 1.700 1.300s.7 1.400.7 2.200-.2 1.600-.7 2.300-1.100 1.200-1.900 1.500-1.700.6-2.600.6c-1.100 0-2-.3-2.800-.8z" />
          </svg>
          <span>{{ $t('calendarExport.addToGoogle') }}</span>
        </a>
        <button class="secondary" type="button" role="menuitem" @click="handleRegenerate">
          {{ $t('calendarExport.regenerate') }}
        </button>
        <p class="hint">{{ $t('calendarExport.secretHint') }}</p>
      </template>
    </div>
  </div>
</template>

<style scoped>
.calendar-export {
  position: relative;
  display: inline-block;
}

.menu {
  position: absolute;
  right: 0;
  bottom: 100%;
  margin-bottom: 0.4rem;
  z-index: 10;
  min-width: 17rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.75rem;
  background: var(--color-surface, #fff);
  border: 1px solid var(--color-border, #ddd);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgb(0 0 0 / 15%);
}

.label {
  font-size: 0.85rem;
  margin-top: 0.25rem;
}

.hint {
  margin: 0;
  font-size: 0.8rem;
  opacity: 0.75;
}

.google {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  padding: 0.5rem 0.9rem;
  background: #fff;
  color: #3c4043;
  border: 1px solid #dadce0;
  border-radius: 4px;
  font-family: 'Google Sans', Roboto, Arial, sans-serif;
  font-size: 0.875rem;
  font-weight: 500;
  text-decoration: none;
}

.google:hover {
  background: #f8f9fa;
  border-color: #d2e3fc;
}

.google-logo {
  flex-shrink: 0;
}
</style>
