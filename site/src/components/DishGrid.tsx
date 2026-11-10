/** Сетка меню: фильтры по категориям и карточки блюд. */

import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { fmt, imgUrl } from '../api/client'
import { queries, mutations } from '../api/service'
import type { Category, Dish } from '../types'
import { useCart } from '../state/CartContext'
import { useAuth } from '../state/AuthContext'
import { useToast } from '../state/ToastContext'

interface DishGridProps {
  dishes: Dish[]
  categories: Category[]
  onOpen: (dishId: number) => void
  /** Переход к категории с главной ({ id, ts }): ts уникален для каждого клика. */
  jump: { id: string; ts: number } | null
}

function DishCard({
  dish,
  favActive,
  onFav,
  onAdd,
  onOpen,
  index,
}: {
  dish: Dish
  favActive: boolean
  onFav: (dish: Dish) => void
  onAdd: (dish: Dish) => void
  onOpen: (dishId: number) => void
  index: number
}) {
  const src = imgUrl(dish.image)
  return (
    <article
      className={`dish-card${index > 0 ? ' pop' : ''}`}
      style={index > 0 ? { animationDelay: `${index * 60}ms` } : undefined}
      tabIndex={0}
      role="button"
      aria-label={dish.name}
      onClick={() => onOpen(dish.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter') onOpen(dish.id)
      }}
    >
      <div className="dish-cover">
        {!dish.is_available && <div className="dish-unav">Скоро вернёмся</div>}
        {src ? <img src={src} alt={dish.name} loading="lazy" /> : <div className="noimg">🍣</div>}
        {dish.category.name.length <= 8 && (
          <span className="dish-badge hot">{dish.category.name}</span>
        )}
        <button
          className={`dfav${favActive ? ' on' : ''}`}
          data-fav
          aria-label="В избранное"
          onClick={(e) => {
            e.stopPropagation()
            onFav(dish)
          }}
        >
          {favActive ? '❤️' : '🤍'}
        </button>
      </div>
      <div className="dish-body">
        <div className="dish-name">{dish.name}</div>
        <div className="dish-meta">
          <span>{dish.ingredients.split(',').slice(0, 3).join(',')}</span>
        </div>
        <div className="dish-row">
          <span className="dish-price">{fmt(dish.price)}</span>
          <button
            className="dadd"
            data-add
            aria-label={`Добавить ${dish.name} в корзину`}
            onClick={(e) => {
              e.stopPropagation()
              onAdd(dish)
            }}
          >
            +
          </button>
        </div>
      </div>
    </article>
  )
}

export function DishGrid({ dishes, categories, onOpen, jump }: DishGridProps) {
  const cart = useCart()
  const auth = useAuth()
  const nav = useNavigate()
  const toast = useToast()
  const [filter, setFilter] = useState('all')

  // Клик по категории на главной скроллит к меню и включает её фильтр
  useEffect(() => {
    if (jump) setFilter(jump.id)
  }, [jump])

  const favorites = useQuery(queries.favorites())
  const favQuery = favorites.data ?? []
  const favDishIds = new Set(favQuery.map((f) => f.dish.id))

  const favAdd = useMutation({
    mutationFn: (dishId: number) => mutations.addFavorite(dishId),
    onSuccess: (_, dishId) => {
      void dishId
    },
  })
  const favRemove = useMutation({
    mutationFn: (favId: number) => mutations.removeFavorite(favId),
    onSuccess: () => undefined,
  })

  function toggleFav(dish: Dish) {
    if (!auth.isAuthed) {
      nav('/login')
      return
    }
    const existing = favQuery.find((f) => f.dish.id === dish.id)
    if (existing) {
      favRemove.mutate(existing.id, {
        onSuccess: () => {
          void favorites.refetch()
          toast.push('Убрано из избранного')
        },
        onError: (e) => toast.push((e as { message?: string }).message ?? 'Ошибка', 'err'),
      })
    } else {
      favAdd.mutate(dish.id, {
        onSuccess: () => {
          void favorites.refetch()
          toast.push('❤️ Добавлено в избранное')
        },
        onError: (e) => toast.push((e as { message?: string }).message ?? 'Ошибка', 'err'),
      })
    }
  }

  function add(dish: Dish) {
    cart.add(dish.id)
    toast.push(`🛒 ${dish.name} — в корзине`)
  }

  const visible = dishes.filter(
    (d) => filter === 'all' || d.category.id === Number(filter),
  )

  return (
    <>
      <div className="filters" data-rv role="tablist" aria-label="Фильтр меню">
        <button className={`fchip${filter === 'all' ? ' on' : ''}`} onClick={() => setFilter('all')}>
          Всё меню
        </button>
        {categories.map((c) => (
          <button
            key={c.id}
            className={`fchip${filter === String(c.id) ? ' on' : ''}`}
            onClick={() => setFilter(String(c.id))}
          >
            {c.name}
          </button>
        ))}
      </div>

      <div className="pgrid" id="pgrid">
        {visible.map((dish, i) => (
          <DishCard
            key={dish.id}
            dish={dish}
            index={i}
            favActive={favDishIds.has(dish.id)}
            onFav={toggleFav}
            onAdd={add}
            onOpen={onOpen}
          />
        ))}
        {visible.length === 0 && <p className="dmenu-empty">В этой категории пока пусто…</p>}
      </div>
    </>
  )
}
