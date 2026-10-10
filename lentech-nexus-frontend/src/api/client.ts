const DEFAULT_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

function getCsrfCookie(): string | undefined {
  const name = 'csrftoken'
  const cookies = document.cookie.split('; ')
  for (const c of cookies) {
    if (c.startsWith(name + '=')) {
      return decodeURIComponent(c.substring(name.length + 1))
    }
  }
  return undefined
}

export async function ensureCsrf(): Promise<void> {
  await fetch(`${DEFAULT_BASE}/api/auth/csrf/`, {
    credentials: 'include',
    headers: { 'Accept': 'application/json' },
  })
}

export async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const url = `${DEFAULT_BASE}${path}`
  const method = (init.method ?? 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  if (!headers.has('Accept')) headers.set('Accept', 'application/json')
  if (method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
    if (!headers.has('Content-Type') && !(init.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json')
    }
    const csrf = getCsrfCookie()
    if (csrf && !headers.has('X-CSRFToken')) {
      headers.set('X-CSRFToken', csrf)
    }
  }

  const res = await fetch(url, {
    ...init,
    credentials: 'include',
    headers,
  })

  if (res.status === 204) return undefined as T

  let data: unknown = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!res.ok) {
    throw new ApiError(res.status, data)
  }

  return data as T
}

export class ApiError extends Error {
  status: number
  data: unknown

  constructor(status: number, data: unknown) {
    super(`API request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

export function getErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    const { data } = err
    if (typeof data === 'string' && data) return data
    if (data && typeof data === 'object') {
      const record = data as Record<string, unknown>
      if (typeof record.detail === 'string') return record.detail
      for (const value of Object.values(record)) {
        if (Array.isArray(value) && value.length) return String(value[0])
        if (typeof value === 'string' && value) return value
      }
    }
    return `Request failed (${err.status})`
  }
  if (err instanceof Error) return err.message
  return 'Something went wrong'
}