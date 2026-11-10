/** Корзина-данвер: позиции → шаг 2 (адрес + промокод) → создание заказа. */

import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { fmt, imgUrl } from '../api/client'
import { mutations, queries } from '../api/service'
import { useCart } from '../state/CartContext'
import { useAuth } from '../state/AuthContext'
import { useToast } from '../state/ToastContext'
import type { Dish, OrderCreateData } from '../types'
import { useEscape } from '../hooks/useEscape'

export function CartDrawer() {
  const cart = useCart()
  const auth = useAuth()
  const nav = useNavigate()
  const toast = useToast()
  const [step, setStep] = useState<0 | 1>(0)

  const dishes = useQuery({ ...queries.dishes(), staleTime: 10 * 60 * 1000 })
  const byId = new Map<number, Dish>((dishes.data ?? []).map((d) => [d.id, d]))

  const rows = useMemo(
    () =>
      Object.entries(cart.items)
        .map(([id, qty]) => ({ id: Number(id), qty }))
        .filter((r) => byId.has(r.id))
        .map((r) => ({ ...r, dish: byId.get(r.id) as Dish })),
    [cart.items, byId],
  )

  const total = rows.reduce((s, r) => s + Number(r.dish.price) * r.qty, 0)
  useEscape(cart.isOpen, cart.close)

  const [street, setStreet] = useState('')
  const [house, setHouse] = useState('')
  const [entrance, setEntrance] = useState('')
  const [floor, setFloor] = useState('')
  const [apartment, setApartment] = useState('')
  const [comment, setComment] = useState('')
  const [promo, setPromo] = useState('')

  const order = useMutation({
    mutationFn: (data: OrderCreateData) => mutations.createOrder(data),
    onSuccess: (created) => {
      cart.clear()
      setStep(0)
      setStreet(''); setHouse(''); setEntrance('')
      setFloor(''); setApartment(''); setComment(''); setPromo('')
      toast.push(`🎉 Заказ №${created.id} создан!`, 'ok')
      cart.close()
      nav('/orders')
    },
    onError: (e) => toast.push((e as { message?: string }).message ?? 'Не удалось создать заказ', 'err'),
  })

  function checkout() {
    if (!auth.isAuthed) {
      cart.close()
      nav('/login')
      return
    }
    setStep(1)
  }

  function submit(e: React.FormEvent) {
    e.preventDefault()
    order.mutate({
      street,
      house,
      entrance,
      floor,
      apartment,
      comment,
      promo_code: promo,
      items: rows.map((r) => ({ dish_id: r.id, quantity: r.qty })),
    })
  }

  if (!cart.isOpen) return null

  return (
    <div className="cdrawer open" role="dialog" aria-modal="true" aria-label="Корзина">
      <div className="cd-head">
        <h3>{step === 0 ? '🛒 Корзина' : '📮 Оформление'}</h3>
        <button className="dm-close" aria-label="Закрыть" onClick={cart.close}>✕</button>
      </div>

      {step === 0 ? (
        <>
          <div className="cd-body">
            {rows.length === 0 ? (
              <div className="cd-empty">
                <span className="big">🛒</span>Пока пусто…<br />Загляни в меню — там огонь 🔥
              </div>
            ) : (
              rows.map((r) => {
                const src = imgUrl(r.dish.image)
                return (
                  <div className="ci" key={r.id}>
                    <div className="th">
                      {src ? <img src={src} alt={r.dish.name} /> : <div className="noimg" style={{ position: 'absolute', inset: 0, display: 'grid', placeItems: 'center', fontSize: 26 }}>🍣</div>}
                    </div>
                    <div className="in4">
                      <div className="nm">{r.dish.name}</div>
                      <div className="op">{r.dish.category.name}</div>
                      <div className="pr">{fmt(Number(r.dish.price) * r.qty)}</div>
                    </div>
                    <div className="qty">
                      <button aria-label="Меньше" onClick={() => cart.setQty(r.id, r.qty - 1)}>−</button>
                      <span>{r.qty}</span>
                      <button aria-label="Больше" onClick={() => cart.add(r.id)}>+</button>
                    </div>
                    <button className="rm" aria-label="Удалить" onClick={() => cart.remove(r.id)}>🗑</button>
                  </div>
                )
              })
            )}
          </div>
          <div className="cd-foot">
            <div className="cd-running">
              <i></i> Кухня свежая · среднее время доставки 30 мин
            </div>
            <div className="cd-total">
              <span>Итого</span>
              <b>{fmt(total)}</b>
            </div>
            <button className="btn btn-fire" style={{ width: '100%' }} disabled={rows.length === 0} onClick={checkout}>
              Оформить
            </button>
          </div>
        </>
      ) : (
        <form className="cd-body" onSubmit={submit}>
          <div className="co-fields">
            <div>
              <label htmlFor="co-street">Улица</label>
              <input
                id="co-street"
                value={street}
                onChange={(e) => setStreet(e.target.value)}
                placeholder="Абая"
                required
              />
            </div>
            <div className="co-row">
              <div>
                <label htmlFor="co-house">Дом</label>
                <input id="co-house" value={house} onChange={(e) => setHouse(e.target.value)} placeholder="18" required />
              </div>
              <div>
                <label htmlFor="co-entrance">Подъезд</label>
                <input id="co-entrance" value={entrance} onChange={(e) => setEntrance(e.target.value)} />
              </div>
              <div>
                <label htmlFor="co-floor">Этаж</label>
                <input id="co-floor" value={floor} onChange={(e) => setFloor(e.target.value)} />
              </div>
              <div>
                <label htmlFor="co-apartment">Квартира</label>
                <input id="co-apartment" value={apartment} onChange={(e) => setApartment(e.target.value)} />
              </div>
            </div>
            <div>
              <label htmlFor="co-comment">Комментарий курьеру</label>
              <textarea
                id="co-comment"
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={2}
                placeholder="Позвонить заранее, домофон…"
              />
            </div>
            <div>
              <label htmlFor="co-promo">Промокод (если есть)</label>
              <input id="co-promo" value={promo} onChange={(e) => setPromo(e.target.value)} placeholder="Он появится у акций" />
            </div>
          </div>
          {order.isError && <p className="ferr">{(order.error as { message?: string }).message}</p>}
          <div className="cd-total">
            <span>К оплате</span>
            <b>{fmt(total)}</b>
          </div>
          <button className="btn btn-fire" style={{ width: '100%' }} disabled={order.isPending}>
            {order.isPending ? 'Создаём…' : `Заказать · ${fmt(total)}`}
          </button>
          <button type="button" className="back-link" onClick={() => setStep(0)}>
            ← назад в корзину
          </button>
        </form>
      )}
    </div>
  )
}
