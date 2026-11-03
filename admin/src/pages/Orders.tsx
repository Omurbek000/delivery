import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { errText, fetchAll, json } from '../api'
import type { AdminUser, Order } from '../types'
import { NEXT_STATUS, STATUS_LABELS } from '../statuses'

export default function Orders() {
  const qc = useQueryClient()
  const [error, setError] = useState('')

  const orders = useQuery({ queryKey: ['orders'], queryFn: () => fetchAll<Order>('/orders/', 5) })
  const users = useQuery({ queryKey: ['users-map'], queryFn: () => fetchAll<AdminUser>('/users/') })

  const setStatus = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      json<Order>('PATCH', `/orders/${id}/status/`, { status }),
    onSuccess: () => {
      setError('')
      qc.invalidateQueries({ queryKey: ['orders'] })
    },
    onError: (e) => setError(errText(e)),
  })

  if (orders.isLoading) return <p>Загружаем заказы...</p>
  if (orders.isError) return <p className="error">Не удалось загрузить заказы: {errText(orders.error)}</p>

  const userMap = new Map((users.data ?? []).map((user) => [user.id, user]))

  return (
    <div>
      <h2>Заказы</h2>
      {error && <p className="hint error">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>№</th>
            <th>Дата</th>
            <th>Клиент</th>
            <th>Адрес</th>
            <th>Состав</th>
            <th>Сумма</th>
            <th>Статус</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {orders.data!.map((order) => {
            const client = userMap.get(order.user)
            return (
              <tr key={order.id} data-order-id={order.id}>
                <td>{order.id}</td>
                <td>{new Date(order.created_at).toLocaleString('ru-RU')}</td>
                <td>
                  {client
                    ? `${client.first_name} ${client.last_name} ${client.phone}`
                    : `#${order.user}`}
                </td>
                <td>
                  ул. {order.street}, {order.house}
                  {order.apartment ? `, кв. ${order.apartment}` : ''}
                  {order.comment && (
                    <div className="muted small">Комментарий: {order.comment}</div>
                  )}
                </td>
                <td>
                  {order.order_item.map((item) => (
                    <div key={item.id} className="small">
                      {item.dish ? item.dish.name : `#${item.dish}`} × {item.quantity}
                    </div>
                  ))}
                </td>
                <td>
                  {order.total_price}
                  {Number(order.discount_amount) > 0 && (
                    <div className="muted small">скидка −{order.discount_amount}</div>
                  )}
                </td>
                <td>
                  <span className={`badge status-${order.status}`}>
                    {STATUS_LABELS[order.status] ?? order.status}
                  </span>
                </td>
                <td>
                  {(NEXT_STATUS[order.status] ?? []).map((next) => (
                    <button
                      key={next}
                      className={next === 'cancelled' ? 'danger' : ''}
                      disabled={setStatus.isPending}
                      onClick={() => setStatus.mutate({ id: order.id, status: next })}
                    >
                      {STATUS_LABELS[next]}
                    </button>
                  ))}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
      {orders.data!.length === 0 && <p>Заказов пока нет.</p>}
    </div>
  )
}
