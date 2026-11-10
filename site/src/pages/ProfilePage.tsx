/** Профиль: имя, фамилия, фото (PATCH /profile/), выход. */

import { useState, type FormEvent } from 'react'
import { Navigate } from 'react-router-dom'
import { imgUrl } from '../api/client'
import { mutations } from '../api/service'
import { useAuth } from '../state/AuthContext'
import { useToast } from '../state/ToastContext'

export default function ProfilePage() {
  const auth = useAuth()
  const toast = useToast()
  const [first, setFirst] = useState(auth.user?.first_name ?? '')
  const [last, setLast] = useState(auth.user?.last_name ?? '')
  const [photo, setPhoto] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)

  if (!auth.isAuthed || !auth.user) return <Navigate to="/login?return=/profile" replace />

  const avatar = photo instanceof File ? URL.createObjectURL(photo) : imgUrl(auth.user.photo)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    try {
      let updated: typeof auth.user
      if (photo) {
        const fd = new FormData()
        if (first) fd.append('first_name', first)
        if (last) fd.append('last_name', last)
        fd.append('photo', photo)
        updated = await mutations.savePhoto(fd)
      } else {
        updated = await mutations.saveProfile({ first_name: first, last_name: last })
      }

      auth.setUser(updated)
      toast.push('Профиль обновлён', 'ok')
      setPhoto(null)
    } catch (err) {
      toast.push((err as { message?: string }).message ?? 'Не удалось сохранить', 'err')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="wrap prof-wrap" style={{ paddingTop: 120 }}>
      <span className="sover">Профиль</span>
      <h2 className="stitle" style={{ fontSize: 'clamp(20px, 3vw, 30px)' }}>
        Привет, <span className="grad">{auth.user.first_name || 'гость'}</span>
      </h2>

      <form className="prof-form" style={{ marginTop: 20 }} onSubmit={submit}>
        <div className="prof-ava">
          {avatar ? <img src={avatar} alt="Аватар" /> : <span className="noimg">👤</span>}
          <span className="muted small">
            {auth.user.phone}
            <br />
            PNG/JPG до 2 МБ
          </span>
        </div>
        <div className="co-row">
          <div>
            <label htmlFor="p-first" style={{ display: 'block', fontSize: 12.5, color: 'var(--muted)', marginBottom: 6 }}>
              Имя
            </label>
            <input id="p-first" value={first} onChange={(e) => setFirst(e.target.value)} />
          </div>
          <div>
            <label htmlFor="p-last" style={{ display: 'block', fontSize: 12.5, color: 'var(--muted)', marginBottom: 6 }}>
              Фамилия
            </label>
            <input id="p-last" value={last} onChange={(e) => setLast(e.target.value)} />
          </div>
        </div>
        <div>
          <label htmlFor="p-photo" style={{ display: 'block', fontSize: 12.5, color: 'var(--muted)', marginBottom: 6 }}>
            Фото профиля
          </label>
          <input
            id="p-photo"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(e) => setPhoto(e.target.files?.[0] ?? null)}
            style={{ fontSize: 13, paddingTop: 9 }}
          />
        </div>
        <button className="btn btn-fire" disabled={busy}>
          {busy ? 'Сохраняем…' : 'Сохранить'}
        </button>
        <button type="button" className="back-link" onClick={() => void auth.logout()}>
          🚪 Выйти
        </button>
      </form>
    </div>
  )
}
