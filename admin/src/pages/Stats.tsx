import { useQuery } from '@tanstack/react-query'
import { api, errText } from '../api'
import type { Stats } from '../types'
import { STATUS_LABELS } from '../statuses'

export default function Stats() {
  const stats = useQuery({ queryKey: ['stats'], queryFn: () => api<Stats>('/stats/') })

  if (stats.isLoading) return <p>Загружаем статистику...</p>
  if (stats.isError) return <p className="error">Не удалось загрузить: {errText(stats.error)}</p>

  const data = stats.data!

  return (
    <div>
      <h2>Дэшборд</h2>
      <div className="cards">
        <div className="card">
          <div className="muted">Заказов сегодня</div>
          <div className="num">{data.today.orders}</div>
        </div>
        <div className="card">
          <div className="muted">Выручка за сегодня</div>
          <div className="num">{data.today.revenue}</div>
        </div>
      </div>

      <h3>Заказы по статусам</h3>
      <table>
        <thead>
          <tr>
            <th>Статус</th>
            <th>Количество</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(data.status_counts).map(([code, count]) => (
            <tr key={code}>
              <td>
                <span className={`badge status-${code}`}>{STATUS_LABELS[code] ?? code}</span>
              </td>
              <td>{count}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Топ-5 блюд по продажам</h3>
      <table>
        <thead>
          <tr>
            <th>Блюдо</th>
            <th>Продано шт.</th>
            <th>Выручка</th>
          </tr>
        </thead>
        <tbody>
          {data.top_dishes.map((dish) => (
            <tr key={dish.name}>
              <td>{dish.name}</td>
              <td>{dish.qty}</td>
              <td>{dish.revenue}</td>
            </tr>
          ))}
          {data.top_dishes.length === 0 && (
            <tr>
              <td className="muted">Пока нет проданных блюд</td>
              <td />
              <td />
            </tr>
          )}
        </tbody>
      </table>
    </div>
  )
}
