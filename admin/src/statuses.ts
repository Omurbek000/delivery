/** Статусы заказов и разрешённые переходы (копия матрицы из models.py). */

export const STATUS_LABELS: Record<string, string> = {
  created: 'Создан',
  confirmed: 'Подтверждён',
  cooking: 'Готовится',
  delivering: 'Доставляется',
  delivered: 'Доставлен',
  cancelled: 'Отменён',
}

export const NEXT_STATUS: Record<string, string[]> = {
  created: ['confirmed', 'cancelled'],
  confirmed: ['cooking', 'cancelled'],
  cooking: ['delivering'],
  delivering: ['delivered'],
  delivered: [],
  cancelled: [],
}
