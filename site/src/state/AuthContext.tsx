/** AuthContext: логин/регистрация/выход, пользователь в localStorage. */

import { createContext, useContext, useEffect, useState, useMemo, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { tokens, json } from '../api/client'
import type { AuthUser } from '../types'
import { mutations } from '../api/service'
import { useQueryClient } from '@tanstack/react-query'

interface AuthCtx {
  user: AuthUser | null
  isAuthed: boolean
  login: (phone: string, password: string) => Promise<void>
  register: (phone: string, first: string, last: string, password: string) => Promise<void>
  logout: () => Promise<void>
  setUser: (u: AuthUser | null) => void
}

const Ctx = createContext<AuthCtx | null>(null)

function readUser(): AuthUser | null {
  const raw = localStorage.getItem('onigiri-user')
  if (!raw) return null
  try {
    return JSON.parse(raw) as AuthUser
  } catch {
    return null
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUserState] = useState<AuthUser | null>(readUser)
  const navigate = useNavigate()
  const queryClient = useQueryClient()

  // Слушаем отказ токена из api-клиента: сбрасываем пользователя
  useEffect(() => {
    function reset() {
      setUserState(null)
      queryClient.removeQueries({ queryKey: ['favorites'] })
      queryClient.removeQueries({ queryKey: ['orders'] })
      queryClient.removeQueries({ queryKey: ['profile'] })
    }
    addEventListener('onigiri:auth-expired', reset)
    return () => removeEventListener('onigiri:auth-expired', reset)
  }, [queryClient])

  const functions = useMemo(
    () => ({
      async login(phone: string, password: string) {
        const data = await mutations.login(phone, password)
        tokens.set(data.access, data.refresh)
        setUserState(data.user)
        localStorage.setItem('onigiri-user', JSON.stringify(data.user))
        queryClient.invalidateQueries({ queryKey: ['favorites'] })
        queryClient.invalidateQueries({ queryKey: ['orders'] })
      },
      async register(phone: string, first: string, last: string, password: string) {
        const data = await mutations.register(phone, first, last, password)
        tokens.set(data.access, data.refresh)
        setUserState(data.user)
        localStorage.setItem('onigiri-user', JSON.stringify(data.user))
      },
      async logout() {
        try {
          await mutations.logout(tokens.refresh ?? '')
        } catch {
          // Токен мог протухнуть — всё равно выходим
        } finally {
          tokens.clear()
          setUserState(null)
          queryClient.removeQueries({ queryKey: ['favorites'] })
          queryClient.removeQueries({ queryKey: ['orders'] })
          navigate('/')
        }
      },
      setUser(u: AuthUser | null) {
        setUserState(u)
        if (u) localStorage.setItem('onigiri-user', JSON.stringify(u))
        else localStorage.removeItem('onigiri-user')
      },
    }),
    [queryClient, navigate],
  )

  const value = useMemo(
    () => ({ user, isAuthed: user !== null && tokens.access !== null, ...functions }),
    [user, functions],
  )

  // Обновляем профиль, если access жив — чтобы имя/фото были актуальны
  useEffect(() => {
    if (value.isAuthed) {
      json<AuthUser>('GET', '/profile/')
        .then((fresh) => value.setUser(fresh))
        .catch(() => undefined)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useAuth(): AuthCtx {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useAuth вне AuthProvider')
  return ctx
}
