import { defineConfig, devices } from '@playwright/test'

// Génère les captures d'écran de la documentation (docs/assets/screenshots/) :
//   E2E_ADMIN_EMAIL=... E2E_ADMIN_PASSWORD=... npm run docs:screenshots
// Distinct de playwright.config.ts pour que `npm run test:e2e` n'exécute pas ces scénarios.
// Comme les e2e, nécessite le backend (:8000) et le frontend (:5173) déjà lancés.
const launchOptions = { executablePath: process.env.PLAYWRIGHT_CHROMIUM_PATH || undefined }

export default defineConfig({
  testDir: './tests/docs',
  fullyParallel: false,
  workers: 1,
  timeout: 300_000,
  expect: { timeout: 15_000 },
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'retain-on-failure',
    // Le service worker (Workbox) intercepterait les requêtes avant page.route() et servirait
    // des réponses en cache : on le bloque pour des captures déterministes.
    serviceWorkers: 'block',
    colorScheme: 'light',
    locale: 'en-US',
  },
  projects: [
    {
      name: 'desktop',
      use: {
        ...devices['Desktop Chrome'],
        viewport: { width: 1280, height: 800 },
        deviceScaleFactor: 2,
        colorScheme: 'light',
        locale: 'en-US',
        launchOptions,
      },
    },
    {
      name: 'mobile',
      use: {
        ...devices['Pixel 7'],
        colorScheme: 'light',
        locale: 'en-US',
        launchOptions,
      },
    },
  ],
})
