/** Плавающая корзина: висит поверх всего сайта, её можно перетащить в любой угол. */

import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fmt } from '../api/client'
import { queries } from '../api/service'
import { useCart } from '../state/CartContext'
import { useDragFab } from '../hooks/useDragFab'

export function CartFab() {
  const cart = useCart()
  const ref = useRef<HTMLButtonElement>(null)
  const dishes = useQuery({ ...queries.dishes(), enabled: cart.count > 0 })
  const { style, handlers } = useDragFab('onigiri-fab-pos', () => cart.open(), ref)
  const [bump, setBump] = useState(false)

  useEffect(() => {
    if (cart.count <= 0) return
    setBump(true)
    const t = setTimeout(() => setBump(false), 500)
    return () => clearTimeout(t)
  }, [cart.count])

  const rows = Object.entries(cart.items).map(([id, qty]) => ({
    qty,
    dish: (dishes.data ?? []).find((d) => d.id === Number(id)),
  }))
  const total = rows.reduce((s, r) => (r.dish ? s + Number(r.dish.price) * r.qty : s), 0)

  return (
    <button
      ref={ref}
      type="button"
      className={`mcfab${cart.isOpen ? ' hide' : ''}${bump && cart.count > 0 ? ' bump' : ''}`}
      style={style}
      {...handlers}
      onDragStart={(e) => e.preventDefault()}
      aria-label={`Корзина: ${cart.count}`}
    >
      <span className="mc-i">🛒</span>
      <span className="mc-cnt">{cart.count}</span>
      {cart.count > 0 && <span className="mc-t">{fmt(total)}</span>}
      {cart.count === 0 && <span className="mc-lbl">Корзина</span>}
    </button>
  )
}
