import axios from 'axios'
import client from './client'

const AUTH_BASE = '/api/auth/'

export function register(payload) {
  return axios.post(`${AUTH_BASE}register/`, payload).then((r) => r.data)
}

export function obtainToken(username, password) {
  return axios.post(`${AUTH_BASE}token/`, { username, password }).then((r) => r.data)
}

export function refreshTokenRequest(refresh) {
  return axios.post(`${AUTH_BASE}token/refresh/`, { refresh }).then((r) => r.data)
}

export function fetchMe() {
  return client.get('auth/me/').then((r) => r.data)
}

export function updateMe(payload) {
  return client.patch('auth/me/', payload).then((r) => r.data)
}
