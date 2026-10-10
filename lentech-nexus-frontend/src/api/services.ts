import type {
  Developer,
  Idea,
  JoinRequest,
  Paginated,
  Project,
  User,
} from '../types/api'
import { apiFetch, ensureCsrf } from './client'

export const auth = {
  async csrf() {
    return ensureCsrf()
  },
  async register(payload: {
    username: string
    email: string
    password: string
    password_confirm: string
  }) {
    await ensureCsrf()
    return apiFetch<User>('/api/auth/register/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  async login(payload: { username: string; password: string }) {
    await ensureCsrf()
    return apiFetch<User>('/api/auth/login/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  async logout() {
    await ensureCsrf()
    return apiFetch<void>('/api/auth/logout/', { method: 'POST' })
  },
  async me() {
    return apiFetch<User>('/api/auth/me/')
  },
  async updateMe(payload: Partial<User>) {
    await ensureCsrf()
    return apiFetch<User>('/api/auth/me/', {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
  async changePassword(payload: { old_password: string; new_password: string }) {
    await ensureCsrf()
    return apiFetch<{ detail: string }>('/api/auth/password/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
}

export const developers = {
  list(params?: Record<string, string>) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return apiFetch<Paginated<Developer>>(`/api/developers/${qs}`)
  },
  get(id: number) {
    return apiFetch<Developer>(`/api/developers/${id}/`)
  },
  me() {
    return apiFetch<Developer>('/api/developers/me/')
  },
  create(payload: Partial<Developer>) {
    return apiFetch<Developer>('/api/developers/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  update(id: number, payload: Partial<Developer>) {
    return apiFetch<Developer>(`/api/developers/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
  uploadPhoto(file: File) {
    const fd = new FormData()
    fd.append('image', file)
    return apiFetch<Developer>('/api/developers/me/photo/', {
      method: 'POST',
      body: fd,
    })
  },
  removePhoto() {
    return apiFetch<Developer>('/api/developers/me/photo/', {
      method: 'DELETE',
    })
  },
}

export const projects = {
  list(params?: Record<string, string>) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return apiFetch<Paginated<Project>>(`/api/projects/${qs}`)
  },
  get(id: number) {
    return apiFetch<Project>(`/api/projects/${id}/`)
  },
  create(payload: Partial<Project>) {
    return apiFetch<Project>('/api/projects/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  update(id: number, payload: Partial<Project>) {
    return apiFetch<Project>(`/api/projects/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
  remove(id: number) {
    return apiFetch<void>(`/api/projects/${id}/`, { method: 'DELETE' })
  },
  join(id: number, message?: string) {
    return apiFetch<JoinRequest>(`/api/projects/${id}/join/`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    })
  },
  leave(id: number) {
    return apiFetch<void>(`/api/projects/${id}/leave/`, { method: 'DELETE' })
  },
  requests(id: number) {
    return apiFetch<JoinRequest[]>(`/api/projects/${id}/requests/`)
  },
  removeMember(id: number, userId: number) {
    return apiFetch<void>(`/api/projects/${id}/members/${userId}/`, {
      method: 'DELETE',
    })
  },
}

export const ideas = {
  list(params?: Record<string, string>) {
    const qs = params ? '?' + new URLSearchParams(params).toString() : ''
    return apiFetch<Paginated<Idea>>(`/api/ideas/${qs}`)
  },
  get(id: number) {
    return apiFetch<Idea>(`/api/ideas/${id}/`)
  },
  create(payload: Partial<Idea>) {
    return apiFetch<Idea>('/api/ideas/', {
      method: 'POST',
      body: JSON.stringify(payload),
    })
  },
  update(id: number, payload: Partial<Idea>) {
    return apiFetch<Idea>(`/api/ideas/${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    })
  },
  remove(id: number) {
    return apiFetch<void>(`/api/ideas/${id}/`, { method: 'DELETE' })
  },
  interest(id: number, message?: string) {
    return apiFetch<unknown>(`/api/ideas/${id}/interest/`, {
      method: 'POST',
      body: JSON.stringify({ message }),
    })
  },
}

export const joinRequests = {
  approve(id: number) {
    return apiFetch<unknown>(`/api/join-requests/${id}/approve/`, { method: 'POST' })
  },
  reject(id: number) {
    return apiFetch<unknown>(`/api/join-requests/${id}/reject/`, { method: 'POST' })
  },
}