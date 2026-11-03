import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { errText, fetchAll, imgUrl, json, tokens } from '../api'
import type { AdminUser } from '../types'

export default function Users() {
  const qc = useQueryClient()
  const [error, setError] = useState('')

  const me = tokens.access ? getUserFromStorage() : null

  const users = useQuery({ queryKey: ['users'], queryFn: () => fetchAll<AdminUser>('/users/') })

  const ban = useMutation({
    mutationFn: ({ id, isActive }: { id: number; isActive: boolean }) =>
      json<AdminUser>('PATCH', `/users/${id}/ban/`, { is_active: isActive }),
    onSuccess: () => {
      setError('')
      qc.invalidateQueries({ queryKey: ['users'] })
      qc.invalidateQueries({ queryKey: ['users-map'] })
    },
    onError: (e) => setError(errText(e)),
  })

  if (users.isLoading) return <p>Загружаем пользователей...</p>
  if (users.isError) return <p className="error">Не удалось загрузить: {errText(users.error)}</p>

  return (
    <div>
      <h2>Пользователи</h2>
      {error && <p className="hint error">{error}</p>}
      <table>
        <thead>
          <tr>
            <th>Фото</th>
            <th>Имя</th>
            <th>Телефон</th>
            <th>Админ</th>
            <th>Зарегистрирован</th>
            <th>Действия</th>
          </tr>
        </thead>
        <tbody>
          {(users.data ?? []).map((user) => (
            <tr key={user.id} data-user-id={user.id}>
              <td>
                {user.photo ? (
                  <img className="thumb" src={imgUrl(user.photo) ?? ''} alt="" />
                ) : (
                  <span className="muted">—</span>
                )}
              </td>
              <td>
                {`${user.first_name} ${user.last_name}`.trim() || '—'}
                <span className={`badge ${user.is_active ? 'ok' : 'bad'}`}>
                  {user.is_active ? 'активен' : 'забанен'}
                </span>
              </td>
              <td>{user.phone}</td>
              <td>{user.is_staff ? <span className="badge warn">админ</span> : '—'}</td>
              <td>{new Date(user.date_joined).toLocaleDateString('ru-RU')}</td>
              <td>
                <button
                  disabled={user.id === me?.id || ban.isPending}
                  title={user.id === me?.id ? 'Нельзя заблокировать самого себя' : ''}
                  onClick={() => ban.mutate({ id: user.id, isActive: !user.is_active })}
                >
                  {user.is_active ? 'Забанить' : 'Разбанить'}
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function getUserFromStorage(): { id?: number } | null {
  try {
    return JSON.parse(localStorage.getItem('user') ?? 'null')
  } catch {
    return null
  }
}
