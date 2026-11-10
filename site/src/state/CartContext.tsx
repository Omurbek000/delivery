/** CartContext: корзина в localStorage, счётчик и суммы по ценам кэша меню. */

import { createContext, useContext, useMemo, useState, useEffect, type ReactNode } from 'react'

type CartItems = Record<number, number>

interface CartCtx {
  items: CartItems
  count: number
  isOpen: boolean
  open: () => void
  close: () => void
  add: (dishId: number, qty?: number) => void
  setQty: (dishId: number, qty: number) => void
  remove: (dishId: number) => void
  clear: () => void
}

const Ctx = createContext<CartCtx | null>(null)

function readCart(): CartItems {
  const raw = localStorage.getItem('onigiri-cart')
  if (!raw) return {}
  try {
    return JSON.parse(raw) as CartItems
  } catch {
    return {}
  }
}

export function CartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CartItems>(readCart)
  const [isOpen, setOpen] = useState(false)

  useEffect(() => {
    localStorage.setItem('onigiri-cart', JSON.stringify(items))
  }, [items])

  useEffect(() => {
    document.body.classList.toggle('lock', isOpen)
    return () => {
      document.body.classList.remove('lock')
    }
  }, [isOpen])

  const value = useMemo<CartCtx>(() => {
    const count = Object.values(items).reduce((s, q) => s + q, 0)
    return {
      items,
      count,
      isOpen,
      open: () => setOpen(true),
      close: () => setOpen(false),
      add: (dishId, qty = 1) => setItems((c) => ({ ...c, [dishId]: Math.min(20, (c[dishId] ?? 0) + qty) })),
      setQty: (dishId, qty) => setItems((c) => ({ ...c, [dishId]: Math.min(20, Math.max(0, qty)) })),
      remove: (dishId) =>
        setItems((c) => {
          const next = { ...c }
          delete next[dishId]
          return next
        }),
      clear: () => setItems({}),
    }
  }, [items, isOpen])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useCart(): CartCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useCart вне CartProvider')
  return ctx
}
