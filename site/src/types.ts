/** Типы данных API доставки «Онигири». */

export interface Category {
  id: number
  name: string
}

export interface Dish {
  id: number
  name: string
  description: string
  ingredients: string
  price: string
  image: string | null
  is_available: boolean
  category: Category
}

export interface Promo {
  id: number
  title: string
  description: string
  old_price: string
  new_price: string
  discount_percent: string
  dish: Dish | null
  image: string | null
  sort_order: number
}

export interface Favorite {
  id: number
  dish: Dish
  created_at: string
}

export interface AuthUser {
  id: number
  phone: string
  first_name: string
  last_name: string
  photo: string | null
}

export interface LoginResult {
  user: AuthUser & { is_staff: boolean }
  access: string
  refresh: string
}

export interface OrderItem {
  id: number
  dish: Dish
  quantity: number
  price_at_order: string
}

export type OrderStatus =
  | 'created'
  | 'confirmed'
  | 'cooking'
  | 'delivering'
  | 'delivered'
  | 'cancelled'

export interface Order {
  id: number
  created_at: string
  status: OrderStatus
  street: string
  house: string
  entrance: string
  floor: string
  apartment: string
  total_price: string
  discount_amount: string
  subtotal: string
  promo_code: string | null
  comment: string
  order_item: OrderItem[]
}

export interface OrderCreateData {
  street: string
  house: string
  entrance: string
  floor: string
  apartment: string
  comment: string
  promo_code: string
  items: Array<{ dish_id: number; quantity: number }>
}

export interface AiRecommendResult {
  query: string
  answer: string
  dish_ids: number[]
  dishes: Dish[]
  source: 'ai' | 'fallback'
}

export type ApiErr = { message: string; status: number }

export const ORDER_STATUSES: Array<Exclude<OrderStatus, 'cancelled'>> = [
  'created',
  'confirmed',
  'cooking',
  'delivering',
  'delivered',
]

export const STATUS_LABELS: Record<OrderStatus, string> = {
  created: 'Создан',
  confirmed: 'Подтверждён',
  cooking: 'Готовится',
  delivering: 'Доставляется',
  delivered: 'Доставлен',
  cancelled: 'Отменён',
}
