<script setup>
import { onMounted, ref } from 'vue'
import RecipeCard from '../components/RecipeCard.vue'
import { listRecipes } from '../api/recipes'
import { listThematicPages } from '../api/thematicPages'

const latestRecipes = ref([])
const thematicPages = ref([])
const isLoading = ref(true)

onMounted(async () => {
  try {
    const [recipesData, pagesData] = await Promise.all([listRecipes(), listThematicPages()])
    latestRecipes.value = recipesData.results.slice(0, 6)
    thematicPages.value = pagesData
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <div>
    <section class="card hero">
      <h1>{{ $t('home.title') }}</h1>
      <p class="muted">{{ $t('home.tagline') }}</p>
      <div class="row">
        <RouterLink :to="{ name: 'recipes' }"><button>{{ $t('home.browseRecipes') }}</button></RouterLink>
        <RouterLink :to="{ name: 'recipe-random' }"><button class="secondary">{{ $t('nav.random') }}</button></RouterLink>
      </div>
    </section>

    <section v-if="thematicPages.length" class="home-section">
      <h2>{{ $t('home.thematicPages') }}</h2>
      <div class="thematic-grid">
        <RouterLink
          v-for="page in thematicPages"
          :key="page.id"
          class="thematic-card card"
          :to="{ name: 'recipes', query: page.filters }"
        >
          <span v-if="page.icon" class="thematic-icon">{{ page.icon }}</span>
          <h3>{{ page.title }}</h3>
          <p v-if="page.description" class="muted">{{ page.description }}</p>
        </RouterLink>
      </div>
    </section>

    <section class="home-section">
      <div class="row page-header">
        <h2>{{ $t('home.latestRecipes') }}</h2>
        <RouterLink :to="{ name: 'recipes' }">{{ $t('home.seeAll') }}</RouterLink>
      </div>
      <p v-if="isLoading" class="muted">{{ $t('common.loading') }}</p>
      <p v-else-if="!latestRecipes.length" class="muted">{{ $t('home.noRecipes') }}</p>
      <RecipeCard v-for="recipe in latestRecipes" :key="recipe.id" :recipe="recipe" />
    </section>
  </div>
</template>

<style scoped>
.hero {
  margin-bottom: 1.5rem;
}

.hero h1 {
  margin-top: 0;
}

.home-section {
  margin-bottom: 2rem;
}

.page-header {
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1rem;
}

.thematic-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1rem;
}

.thematic-card {
  text-decoration: none;
  color: inherit;
  display: block;
}

.thematic-icon {
  font-size: 1.75rem;
  display: block;
  margin-bottom: 0.4rem;
}

.thematic-card h3 {
  margin: 0 0 0.25rem;
}

.thematic-card p {
  margin: 0;
}
</style>
