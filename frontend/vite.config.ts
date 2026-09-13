import { defineConfig } from 'vitest/config'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    vue(),
    VitePWA({
      registerType: 'autoUpdate',
      // Le service worker tourne aussi en `vite dev`, pour pouvoir tester le mode
      // hors ligne sans build de production (context.setOffline() en e2e, par ex.).
      devOptions: { enabled: true, type: 'module' },
      includeAssets: ['favicon.svg', 'favicon-32.png', 'apple-touch-icon.png'],
      manifest: {
        name: 'Cocotte',
        short_name: 'Cocotte',
        description:
          "Recettes, menus de la semaine et listes de courses — accessibles même hors connexion.",
        lang: 'fr',
        start_url: '/',
        scope: '/',
        display: 'standalone',
        background_color: '#FBF6F3',
        theme_color: '#FF6A3D',
        icons: [
          { src: '/pwa-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/pwa-512.png', sizes: '512x512', type: 'image/png' },
          { src: '/pwa-maskable-512.png', sizes: '512x512', type: 'image/png', purpose: 'maskable' },
        ],
      },
      workbox: {
        // Tout le reste (auth, création/édition, exports PDF/texte) passe en direct au
        // réseau : ne pas mettre en cache des écritures, ni des fichiers volumineux à
        // usage ponctuel.
        runtimeCaching: [
          {
            // Recettes + pages thématiques : données publiques, on privilégie le réseau
            // mais on retombe sur le cache hors ligne.
            urlPattern: ({ url, request }) =>
              request.method === 'GET' &&
              (url.pathname.startsWith('/api/recipes') || url.pathname.startsWith('/api/thematic-pages')) &&
              !url.pathname.endsWith('/pdf/'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'cocotte-recipes',
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 300, maxAgeSeconds: 60 * 60 * 24 * 7 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // Agenda + listes de courses : données propres à l'utilisateur — voir
            // stores/auth.ts pour le nettoyage de ce cache à la déconnexion.
            urlPattern: ({ url, request }) =>
              request.method === 'GET' &&
              (url.pathname.startsWith('/api/meal-plan-entries') ||
                url.pathname.startsWith('/api/shopping-lists')) &&
              !url.pathname.endsWith('/export/') &&
              !url.pathname.endsWith('/week-pdf/'),
            handler: 'NetworkFirst',
            options: {
              cacheName: 'cocotte-user-data',
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 * 3 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            // Photos de recettes (fichier téléversé ou URL externe type Unsplash).
            urlPattern: ({ request, url }) =>
              request.destination === 'image' || /\.(png|jpe?g|webp|gif)$/i.test(url.pathname),
            handler: 'CacheFirst',
            options: {
              cacheName: 'cocotte-images',
              expiration: { maxEntries: 150, maxAgeSeconds: 60 * 60 * 24 * 30 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      '/api': process.env.VITE_API_PROXY_TARGET || 'http://localhost:8000',
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    include: ['tests/unit/**/*.test.ts'],
  },
})
