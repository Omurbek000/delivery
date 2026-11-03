import { Navigate, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { json, tokens } from '../api'

const links = [
  { to: '/orders', label: 'Заказы' },
  { to: '/menu', label: 'Меню' },
  { to: '/promos', label: 'Акции и промокоды' },
  { to: '/users', label: 'Пользователи' },
  { to: '/stats', label: 'Дэшборд' },
]

export default function Layout() {
  const nav = useNavigate()
  if (!tokens.access) return <Navigate to="/login" replace />

  async function logout() {
    try {
      await json('POST', '/logout/', { refresh: tokens.refresh })
    } catch {
      // Токен мог уже протухнуть — выходим и так
    } finally {
      tokens.clear()
      nav('/login')
    }
  }

  const stored = localStorage.getItem('user')
  const user = stored ? (JSON.parse(stored) as { first_name?: string }) : null

  return (
    <div className="layout">
      <aside>
        <h1>Онигири</h1>
        <p className="muted">админ-панель</p>
        <nav>
          {links.map((link) => (
            <NavLink key={link.to} to={link.to}>
              {link.label}
            </NavLink>
          ))}
        </nav>
        <button onClick={logout}>Выйти</button>
        {user?.first_name && <p className="muted small">{user.first_name}</p>}
      </aside>
      <main>
        <Outlet />
      </main>
    </div>
  )
}
