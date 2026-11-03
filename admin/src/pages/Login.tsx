import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, tokens } from '../api'

type LoginResult = {
  access: string
  refresh: string
  user: { is_staff?: boolean; first_name?: string }
}

export default function Login() {
  const nav = useNavigate()
  const [phone, setPhone] = useState('+996')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const data = await api<LoginResult>('/login/', {
        method: 'POST',
        body: JSON.stringify({ phone, password }),
      })
      if (!data.user.is_staff) {
        setError('Вход в панель только для администраторов.')
        return
      }
      tokens.set(data.access, data.refresh)
      localStorage.setItem('user', JSON.stringify(data.user))
      nav('/orders')
    } catch (err) {
      setError((err as { message?: string }).message ?? 'Не удалось войти')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="login" onSubmit={submit}>
      <h1>Панель Онигири</h1>
      <label>
        Телефон
        <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+996..." />
      </label>
      <label>
        Пароль
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Пароль"
        />
      </label>
      {error && <p className="hint error">{error}</p>}
      <button disabled={busy}>{busy ? 'Входим...' : 'Войти'}</button>
    </form>
  )
}
