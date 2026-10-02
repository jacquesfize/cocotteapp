import { defineStore } from 'pinia'
import {
  deleteMe,
  fetchMe,
  obtainToken,
  refreshTokenRequest,
  register as registerRequest,
  setHealthDataConsent,
  updateMe,
} from '../api/auth'
import { clearPrivateOfflineData } from '../offline/sync'
import type { RegisterPayload } from '../types/api'
import type { User } from '../types/models'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    accessToken: localStorage.getItem('access_token') as string | null,
    refreshToken: localStorage.getItem('refresh_token') as string | null,
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
  },

  actions: {
    async register(payload: RegisterPayload) {
      await registerRequest(payload)
      await this.login(payload.email, payload.password)
    },

    async login(email: string, password: string) {
      const data = await obtainToken(email, password)
      this._setTokens(data.access, data.refresh)
      await this.fetchMe()
    },

    async fetchMe() {
      this.user = await fetchMe()
    },

    async updateProfile(payload: Partial<User>) {
      this.user = await updateMe(payload)
    },

    async setHealthConsent(consent: boolean) {
      this.user = await setHealthDataConsent(consent)
    },

    async deleteAccount(keepRecipes = false) {
      await deleteMe(keepRecipes)
      this.logout()
    },

    async refreshAccessToken(): Promise<boolean> {
      if (!this.refreshToken) return false
      try {
        const data = await refreshTokenRequest(this.refreshToken)
        this._setTokens(data.access, this.refreshToken)
        return true
      } catch {
        return false
      }
    },

    logout() {
      this.user = null
      this.accessToken = null
      this.refreshToken = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      // Sur un appareil partagé, les données d'un compte ne doivent pas rester
      // consultables hors ligne une fois que son utilisateur s'est déconnecté.
      clearPrivateOfflineData().catch(() => {})
    },

    _setTokens(access: string, refresh: string) {
      this.accessToken = access
      this.refreshToken = refresh
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)
    },
  },
})
