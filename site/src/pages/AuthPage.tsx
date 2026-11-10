/** Вход/регистрация по номеру телефона и паролю. */

import { useState, type FormEvent } from 'react'
import { Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../state/AuthContext'
import { useCart } from '../state/CartContext'
import { useToast } from '../state/ToastContext'

export default function AuthPage() {
  const auth = useAuth()
  const cart = useCart()
  const nav = useNavigate()
  const [params] = useSearchParams()
  const toast = useToast()

  const [tab, setTab] = useState<'login' | 'register'>('login')
  const [phone, setPhone] = useState('+996')

  /** Нормализует ввод: хвост из 9 цифр всегда приклеивается к префиксу +996 (дубль префикса невозможен). */
  function setPhoneInput(v: string) {
    let digits = v.replace(/\D/g, '')
    if (digits.startsWith('0')) digits = digits.replace(/^0+/, '')
    if (digits.length > 9) digits = digits.slice(-9)
    setPhone(digits ? `+996${digits}` : '')
  }
  const [password, setPassword] = useState('')
  const [first, setFirst] = useState('')
  const [last, setLast] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (auth.isAuthed) return <Navigate to="/" replace />

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      if (tab === 'login') {
        await auth.login(phone, password)
        toast.push('Рады видеть снова!', 'ok')
      } else {
        await auth.register(phone, first, last, password)
        toast.push('Аккаунт создан, добро пожаловать!', 'ok')
      }
      nav(params.get('return') ?? '/')
    } catch (err) {
      setError((err as { message?: string }).message ?? 'Не удалось войти')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-wrap" style={{ paddingTop: 0 }}>
      <span className="sover">{cart.count > 0 ? 'В корзине ждёт заказ' : 'Онигири'}</span>
      <h2 className="stitle" style={{ fontSize: 'clamp(20px, 3vw, 30px)' }}>
        {tab === 'login' ? (
          <>
            С возвращением, <span className="grad">огненный</span>
          </>
        ) : (
          <>
            Присоединяйся к <span className="grad">нашим</span>
          </>
        )}
      </h2>

      <div className="auth-tabs" style={{ marginTop: 20 }}>
        <button className={tab === 'login' ? 'on' : ''} onClick={() => setTab('login')}>
          Вход
        </button>
        <button className={tab === 'register' ? 'on' : ''} onClick={() => setTab('register')}>
          Регистрация
        </button>
      </div>

      <form className="auth-form" onSubmit={submit}>
        <div>
          <label htmlFor="a-phone" className="muted" style={{ display: 'block', fontSize: 12.5, marginBottom: 6 }}>
            Телефон
          </label>
          <input id="a-phone" value={phone} onChange={(e) => setPhoneInput(e.target.value)} placeholder="+996 XXX XXX XXX" inputMode="tel" required />
        </div>
        <div>
          <label htmlFor="a-pass" style={{ display: 'block', fontSize: 12.5, color: 'var(--muted)', marginBottom: 6 }}>
            Пароль
          </label>
          <input
            id="a-pass"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
          />
        </div>
        {tab === 'register' && (
          <div className="co-row">
            <div>
              <label htmlFor="a-first" style={{ display: 'block', fontSize: 12.5, color: 'var(--muted)', marginBottom: 6 }}>
                Имя
              </label>
              <input id="a-first" value={first} onChange={(e) => setFirst(e.target.value)} required />
            </div>
            <div>
              <label htmlFor="a-last" style={{ display: 'block', fontSize: 12.5, color: 'var(--muted)', marginBottom: 6 }}>
                Фамилия
              </label>
              <input id="a-last" value={last} onChange={(e) => setLast(e.target.value)} />
            </div>
          </div>
        )}
        {error && <p className="ferr" role="alert">{error}</p>}
        <button className="btn btn-fire" disabled={busy}>
          {busy ? 'Входим…' : tab === 'login' ? 'Войти' : 'Создать аккаунт'}
        </button>
      </form>
    </div>
  )
}
