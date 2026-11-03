/** Общие типы данных API. */

export type Category = { id: number; name: string }

export type Dish = {
  id: number
  name: string
  description: string
  ingredients: string
  price: string
  image: string | null
  is_available: boolean
  category: Category | null
}

export type PromoCode = {
  id: number
  code: string
  discount_percent: string
  is_active: boolean
  valid_until: string | null
  min_order_amount: string
}

export type Promo = {
  id: number
  title: string
  description: string
  old_price: string
  discount_percent: string
  dish: Dish | null
  image: string | null
  is_active: boolean
  sort_order: number
}

export type OrderItem = {
  id: number
  dish: Dish | null
  quantity: number
  price_at_order: string
}

export type Order = {
  id: number
  user: number
  created_at: string
  status: string
  street: string
  house: string
  apartment: string
  total_price: string
  discount_amount: string
  comment: string
  order_item: OrderItem[]
}

export type AdminUser = {
  id: number
  phone: string
  first_name: string
  last_name: string
  photo: string | null
  is_active: boolean
  is_staff: boolean
  date_joined: string
}

export type Stats = {
  today: { orders: number; revenue: string }
  status_counts: Record<string, number>
  top_dishes: { name: string; qty: number; revenue: string }[]
}

/** Стандартная DRF-страница с пагинацией. */
export type Paged<T> = { count: number; results: T[] }
