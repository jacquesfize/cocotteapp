import axios from 'axios'
import client from './client'
import type {
  ChangePasswordPayload,
  PasswordResetConfirmPayload,
  RegisterPayload,
  TokenPair,
} from '../types/api'
import type { LegalInfo, User } from '../types/models'

const AUTH_BASE = '/api/auth/'

export function register(payload: RegisterPayload): Promise<User> {
  return axios.post(`${AUTH_BASE}register/`, payload).then((r) => r.data)
}

export function obtainToken(email: string, password: string): Promise<TokenPair> {
  return axios.post(`${AUTH_BASE}token/`, { email, password }).then((r) => r.data)
}

export function refreshTokenRequest(refresh: string): Promise<TokenPair> {
  return axios.post(`${AUTH_BASE}token/refresh/`, { refresh }).then((r) => r.data)
}

export function fetchMe(): Promise<User> {
  return client.get('auth/me/').then((r) => r.data)
}

export function updateMe(payload: Partial<User>): Promise<User> {
  return client.patch('auth/me/', payload).then((r) => r.data)
}

export function deleteMe() {
  return client.delete('auth/me/')
}

export function changePassword(payload: ChangePasswordPayload) {
  return client.post('auth/me/change-password/', payload)
}

export function exportMyData(): Promise<Blob> {
  return client.get('auth/me/export/', { responseType: 'blob' }).then((r) => r.data)
}

export function requestPasswordReset(email: string): Promise<void> {
  return axios.post(`${AUTH_BASE}password-reset/`, { email }).then((r) => r.data)
}

export function confirmPasswordReset(payload: PasswordResetConfirmPayload): Promise<void> {
  return axios.post(`${AUTH_BASE}password-reset/confirm/`, payload).then((r) => r.data)
}

export function setHealthDataConsent(consent: boolean): Promise<User> {
  return client.post('auth/me/health-data-consent/', { consent }).then((r) => r.data)
}

export function fetchLegalInfo(): Promise<LegalInfo> {
  return axios.get(`${AUTH_BASE}legal/`).then((r) => r.data)
}
