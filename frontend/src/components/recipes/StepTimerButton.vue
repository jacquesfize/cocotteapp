<script setup lang="ts">
import { Pause, Play, RotateCcw, Timer } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import { useStepTimer, type StepTimerHandle } from '../../composables/useStepTimer'

const props = defineProps<{
  /** Durée du minuteur en secondes (ignoré si `handle` est fourni) */
  seconds?: number
  /** Nom optionnel du minuteur (ex. "repos"), affiché à côté du décompte (ignoré si `handle` est fourni) */
  label?: string
  /** Minuteur partagé (créé ailleurs, ex. RecipeCookMode.vue) : permet à cette pastille et à un
   * autre affichage (dock du mode cuisine) de piloter le même décompte plutôt que d'en démarrer
   * un chacun. Sans lui, la pastille crée et possède son propre minuteur, comme avant. */
  handle?: StepTimerHandle
}>()

const { t } = useI18n()

const timer = props.handle ?? useStepTimer(props.seconds ?? 0, props.label)
const { phase, durationLabel, clockLabel, start, pause, reset } = timer
</script>

<template>
  <button
    v-if="phase === 'idle'"
    type="button"
    class="secondary timer-chip"
    :aria-label="t('timer.start', { duration: durationLabel })"
    @click="start"
  >
    <Timer :size="14" />
    <span v-if="label">{{ label }} · </span>{{ durationLabel }}
  </button>
  <span v-else class="timer-chip active" :class="{ finished: phase === 'finished' }" role="timer" aria-live="polite">
    <Timer :size="14" />
    <span v-if="label">{{ label }} · </span>
    <template v-if="phase === 'finished'">{{ t('timer.finished') }}</template>
    <template v-else>{{ clockLabel }}</template>
    <button
      v-if="phase === 'running'"
      type="button"
      class="timer-control"
      :aria-label="t('timer.pause')"
      @click="pause"
    >
      <Pause :size="12" />
    </button>
    <button
      v-else-if="phase === 'paused'"
      type="button"
      class="timer-control"
      :aria-label="t('timer.resume')"
      @click="start"
    >
      <Play :size="12" />
    </button>
    <button type="button" class="timer-control" :aria-label="t('timer.reset')" @click="reset">
      <RotateCcw :size="12" />
    </button>
  </span>
</template>

<style scoped>
.timer-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.15rem 0.6rem;
  min-height: auto;
  font-size: 0.85rem;
  font-weight: 600;
  border-radius: 999px;
  vertical-align: middle;
  margin: 0 0.15rem;
  white-space: nowrap;
}

.timer-chip.active {
  background: var(--color-primary-soft);
  color: var(--color-primary-dark);
}

.timer-chip.finished {
  background: var(--color-primary);
  color: var(--color-on-primary);
  animation: timer-pulse 1s ease-in-out infinite;
}

.timer-control {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.35rem;
  min-height: 1.35rem;
  padding: 0;
  border-radius: 50%;
  background: transparent;
  color: inherit;
}

.timer-control:hover {
  background: rgba(0, 0, 0, 0.08);
}

@keyframes timer-pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}
</style>
