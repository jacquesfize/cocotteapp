import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/',
    name: 'home',
    component: () => import('../views/HomeView.vue'),
    meta: { public: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { public: true },
  },
  {
    path: '/recipes',
    name: 'recipes',
    component: () => import('../views/RecipeListView.vue'),
    meta: { public: true },
  },
  {
    path: '/recipes/new',
    name: 'recipe-new',
    component: () => import('../views/RecipeFormView.vue'),
  },
  {
    path: '/recipes/random',
    name: 'recipe-random',
    component: () => import('../views/RandomRecipeView.vue'),
    meta: { public: true },
  },
  {
    path: '/recipes/:id',
    name: 'recipe-detail',
    component: () => import('../views/RecipeDetailView.vue'),
    props: true,
    meta: { public: true },
  },
  {
    path: '/recipes/:id/edit',
    name: 'recipe-edit',
    component: () => import('../views/RecipeFormView.vue'),
    props: true,
  },
  {
    path: '/planning',
    name: 'planning',
    component: () => import('../views/PlanningView.vue'),
  },
  {
    path: '/shopping-lists',
    name: 'shopping-lists',
    component: () => import('../views/ShoppingListsView.vue'),
  },
  {
    path: '/shopping-lists/:id',
    name: 'shopping-list-detail',
    component: () => import('../views/ShoppingListDetailView.vue'),
    props: true,
  },
  { path: '/:pathMatch(.*)*', redirect: '/recipes' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const authStore = useAuthStore()
  if (!to.meta.public && !authStore.isAuthenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  return true
})

export default router
