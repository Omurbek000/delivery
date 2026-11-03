/** HTTP-клиент панели: JWT в localStorage, авто-обновление access при 401. */

// В дев-режиме панель живёт на 5173 и ходит прямо на бэкенд с CORS,
// в проде сборку раздаёт сам Django — тогда тот же origin.
const API = window.location.port === '5173' ? 'http://localhost:8000' : ''

// Суффикс для переброса на /login, если в проде панель под /panel/
const PANEL_BASE = window.location.pathname.startsWith('/panel') ? '/panel' : ''

export const apiBase = API

/** Ссылка на загруженный на сервер файл (фото и т.п.). */
export function imgUrl(path: string | null | undefined): string | null {
  if (!path) return null
  return path.startsWith('http') ? path : `${API}${path}`
}

export const tokens = {
  get access() {
    return localStorage.getItem('access')
  },
  get refresh() {
    return localStorage.getItem('refresh')
  },
  set(access: string, refresh: string) {
    localStorage.setItem('access', access)
    localStorage.setItem('refresh', refresh)
  },
  clear() {
    localStorage.removeItem('access')
    localStorage.removeItem('refresh')
    localStorage.removeItem('user')
  },
}

export type ApiErr = { message: string; status: number }

/** Достаёт первую понятную строчку из любой DRF-ошибки. */
function firstError(data: unknown): string | undefined {
  if (data == null || typeof data === 'boolean') return undefined
  if (typeof data === 'string') return data
  if (Array.isArray(data)) return firstError(data[0])
  if (typeof data === 'object') {
    for (const value of Object.values(data)) {
      const msg = firstError(value)
      if (msg) return msg
    }
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

/** Основной запрос: при 401 один раз обновляет токен и повторяет. */
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
    if (!window.location.pathname.endsWith('/login')) {
      window.location.href = `${PANEL_BASE}/login`
    }
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

/** Удобная обёртка для JSON-запросов. Для DELETE можно не передавать тело. */
export function json<T>(method: string, path: string, data?: unknown): Promise<T> {
  return api<T>(path, {
    method,
    body: data === undefined ? null : JSON.stringify(data),
  })
}

/** Понятный текст из любого исключения (react-query отдаёт Error). */
export function errText(e: unknown): string {
  return (e as { message?: string }).message ?? 'Неизвестная ошибка'
}

/** Загрузка файлов через FormData (фото блюд и акций). */
export function form<T>(method: string, path: string, data: FormData): Promise<T> {
  return api<T>(path, { method, body: data })
}

/** Забирает все страницы пагинации DRF (поддерживает и непагинированный ответ). */
export async function fetchAll<T>(path: string, maxPages = 20): Promise<T[]> {
  const first = await api<T[] | { results?: T[]; count?: number }>(path)
  const results = Array.isArray(first) ? [...first] : [...(first.results ?? [])]
  const count = Array.isArray(first) ? first.length : (first.count ?? results.length)
  const pageSize = results.length || 1
  const pages = Math.min(Math.ceil(count / pageSize), maxPages)
  for (let page = 2; page <= pages; page++) {
    const sep = path.includes('?') ? '&' : '?'
    const next = await api<{ results?: T[] }>(`${path}${sep}page=${page}`)
    results.push(...(next.results ?? []))
  }
  return results
}
