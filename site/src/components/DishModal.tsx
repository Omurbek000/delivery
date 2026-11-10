/** Модал блюда: фото, описание, состав, выбор количества, добавление в корзину. */

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { fmt, imgUrl } from '../api/client'
import { queries } from '../api/service'
import { useCart } from '../state/CartContext'
import { useEscape } from '../hooks/useEscape'
import type { Promo } from '../types'

interface DishModalProps {
  dishId: number | null
  promos: Promo[]
  onClose: () => void
}

export function DishModal({ dishId, promos, onClose }: DishModalProps) {
  const cart = useCart()
  const [qty, setQty] = useState(1)
  const [added, setAdded] = useState(false)
  const [tab, setTab] = useState(0)

  const dish = useQuery({ ...queries.dish(dishId ?? 0), enabled: dishId !== null })
  useEscape(dishId !== null, onClose)

  if (dishId === null) return null

  const d = dish.data
  const promo = d ? promos.find((p) => p.dish?.id === d.id) : undefined
  const price = d ? (promo ? promo.new_price : d.price) : '0'
  const oldPrice = promo ? promo.old_price : null
  const src = imgUrl(d?.image)

  function add() {
    if (!d) return
    cart.add(d.id, qty)
    setAdded(true)
    setTimeout(() => setAdded(false), 1400)
  }

  const total = fmt(Number(price) * qty)

  return (
    <div
      className={`dmodal${dishId ? ' open' : ''}`}
      role="dialog"
      aria-modal="true"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
    >
      <div className="dm-box">
        <div className="dm-head">
          <button className="dm-close" aria-label="Закрыть" onClick={onClose}>
            ✕
          </button>
          <span className="dm-crumb">Меню / {(d?.category.name ?? '').replace(/^[^ ]+ /, '')} / {d?.name ?? ''}</span>
        </div>
        <div className="dm-grid">
          <div className="dm-photo">
            <div className="dm-img">
              {src ? <img src={src} alt={d?.name ?? 'Фото блюда'} /> : <div className="noimg">🍣</div>}
            </div>
          </div>
          <div className="dm-info">
            {d ? (
              <>
                <div className="dm-tags">
                  <span>{d.category.name}</span>
                  {!d.is_available && <span>нет в наличии</span>}
                  {promo && <span className="hot">акция</span>}
                </div>
                <h2 className="dm-title">{d.name}</h2>
                {d.description && <p style={{ color: '#c9c9d2', fontSize: 14 }}>{d.description}</p>}
                <div className="dm-price">
                  <b>{total}</b>
                  {oldPrice && <s>{fmt(oldPrice)}</s>}
                  {promo && (
                    <span className="disc">−{Math.round(Number(promo.discount_percent))}%</span>
                  )}
                </div>
                <div className="buyrow">
                  <div className="qty">
                    <button aria-label="Меньше" onClick={() => setQty((q) => Math.max(1, q - 1))}>
                      −
                    </button>
                    <span>{qty}</span>
                    <button aria-label="Больше" onClick={() => setQty((q) => Math.min(20, q + 1))}>
                      +
                    </button>
                  </div>
                  <button
                    className={`btn btn-fire buybtn${added ? ' added' : ''}`}
                    disabled={!d.is_available}
                    onClick={add}
                  >
                    {added ? '✓ Добавлено' : `🛒 В корзину · ${total}`}
                  </button>
                </div>
                <div className="deliv">
                  <div>🚀 <span>Доставка <b>за 30 минут</b> по всему городу</span></div>
                  <div>💳 <span>Карта · СБП · наличные курьеру</span></div>
                </div>
                <div className="dm-tabs">
                  <div className="tabbar">
                    <button className={tab === 0 ? 'on' : ''} onClick={() => setTab(0)}>Описание</button>
                    <button className={tab === 1 ? 'on' : ''} onClick={() => setTab(1)}>Состав</button>
                  </div>
                  <div className={`tabpane${tab === 0 ? ' on' : ''}`}>
                    <p>{d.description}</p>
                  </div>
                  <div className={`tabpane${tab === 1 ? ' on' : ''}`}>
                    <div className="ingr">
                      {d.ingredients
                        .split(',')
                        .map((s) => s.trim())
                        .filter(Boolean)
                        .map((chunk) => (
                          <span key={chunk}>{chunk}</span>
                        ))}
                    </div>
                  </div>
                </div>
              </>
            ) : (
              <div className="qz-loading">
                <div className="spinner" />
                Загружаем блюдо…
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
