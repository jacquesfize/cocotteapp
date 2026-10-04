import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '../stores/auth'

declare module 'vue-router' {
  interface RouteMeta {
    public?: boolean
    requiresStaff?: boolean
    // Rendered alone (no navbar/footer), to be displayed inside an <iframe>.
    embed?: boolean
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
    component: () => import('../views/auth/AuthView.vue'),
    props: { mode: 'login' },
    meta: { public: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/auth/AuthView.vue'),
    props: { mode: 'register' },
    meta: { public: true },
  },
  {
    path: '/forgot-password',
    name: 'forgot-password',
    component: () => import('../views/auth/ForgotPasswordView.vue'),
    meta: { public: true },
  },
  {
    path: '/reset-password/:uid/:token',
    name: 'reset-password',
    component: () => import('../views/auth/ResetPasswordView.vue'),
    props: true,
    meta: { public: true },
  },
  {
    path: '/recipes',
    name: 'recipes',
    component: () => import('../views/recipes/RecipeListView.vue'),
    meta: { public: true },
  },
  {
    path: '/recipes/new',
    name: 'recipe-new',
    component: () => import('../views/recipes/RecipeFormView.vue'),
  },
  {
    path: '/recipes/random',
    name: 'recipe-random',
    component: () => import('../views/recipes/RandomRecipeView.vue'),
    meta: { public: true },
  },
  {
    path: '/recipes/:id',
    name: 'recipe-detail',
    component: () => import('../views/recipes/RecipeDetailView.vue'),
    props: true,
    meta: { public: true },
  },
  {
    path: '/recipes/:id/edit',
    name: 'recipe-edit',
    component: () => import('../views/recipes/RecipeFormView.vue'),
    props: true,
  },
  {
    path: '/blog',
    name: 'blog',
    component: () => import('../views/blog/BlogListView.vue'),
    meta: { public: true },
  },
  {
    path: '/blog/new',
    name: 'blog-new',
    component: () => import('../views/blog/BlogPostFormView.vue'),
  },
  {
    path: '/blog/:id',
    name: 'blog-detail',
    component: () => import('../views/blog/BlogPostDetailView.vue'),
    props: true,
    meta: { public: true },
  },
  {
    path: '/blog/:id/edit',
    name: 'blog-edit',
    component: () => import('../views/blog/BlogPostFormView.vue'),
    props: true,
  },
  {
    path: '/embed/recipes/:id',
    name: 'recipe-embed',
    component: () => import('../views/embed/RecipeEmbedView.vue'),
    props: true,
    meta: { public: true, embed: true },
  },
  {
    path: '/planning',
    name: 'planning',
    component: () => import('../views/planning/PlanningView.vue'),
  },
  {
    path: '/shopping-lists',
    name: 'shopping-lists',
    component: () => import('../views/shopping/ShoppingListsView.vue'),
  },
  {
    path: '/shopping-lists/:id',
    name: 'shopping-list-detail',
    component: () => import('../views/shopping/ShoppingListDetailView.vue'),
    props: true,
  },
  {
    path: '/account',
    name: 'account',
    component: () => import('../views/account/AccountSettingsView.vue'),
  },
  {
    path: '/tags',
    name: 'personal-tags',
    component: () => import('../views/account/PersonalTagsView.vue'),
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    component: () => import('../views/admin/AdminUsersView.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/admin/thematic-pages',
    name: 'admin-thematic-pages',
    component: () => import('../views/admin/AdminThematicPagesView.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/admin/ingredients',
    name: 'admin-ingredients',
    component: () => import('../views/admin/AdminIngredientsView.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/admin/cookware',
    name: 'admin-cookware',
    component: () => import('../views/admin/AdminCookwareView.vue'),
    meta: { requiresStaff: true },
  },
  {
    path: '/legal',
    name: 'legal',
    component: () => import('../views/LegalView.vue'),
    props: { page: 'legal' },
    meta: { public: true },
  },
  {
    path: '/privacy',
    name: 'privacy',
    component: () => import('../views/LegalView.vue'),
    props: { page: 'privacy' },
    meta: { public: true },
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
