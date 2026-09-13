import { defineStore } from 'pinia'
import {
  deleteMe,
  fetchMe,
  obtainToken,
  refreshTokenRequest,
  register as registerRequest,
  updateMe,
} from '../api/auth'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: localStorage.getItem('access_token'),
    refreshToken: localStorage.getItem('refresh_token'),
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken),
  },

  actions: {
    async register(payload) {
      await registerRequest(payload)
      await this.login(payload.email, payload.password)
    },

    async login(email, password) {
      const data = await obtainToken(email, password)
      this._setTokens(data.access, data.refresh)
      await this.fetchMe()
    },

    async fetchMe() {
      this.user = await fetchMe()
    },

    async updateProfile(payload) {
      this.user = await updateMe(payload)
    },

    async deleteAccount() {
      await deleteMe()
      this.logout()
    },

    async refreshAccessToken() {
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
    },

    _setTokens(access, refresh) {
      this.accessToken = access
      this.refreshToken = refresh
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)
    },
  },
})
