/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'

import { auth } from '../api/services'
import type { User } from '../types/api'

interface AuthContextValue {
  user: User | null
  loading: boolean
  error: string | null
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  register: (payload: {
    username: string
    email: string
    password: string
    password_confirm: string
  }) => Promise<void>
  refresh: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(() => {
    return auth
      .me()
      .then((me) => setUser(me))
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const login = useCallback(
    async (username: string, password: string) => {
      setError(null)
      const u = await auth.login({ username, password })
      setUser(u)
    },
    [],
  )

  const logout = useCallback(async () => {
    try {
      await auth.logout()
    } finally {
      setUser(null)
    }
  }, [])

  const register = useCallback(
    async (payload: {
      username: string
      email: string
      password: string
      password_confirm: string
    }) => {
      setError(null)
      const u = await auth.register(payload)
      setUser(u)
    },
    [],
  )

  const value = useMemo(
    () => ({ user, loading, error, login, logout, register, refresh }),
    [user, loading, error, login, logout, register, refresh],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}