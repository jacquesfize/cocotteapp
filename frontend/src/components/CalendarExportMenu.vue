<script setup lang="ts">
import { CalendarPlus } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { downloadWeekIcs, getCalendarFeed, regenerateCalendarFeed } from '../api/planning'
import type { CalendarFeed } from '../api/planning'
import { downloadBlob } from '../utils/download'
import type { MealPlanEntryListParams } from '../types/api'

const props = defineProps<{ params: MealPlanEntryListParams }>()

const { t } = useI18n()
const open = ref(false)
const feed = ref<CalendarFeed | null>(null)
const error = ref(false)
const copied = ref(false)

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
  await navigator.clipboard.writeText(feed.value.url)
  copied.value = true
  setTimeout(() => (copied.value = false), 2000)
}

async function handleRegenerate() {
  if (!window.confirm(t('calendarExport.regenerateConfirm'))) return
  feed.value = await regenerateCalendarFeed()
}
</script>

<template>
  <div class="calendar-export">
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
          {{ $t('calendarExport.addToGoogle') }}
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
  text-align: center;
  padding: 0.4rem;
}
</style>
