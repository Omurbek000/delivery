/** Тосты: контекст + рендер всплывающих сообщений справа сверху. */

import { createContext, useContext, useState, type ReactNode } from 'react'

type Toast = { id: number; message: string; kind: 'info' | 'ok' | 'err' }

interface ToastCtx {
  push: (message: string, kind?: Toast['kind']) => void
}

const Ctx = createContext<ToastCtx | null>(null)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  function push(message: string, kind: Toast['kind'] = 'info') {
    const id = Date.now() + Math.random()
    setToasts((list) => [...list, { id, message, kind }])
    setTimeout(() => setToasts((list) => list.filter((t) => t.id !== id)), 2800)
  }

  return (
    <Ctx.Provider value={{ push }}>
      {children}
      <div id="toasts" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.kind}`}>
            {t.message}
          </div>
        ))}
      </div>
    </Ctx.Provider>
  )
}

export function useToast(): ToastCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useToast вне ToastProvider')
  return ctx
}
