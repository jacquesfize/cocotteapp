<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

// Dé dessiné sur un <canvas> : il tourne et rebondit tant que `rolling` est vrai, puis se pose
// sur une face au hasard. Le parent décide de la durée (voir RandomRecipeView.vue) ; le dé ne
// fait qu'émettre `roll` au clic.
const props = withDefaults(
  defineProps<{
    label: string
    rolling?: boolean
    size?: 'large' | 'small'
    disabled?: boolean
  }>(),
  { rolling: false, size: 'large', disabled: false },
)

const emit = defineEmits<{ roll: [] }>()

const SIZES = { large: 160, small: 72 }
const FACE_CHANGE_MS = 90
const SETTLE_MS = 250
const QUARTER_TURN = Math.PI / 2

// Position des points de chaque face, sur une grille 3x3 (-1, 0, 1).
const PIPS: Record<number, [number, number][]> = {
  1: [[0, 0]],
  2: [[-1, -1], [1, 1]],
  3: [[-1, -1], [0, 0], [1, 1]],
  4: [[-1, -1], [1, -1], [-1, 1], [1, 1]],
  5: [[-1, -1], [1, -1], [0, 0], [-1, 1], [1, 1]],
  6: [[-1, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [1, 1]],
}

const canvas = ref<HTMLCanvasElement | null>(null)

let ctx: CanvasRenderingContext2D | null = null
let face = 5
let angle = 0
let lift = 0
let frameId: number | null = null

const prefersReducedMotion = () =>
  typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

// Toujours une face différente de la précédente, pour que chaque lancer se voie.
function randomFace() {
  let next = face
  while (next === face) next = 1 + Math.floor(Math.random() * 6)
  return next
}

function cssColor(name: string, fallback: string) {
  if (!canvas.value) return fallback
  return getComputedStyle(canvas.value).getPropertyValue(name).trim() || fallback
}

function draw() {
  if (!ctx || !canvas.value) return
  const px = SIZES[props.size]
  const side = px * 0.56
  const half = side / 2
  const radius = side * 0.18
  const cx = px / 2
  const cy = px * 0.46 - lift * px * 0.06

  ctx.clearRect(0, 0, px, px)

  // Ombre au sol, qui rétrécit quand le dé décolle.
  ctx.fillStyle = 'rgba(0, 0, 0, 0.12)'
  ctx.beginPath()
  ctx.ellipse(cx, px * 0.92, half * (1 - lift * 0.35), px * 0.035, 0, 0, Math.PI * 2)
  ctx.fill()

  ctx.save()
  ctx.translate(cx, cy)
  ctx.rotate(angle)
  ctx.fillStyle = cssColor('--color-primary', '#ff6a3d')
  ctx.beginPath()
  ctx.roundRect(-half, -half, side, side, radius)
  ctx.fill()

  ctx.fillStyle = cssColor('--color-on-primary', '#fff')
  const gap = side * 0.27
  for (const [x, y] of PIPS[face]) {
    ctx.beginPath()
    ctx.arc(x * gap, y * gap, side * 0.085, 0, Math.PI * 2)
    ctx.fill()
  }
  ctx.restore()
}

function stopLoop() {
  if (frameId !== null) cancelAnimationFrame(frameId)
  frameId = null
}

function spin() {
  stopLoop()
  const start = performance.now()
  let lastFaceChange = start
  const tick = (now: number) => {
    const elapsed = now - start
    angle += 0.22
    lift = Math.abs(Math.sin(elapsed / 160))
    if (now - lastFaceChange > FACE_CHANGE_MS) {
      face = randomFace()
      lastFaceChange = now
    }
    draw()
    frameId = requestAnimationFrame(tick)
  }
  frameId = requestAnimationFrame(tick)
}

function settle() {
  stopLoop()
  face = randomFace()
  const fromAngle = angle
  const toAngle = Math.ceil(angle / QUARTER_TURN) * QUARTER_TURN
  const fromLift = lift
  const start = performance.now()
  const tick = (now: number) => {
    const t = Math.min(1, (now - start) / SETTLE_MS)
    const eased = 1 - (1 - t) ** 3
    angle = fromAngle + (toAngle - fromAngle) * eased
    lift = fromLift * (1 - eased)
    draw()
    if (t < 1) frameId = requestAnimationFrame(tick)
    else {
      angle = 0
      frameId = null
    }
  }
  frameId = requestAnimationFrame(tick)
}

function setup() {
  if (!canvas.value) return
  const px = SIZES[props.size]
  const dpr = window.devicePixelRatio || 1
  canvas.value.width = px * dpr
  canvas.value.height = px * dpr
  ctx = canvas.value.getContext('2d')
  ctx?.setTransform(dpr, 0, 0, dpr, 0, 0)
  draw()
}

watch(
  () => props.rolling,
  (rolling) => {
    if (!ctx) return
    if (prefersReducedMotion()) {
      if (!rolling) {
        face = randomFace()
        draw()
      }
      return
    }
    if (rolling) spin()
    else settle()
  },
)

watch(() => props.size, setup)

onMounted(setup)
onBeforeUnmount(stopLoop)
</script>

<template>
  <button
    type="button"
    class="dice"
    :class="size"
    :aria-label="label"
    :title="label"
    :aria-busy="rolling"
    :disabled="disabled"
    @click="emit('roll')"
  >
    <canvas ref="canvas" aria-hidden="true" />
  </button>
</template>

<style scoped>
.dice {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  border: none;
  border-radius: 0;
  background: none;
  cursor: pointer;
  transition: transform 0.15s ease;
}

.dice:hover:not(:disabled) {
  background: none;
  transform: scale(1.05);
}

.dice:disabled {
  cursor: progress;
  opacity: 1;
}

.dice.large canvas {
  width: 160px;
  height: 160px;
}

.dice.small canvas {
  width: 72px;
  height: 72px;
}

@media (prefers-reduced-motion: reduce) {
  .dice {
    transition: none;
  }

  .dice:hover:not(:disabled) {
    transform: none;
  }
}
</style>
