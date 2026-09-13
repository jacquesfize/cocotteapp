<script setup lang="ts">
import { Pause, Play, RotateCcw, Timer } from '@lucide/vue'
import { computed, onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { formatDuration } from '../utils/format'

const props = defineProps<{
  /** Durée du minuteur en secondes */
  seconds: number
  /** Nom optionnel du minuteur (ex. "repos"), affiché à côté du décompte */
  label?: string
}>()

const { t } = useI18n()

type TimerPhase = 'idle' | 'running' | 'paused' | 'finished'

const phase = ref<TimerPhase>('idle')
const remainingSeconds = ref(Math.round(props.seconds))
let intervalId: ReturnType<typeof setInterval> | undefined

const durationLabel = computed(() => formatDuration(Math.round(props.seconds / 60)))

const clockLabel = computed(() => {
  const total = Math.max(0, remainingSeconds.value)
  const m = Math.floor(total / 60)
  const s = total % 60
  return `${m}:${String(s).padStart(2, '0')}`
})

function stopInterval() {
  if (intervalId !== undefined) {
    clearInterval(intervalId)
    intervalId = undefined
  }
}

function tick() {
  if (remainingSeconds.value <= 1) {
    remainingSeconds.value = 0
    stopInterval()
    phase.value = 'finished'
    playChime()
    return
  }
  remainingSeconds.value -= 1
}

function start() {
  stopInterval()
  phase.value = 'running'
  intervalId = setInterval(tick, 1000)
}

function pause() {
  stopInterval()
  phase.value = 'paused'
}

function reset() {
  stopInterval()
  phase.value = 'idle'
  remainingSeconds.value = Math.round(props.seconds)
}

// Petit carillon généré à la volée (pas de fichier audio à charger) ; l'AudioContext doit
// être créé après une interaction utilisateur (politique navigateur), ce qui est le cas ici
// puisque le décompte n'a pu démarrer que via un clic sur le bouton.
function playChime() {
  try {
    const AudioContextCtor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    if (!AudioContextCtor) return
    const ctx = new AudioContextCtor()
    const now = ctx.currentTime
    ;[0, 0.3, 0.6].forEach((offset) => {
      const oscillator = ctx.createOscillator()
      const gain = ctx.createGain()
      oscillator.type = 'sine'
      oscillator.frequency.value = 880
      gain.gain.setValueAtTime(0.0001, now + offset)
      gain.gain.exponentialRampToValueAtTime(0.3, now + offset + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, now + offset + 0.25)
      oscillator.connect(gain).connect(ctx.destination)
      oscillator.start(now + offset)
      oscillator.stop(now + offset + 0.3)
    })
  } catch {
    // Web Audio indisponible ou bloqué par le navigateur : l'état visuel "terminé" suffit.
  }
}

onBeforeUnmount(stopInterval)
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
  color: #fff;
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
