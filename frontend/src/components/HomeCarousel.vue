<script setup lang="ts">
import { ref } from 'vue'
import { formatDuration } from '../utils/format'
import type { Recipe } from '../types/models'

defineProps<{ recipes: Recipe[] }>()

const track = ref<HTMLElement | null>(null)
const active = ref(0)

function onScroll() {
  const el = track.value
  if (!el || !el.children.length) return
  const edge = el.scrollLeft
  let best = 0
  let bestDistance = Infinity
  Array.from(el.children as HTMLCollectionOf<HTMLElement>).forEach((child, index) => {
    const distance = Math.abs(child.offsetLeft - edge)
    if (distance < bestDistance) {
      best = index
      bestDistance = distance
    }
  })
  // En fin de piste, le dernier slide ne peut pas atteindre le bord gauche : on l'active quand même.
  const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - 2
  active.value = atEnd ? el.children.length - 1 : best
}

function goTo(index: number) {
  const child = track.value?.children[index] as HTMLElement | undefined
  child?.scrollIntoView({ behavior: 'smooth', inline: 'start', block: 'nearest' })
}
</script>

<template>
  <div class="hero-carousel">
    <div ref="track" class="track" tabindex="0" :aria-label="$t('home.latestRecipes')" @scroll.passive="onScroll">
      <RouterLink
        v-for="recipe in recipes"
        :key="recipe.id"
        :to="{ name: 'recipe-detail', params: { id: recipe.id } }"
        class="carousel-slide"
      >
        <img v-if="recipe.image || recipe.image_url" :src="recipe.image || recipe.image_url" alt="" />
        <div class="scrim" />
        <div class="caption">
          <h2>{{ recipe.title }}</h2>
          <p>{{ $t(`diet.${recipe.diet_type}`) }} · {{ formatDuration(recipe.total_time_minutes) }}</p>
        </div>
        <span class="pill">{{ $t('home.viewRecipe') }}</span>
      </RouterLink>
    </div>
    <div class="dots" role="tablist">
      <button
        v-for="(recipe, index) in recipes"
        :key="recipe.id"
        type="button"
        role="tab"
        class="dot"
        :class="{ active: index === active }"
        :aria-selected="index === active"
        :aria-label="recipe.title"
        @click="goTo(index)"
      />
    </div>
  </div>
</template>

<style scoped>
.hero-carousel {
  margin-bottom: 1.5rem;
}

.track {
  position: relative;
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
}

.track::-webkit-scrollbar {
  display: none;
}

.carousel-slide {
  position: relative;
  flex: 0 0 84%;
  aspect-ratio: 16 / 7;
  min-height: 220px;
  scroll-snap-align: start;
  border-radius: 20px;
  overflow: hidden;
  color: #fff;
  text-decoration: none;
  display: block;
  background: linear-gradient(135deg, var(--color-primary), var(--color-primary-dark));
}

.carousel-slide img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scrim {
  position: absolute;
  inset: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.65), rgba(0, 0, 0, 0) 55%);
}

.caption {
  position: absolute;
  left: 1.5rem;
  right: 1.5rem;
  bottom: 4rem;
}

.caption h2 {
  margin: 0 0 0.25rem;
  font-size: clamp(1.5rem, 4vw, 2.75rem);
  letter-spacing: 0.02em;
  color: inherit;
}

.caption p {
  margin: 0;
  opacity: 0.9;
}

.pill {
  position: absolute;
  left: 1.5rem;
  bottom: 1.25rem;
  padding: 0.45rem 1.1rem;
  border-radius: 999px;
  /* Posée sur une photo : toujours blanc sur texte sombre, indépendamment du thème
     (--color-text devient clair en mode sombre et serait illisible sur ce fond). */
  background: #fff;
  color: #241f1d;
  font-weight: 600;
  font-size: 0.9rem;
}

.dots {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
  margin-top: 0.9rem;
}

.dot {
  position: relative;
  width: 8px;
  height: 8px;
  min-height: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: var(--color-border);
  transition: background 0.2s ease;
}

/* Zone de clic élargie sans grossir le point visible. */
.dot::before {
  content: '';
  position: absolute;
  inset: -10px -4px;
}

.dot:hover {
  background: var(--color-muted);
}

.dot:active {
  transform: none;
}

.dot.active {
  background: var(--color-muted);
}

@media (max-width: 600px) {
  .carousel-slide {
    flex-basis: 92%;
    aspect-ratio: 4 / 3;
  }

  .caption {
    bottom: 3.75rem;
  }
}
</style>
