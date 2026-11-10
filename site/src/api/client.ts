/** HTTP-клиент сайта: JWT в localStorage, авто-обновление access при 401. */

import type { ApiErr } from '../types'

// Дев-режим сайта живёт на 5174 и ходит прямо на бэкенд 8000, в проде — тот же origin.
const API = window.location.port === '5174' ? 'http://localhost:8000' : ''

export const apiBase = API

export const tokens = {
  get access() {
    return localStorage.getItem('onigiri-access')
  },
  get refresh() {
    return localStorage.getItem('onigiri-refresh')
  },
  set(access: string, refresh: string) {
    localStorage.setItem('onigiri-access', access)
    localStorage.setItem('onigiri-refresh', refresh)
  },
  clear() {
    localStorage.removeItem('onigiri-access')
    localStorage.removeItem('onigiri-refresh')
    localStorage.removeItem('onigiri-user')
  },
}

function firstError(data: unknown): string | undefined {
  if (data == null || typeof data !== 'object') {
    return typeof data === 'string' ? data : undefined
  }
  if (Array.isArray(data)) return firstError(data[0])
  for (const value of Object.values(data as Record<string, unknown>)) {
    const msg = firstError(value)
    if (msg) return msg
  }
  return undefined
}

async function refreshOnce(): Promise<boolean> {
  if (!tokens.refresh) return false
  const res = await fetch(`${API}/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh: tokens.refresh }),
  })
  if (!res.ok) return false
  const data = (await res.json()) as { access: string; refresh?: string }
  tokens.set(data.access, data.refresh ?? tokens.refresh)
  return true
}

export async function api<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const send = () =>
    fetch(`${API}${path}`, {
      ...options,
      headers: {
        ...(tokens.access ? { Authorization: `Bearer ${tokens.access}` } : {}),
        ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
        ...(options.headers ?? {}),
      },
    })

  let res = await send()
  if (res.status === 401 && tokens.refresh && (await refreshOnce())) {
    res = await send()
  }
  if (res.status === 401) {
    tokens.clear()
    dispatchEvent(new Event('onigiri:auth-expired'))
    const err: ApiErr = { message: 'Сессия истекла, войдите заново', status: 401 }
    throw err
  }
  if (res.ok) {
    if (res.status === 204) return undefined as T
    return (await res.json()) as T
  }
  let message = `Ошибка ${res.status}`
  try {
    const data: unknown = await res.json()
    message = firstError(data) ?? message
  } catch {
    // Пустой или не-JSON ответ
  }
  const err: ApiErr = { message, status: res.status }
  throw err
}

export const json = <T>(method: string, path: string, data?: unknown): Promise<T> =>
  api<T>(path, {
    method,
    body: data === undefined ? null : JSON.stringify(data),
  })

export const form = <T>(path: string, data: FormData): Promise<T> =>
  api<T>(path, { method: 'PATCH', body: data })

/** Абсолютная ссылка на файл (фото), загруженный на сервер. */
export function imgUrl(path: string | null | undefined): string | null {
  if (!path) return null
  return path.startsWith('http') ? path : `${API}${path}`
}

/** Деньги с разделителями: 1 800 ₽. */
export function fmt(value: string | number): string {
  const num = typeof value === 'string' ? Number(value) : value
  return `${Math.round(num).toLocaleString('ru-RU')} ₽`
}
