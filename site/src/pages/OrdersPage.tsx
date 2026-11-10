/** Мои заказы: статус-лента из 6 статусов, отмена в статусе «Создан». */

import { Navigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { fmt } from '../api/client'
import { mutations, queries } from '../api/service'
import { useAuth } from '../state/AuthContext'
import { useToast } from '../state/ToastContext'
import { ORDER_STATUSES, STATUS_LABELS, type Order } from '../types'

function StatusRibbon({ status }: { status: Order['status'] }) {
  if (status === 'cancelled') {
    return (
      <div className="ostatus">
        <span className="bad">✗ Отменён</span>
      </div>
    )
  }
  const idx = ORDER_STATUSES.indexOf(status as Exclude<Order['status'], 'cancelled'>)
  return (
    <div className="ostatus">
      {ORDER_STATUSES.map((s, i) => (
        <span key={s} className={i < idx ? 'done' : i === idx ? 'cur' : ''}>
          {i < idx ? '✓ ' : ''}
          {STATUS_LABELS[s]}
        </span>
      ))}
    </div>
  )
}

export default function OrdersPage() {
  const auth = useAuth()
  const toast = useToast()
  const orders = useQuery(queries.orders())

  const cancel = useMutation({
    mutationFn: (id: number) => mutations.cancelOrder(id),
    onSuccess: () => {
      void orders.refetch()
      toast.push('Заказ отменён')
    },
    onError: (e) => toast.push((e as { message?: string }).message ?? 'Ошибка отмены', 'err'),
  })

  if (!auth.isAuthed) return <Navigate to="/login?return=/orders" replace />

  const list = orders.data ?? []

  return (
    <div className="wrap orders-wrap" style={{ paddingTop: 120 }}>
      <div className="shead">
        <span className="sover">История</span>
        <h2 className="stitle">
          Мои <span className="grad">заказы</span>
        </h2>
        <p className="slead">Статус обновляется, когда заказ едет к тебе.</p>
      </div>

      {orders.isPending && (
        <div className="qz-loading">
          <div className="spinner" /> Грузим заказы…
        </div>
      )}
      {orders.isError && <p className="ferr">{(orders.error as { message?: string }).message}</p>}
      {!orders.isPending && list.length === 0 && (
        <div className="cd-empty">
          <span className="big">🛵</span>
          Заказов пока нет — время это исправить!
        </div>
      )}

      {list.map((o) => (
        <article className="ocard" key={o.id}>
          <div className="otop">
            <span className="onum">Заказ №{o.id}</span>
            <span className="odate">
              {new Date(o.created_at).toLocaleString('ru-RU', { day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>

          <StatusRibbon status={o.status} />

          <div className="oitems">
            {o.order_item.map((item) => (
              <div key={item.id}>
                <b>{item.dish.name}</b> × {item.quantity} — {fmt(Number(item.price_at_order) * item.quantity)}
              </div>
            ))}
          </div>

          {o.promo_code && (
            <span className="badge" style={{ width: 'fit-content' }}>
              промокод {o.promo_code}
            </span>
          )}

          <div className="osum">
            <span className="muted small">
              {o.street}, дом {o.house}
              {o.apartment && `, кв. ${o.apartment}`}
            </span>
            <span style={{ display: 'flex', gap: 10, alignItems: 'baseline' }}>
              {Number(o.discount_amount) > 0 && (
                <>
                  <s style={{ color: 'var(--muted)', fontSize: 13 }}>{fmt(o.subtotal)}</s>
                  <span className="dis">−{fmt(o.discount_amount)}</span>
                </>
              )}
              <b>{fmt(o.total_price)}</b>
            </span>
          </div>

          {o.status === 'created' && (
            <button className="back-link ocancel" onClick={() => cancel.mutate(o.id)}>
              ✗ Отменить заказ
            </button>
          )}
        </article>
      ))}
    </div>
  )
}
