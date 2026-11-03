import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState, type FormEvent } from 'react'
import { errText, fetchAll, form, imgUrl, json } from '../api'
import type { Dish, Promo, PromoCode } from '../types'

/** Страница акций (карточки на главной) и промокодов. */

export default function Promos() {
  const qc = useQueryClient()
  const [error, setError] = useState('')

  const fail = (e: unknown) => setError(errText(e))
  const refresh = () => {
    setError('')
    qc.invalidateQueries({ queryKey: ['promos'] })
    qc.invalidateQueries({ queryKey: ['promo-codes'] })
  }

  const promos = useQuery({ queryKey: ['promos'], queryFn: () => fetchAll<Promo>('/promos/') })
  const dishes = useQuery({ queryKey: ['dishes'], queryFn: () => fetchAll<Dish>('/dishes/', 10) })
  const codes = useQuery({ queryKey: ['promo-codes'], queryFn: () => fetchAll<PromoCode>('/promo-codes/') })

  const togglePromo = useMutation({
    mutationFn: (promo: Promo) =>
      json<Promo>('PATCH', `/promos/${promo.id}/edit/`, { is_active: !promo.is_active }),
    onSuccess: refresh,
    onError: fail,
  })

  const deletePromo = useMutation({
    mutationFn: (id: number) => json<never>('DELETE', `/promos/${id}/edit/`),
    onSuccess: refresh,
    onError: fail,
  })

  const toggleCode = useMutation({
    mutationFn: (promoCode: PromoCode) =>
      json<PromoCode>('PATCH', `/promo-codes/${promoCode.id}/edit/`, {
        is_active: !promoCode.is_active,
      }),
    onSuccess: refresh,
    onError: fail,
  })

  const deleteCode = useMutation({
    mutationFn: (id: number) => json<never>('DELETE', `/promo-codes/${id}/edit/`),
    onSuccess: refresh,
    onError: fail,
  })

  return (
    <div>
      <h2>Акции и промокоды</h2>
      {error && <p className="hint error">{error}</p>}

      <PromoForm dishes={dishes.data ?? []} onDone={refresh} onError={fail} />

      <h3>Акции</h3>
      <table>
        <thead>
          <tr>
            <th>Фото</th>
            <th>Название</th>
            <th>Блюдо</th>
            <th>Цена со скидкой</th>
            <th>Скидка</th>
            <th>Порядок</th>
            <th>Активна</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {(promos.data ?? []).map((promo) => {
            const newPrice = Number(promo.old_price) * (1 - Number(promo.discount_percent) / 100)
            return (
              <tr key={promo.id} data-promo-id={promo.id}>
                <td>
                  {promo.image ? (
                    <img className="thumb" src={imgUrl(promo.image) ?? ''} alt={promo.title} />
                  ) : (
                    <span className="muted">—</span>
                  )}
                </td>
                <td>{promo.title}</td>
                <td>{promo.dish?.name ?? '—'}</td>
                <td>
                  <s className="muted">{promo.old_price}</s> {newPrice.toFixed(2)}
                </td>
                <td>{promo.discount_percent}%</td>
                <td>{promo.sort_order}</td>
                <td>
                  <span className={`badge ${promo.is_active ? 'ok' : 'bad'}`}>
                    {promo.is_active ? 'Да' : 'Нет'}
                  </span>
                </td>
                <td>
                  <button
                    disabled={togglePromo.isPending}
                    onClick={() => togglePromo.mutate(promo)}
                  >
                    {promo.is_active ? 'Отключить' : 'Включить'}
                  </button>
                  <button className="danger" onClick={() => deletePromo.mutate(promo.id)}>
                    Удалить
                  </button>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <PromoCodeForm onDone={refresh} onError={fail} />

      <h3>Промокоды</h3>
      <table>
        <thead>
          <tr>
            <th>Код</th>
            <th>Скидка</th>
            <th>Мин. сумма</th>
            <th>Действует до</th>
            <th>Активен</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {(codes.data ?? []).map((promoCode) => (
            <tr key={promoCode.id} data-code={promoCode.code}>
              <td>
                <strong>{promoCode.code}</strong>
              </td>
              <td>{promoCode.discount_percent}%</td>
              <td>{promoCode.min_order_amount}</td>
              <td>{promoCode.valid_until ?? '—'}</td>
              <td>
                <span className={`badge ${promoCode.is_active ? 'ok' : 'bad'}`}>
                  {promoCode.is_active ? 'Да' : 'Нет'}
                </span>
              </td>
              <td>
                <button
                  disabled={toggleCode.isPending}
                  onClick={() => toggleCode.mutate(promoCode)}
                >
                  {promoCode.is_active ? 'Отключить' : 'Включить'}
                </button>
                <button className="danger" onClick={() => deleteCode.mutate(promoCode.id)}>
                  Удалить
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function PromoForm({
  dishes,
  onDone,
  onError,
}: {
  dishes: Dish[]
  onDone: () => void
  onError: (e: unknown) => void
}) {
  const [title, setTitle] = useState('')
  const [oldPrice, setOldPrice] = useState('')
  const [discount, setDiscount] = useState('')
  const [dishId, setDishId] = useState('')
  const [sortOrder, setSortOrder] = useState('0')
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    try {
      const data = new FormData()
      data.set('title', title)
      data.set('old_price', oldPrice)
      data.set('discount_percent', discount)
      data.set('dish_id', dishId)
      data.set('sort_order', sortOrder)
      if (file) data.set('image', file)
      await form<Promo>('POST', '/promos/create/', data)
      setTitle('')
      setOldPrice('')
      setDiscount('')
      setDishId('')
      setFile(null)
      onDone()
    } catch (e) {
      onError(e)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel">
      <strong>Новая акция</strong>
      <div className="row">
        <div>
          <label>Название</label>
          <input value={title} onChange={(e) => setTitle(e.target.value)} />
        </div>
        <div>
          <label>Старая цена</label>
          <input value={oldPrice} onChange={(e) => setOldPrice(e.target.value)} placeholder="490.00" />
        </div>
        <div>
          <label>Скидка, %</label>
          <input value={discount} onChange={(e) => setDiscount(e.target.value)} placeholder="10" />
        </div>
      </div>
      <div className="row">
        <div>
          <label>Блюдо</label>
          <select value={dishId} onChange={(e) => setDishId(e.target.value)}>
            <option value="">— выбери —</option>
            {dishes.map((dish) => (
              <option key={dish.id} value={dish.id}>
                {dish.name}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label>Порядок</label>
          <input value={sortOrder} onChange={(e) => setSortOrder(e.target.value)} />
        </div>
        <div>
          <label>Фото (необязательно)</label>
          <input type="file" accept="image/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </div>
      </div>
      <button
        className="primary"
        disabled={busy || !title.trim() || !oldPrice || !discount || !dishId}
        onClick={submit}
      >
        Создать акцию
      </button>
    </div>
  )
}

function PromoCodeForm({
  onDone,
  onError,
}: {
  onDone: () => void
  onError: (e: unknown) => void
}) {
  const [code, setCode] = useState('')
  const [discount, setDiscount] = useState('')
  const [minAmount, setMinAmount] = useState('0')
  const [validUntil, setValidUntil] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    try {
      await json<PromoCode>('POST', '/promo-codes/create/', {
        code,
        discount_percent: discount,
        min_order_amount: minAmount,
        valid_until: validUntil || null,
      })
      setCode('')
      setDiscount('')
      setMinAmount('0')
      setValidUntil('')
      onDone()
    } catch (e) {
      onError(e)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel">
      <strong>Новый промокод</strong>
      <div className="row">
        <div>
          <label>Код</label>
          <input value={code} onChange={(e) => setCode(e.target.value)} placeholder="Доставка15" />
        </div>
        <div>
          <label>Скидка, %</label>
          <input value={discount} onChange={(e) => setDiscount(e.target.value)} placeholder="15" />
        </div>
        <div>
          <label>Мин. сумма заказа</label>
          <input value={minAmount} onChange={(e) => setMinAmount(e.target.value)} />
        </div>
        <div>
          <label>Действует до (необязательно)</label>
          <input type="date" value={validUntil} onChange={(e) => setValidUntil(e.target.value)} />
        </div>
      </div>
      <button
        className="primary"
        disabled={busy || !code.trim() || !discount}
        onClick={submit}
      >
        Создать промокод
      </button>
    </div>
  )
}
