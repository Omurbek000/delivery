/** Запросы к API вместе с ключами TanStack Query (фабрика queryOptions). */

import { queryOptions } from '@tanstack/react-query'
import { api, json } from './client'
import type {
  AiRecommendResult,
  AuthUser,
  Category,
  Dish,
  Favorite,
  LoginResult,
  Order,
  OrderCreateData,
  Promo,
} from '../types'

const authed = () => localStorage.getItem('onigiri-access') !== null

/** Пагинированный API отдаёт {count, results}, а некоторые списки — просто массив: приводим к массиву. */
type Page<T> = { results: T[] }

async function list<T>(path: string): Promise<T[]> {
  const data = await json<Page<T> | T[]>('GET', path)
  return Array.isArray(data) ? data : data.results
}

export const queries = {
  categories: () =>
    queryOptions({
      queryKey: ['categories'],
      queryFn: () => list<Category>('/categories/?page_size=100'),
    }),
  dishes: () =>
    queryOptions({
      queryKey: ['dishes'],
      queryFn: () => list<Dish>('/dishes/?page_size=100'),
    }),
  dish: (id: number) =>
    queryOptions({
      queryKey: ['dishes', id],
      queryFn: () => json<Dish>('GET', `/dishes/${id}/`),
    }),
  promos: () =>
    queryOptions({
      queryKey: ['promos'],
      queryFn: () => list<Promo>('/promo/?page_size=100'),
    }),
  favorites: () =>
    queryOptions({
      queryKey: ['favorites'],
      queryFn: () => list<Favorite>('/favorites/'),
      enabled: authed(),
    }),
  orders: () =>
    queryOptions({
      queryKey: ['orders'],
      queryFn: () => list<Order>('/orders/?page_size=100'),
      enabled: authed(),
    }),
  profile: () =>
    queryOptions({
      queryKey: ['profile'],
      queryFn: () => json<AuthUser>('GET', '/profile/'),
      enabled: authed(),
    }),
}

/** Квиз-подбор: 4 ответа-настроения собираются в один запрос к AI. */
export function recommendQuery(step: string[]): string {
  return `Подбери блюдо из меню доставки «Онигири»: желание «${step[0]}», размер еды — «${step[1]}», острота — «${step[2]}», бюджет — «${step[3]}». Ответь кратко на русском.`
}

export const mutations = {
  login: (phone: string, password: string) => json<LoginResult>('POST', '/login/', { phone, password }),
  register: (phone: string, first_name: string, last_name: string, password: string) =>
    json<LoginResult>('POST', '/register/', { phone, first_name, last_name, password }),
  logout: (refresh: string) => json('POST', '/logout/', { refresh }),
  saveProfile: (patch: Partial<AuthUser>) => json<AuthUser>('PATCH', '/profile/', patch),
  savePhoto: (data: FormData) => api<AuthUser>('/profile/', { method: 'PATCH', body: data }),
  createOrder: (data: OrderCreateData) => json<Order>('POST', '/orders/create/', data),
  cancelOrder: (id: number) => json<Order>('POST', `/orders/${id}/cancel/`),
  addFavorite: (dishId: number) => json<Favorite>('POST', '/favorites/create/', { dish_id: dishId }),
  removeFavorite: (id: number) => json('DELETE', `/favorites/${id}/delete/`),
  aiRecommend: (query: string) => json<AiRecommendResult>('POST', '/ai/recommend/', { query }),
}
