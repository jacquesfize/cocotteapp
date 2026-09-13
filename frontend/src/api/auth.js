import axios from 'axios'
import client from './client'

const AUTH_BASE = '/api/auth/'

export function register(payload) {
  return axios.post(`${AUTH_BASE}register/`, payload).then((r) => r.data)
}

export function obtainToken(email, password) {
  return axios.post(`${AUTH_BASE}token/`, { email, password }).then((r) => r.data)
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

export function deleteMe() {
  return client.delete('auth/me/')
}

export function changePassword(payload) {
  return client.post('auth/me/change-password/', payload)
}

export function exportMyData() {
  return client.get('auth/me/export/', { responseType: 'blob' }).then((r) => r.data)
}

export function requestPasswordReset(email) {
  return axios.post(`${AUTH_BASE}password-reset/`, { email }).then((r) => r.data)
}

export function confirmPasswordReset(payload) {
  return axios.post(`${AUTH_BASE}password-reset/confirm/`, payload).then((r) => r.data)
}
