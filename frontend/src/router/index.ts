import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
    requiresStaff?: boolean
  }
}

const routes: RouteRecordRaw[] = [
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
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('../views/ForgotPasswordView.vue'),
    meta: { public: true },
  },
  {
    path: '/reset-password/:uid/:token',
    name: 'reset-password',
    component: () => import('../views/ResetPasswordView.vue'),
    props: true,
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
  {
    path: '/account',
    name: 'account',
    component: () => import('../views/AccountSettingsView.vue'),
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: () => import('../views/AdminUsersView.vue'),
    meta: { requiresStaff: true },
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
  // authStore.user peut ne pas encore être chargé juste après un rechargement de page
  // (fetchMe() est asynchrone) : on ne bloque que si l'on sait déjà que ce n'est pas un
  // compte staff, sinon la vue elle-même gère le refus d'accès renvoyé par l'API.
  if (to.meta.requiresStaff && authStore.user && !authStore.user.is_staff) {
    return { name: 'home' }
  }
  return true
})

export default router
