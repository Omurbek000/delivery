/** Хедер: логотип, меню, корзина со счётчиком, профиль. */

import { useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useCart } from '../state/CartContext'

const NAV = [
  { href: '#menu', label: 'Меню' },
  { href: '#how', label: 'Как это работает' },
  { href: '#quiz', label: 'Квиз' },
  { href: '#rev', label: 'Отзывы' },
  { href: '#contacts', label: 'Контакты' },
]

export function Header() {
  const { user, isAuthed, logout } = useAuth()
  const cart = useCart()
  const nav = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)
  const prevCount = useRef(cart.count)

  const bumped = cart.count > prevCount.current

  function go(path: string) {
    setMenuOpen(false)
    nav(path)
  }

  return (
    <header>
      <div className="wrap hin">
        <Link to="/" className="logo">
          <span className="logo-box">🍣</span>
          <span>
            Онигири
            <small>доставка еды 24/7</small>
          </span>
        </Link>

        <nav className="main-nav">
          {NAV.map((item) => (
            <a key={item.href} href={item.href}>
              {item.label}
            </a>
          ))}
        </nav>

        <div className="hacts">
          <button
            className={`icon-btn cart-btn${bumped ? ' bump' : ''}`}
            aria-label="Корзина"
            onClick={() => {
              prevCount.current = cart.count
              cart.open()
            }}
          >
            🛒 <span className="cnt">{cart.count}</span>
          </button>
          {isAuthed ? (
            <Link className="icon-btn" title="Профиль" aria-label="Профиль" to="/orders">
              ↺
            </Link>
          ) : null}
          <Link className="icon-btn" title={isAuthed ? 'Профиль' : 'Войти'} aria-label="Профиль" to={isAuthed ? '/profile' : '/login'}>
            👤
          </Link>
          <button
            className={`icon-btn burger${menuOpen ? ' open' : ''}`}
            aria-label="Меню"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((o) => !o)}
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>
      </div>

      <div className={`mmenu${menuOpen ? ' open' : ''}`}>
        {NAV.map((item) => (
          <a key={item.href} href={item.href} onClick={() => setMenuOpen(false)}>
            {item.label}
          </a>
        ))}
        {isAuthed ? (
          <>
            <a href="#contacts" onClick={() => void logout()}>
              🚪 Выйти{user ? ` (${user.first_name || user.phone})` : ''}
            </a>
          </>
        ) : (
          <a href="/login" onClick={(e) => { e.preventDefault(); go('/login') }}>
            👤 Войти
          </a>
        )}
      </div>
    </header>
  )
}
