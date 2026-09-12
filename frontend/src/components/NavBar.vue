<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const router = useRouter()

function handleLogout() {
  authStore.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="navbar">
    <div class="container navbar-inner">
      <RouterLink to="/recipes" class="brand">🍲 Recettes</RouterLink>
      <nav v-if="authStore.isAuthenticated" class="links">
        <RouterLink to="/recipes">Recettes</RouterLink>
        <RouterLink to="/planning">Agenda</RouterLink>
        <RouterLink to="/shopping-lists">Courses</RouterLink>
        <span class="muted">{{ authStore.user?.username }}</span>
        <button class="secondary" @click="handleLogout">Déconnexion</button>
      </nav>
      <nav v-else class="links">
        <RouterLink to="/login">Connexion</RouterLink>
        <RouterLink to="/register">Inscription</RouterLink>
      </nav>
    </div>
  </header>
</template>

<style scoped>
.navbar {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.navbar-inner {
  padding-top: 0.75rem;
  padding-bottom: 0.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.brand {
  font-weight: 700;
  text-decoration: none;
  color: var(--color-text);
}

.links {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.links a {
  text-decoration: none;
}

.links a.router-link-active {
  font-weight: 600;
}
</style>
