import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import type { User } from '../types'
import { login as apiLogin, register as apiRegister, googleLogin as apiGoogleLogin } from '../services/api'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string, fullName: string) => Promise<void>
  googleLogin: (credential: string) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => {},
  register: async () => {},
  googleLogin: async () => {},
  logout: () => {},
})

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const token = sessionStorage.getItem('token')
    const savedUser = sessionStorage.getItem('user')

    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser))
      } catch {
        sessionStorage.removeItem('token')
        sessionStorage.removeItem('user')
      }
    }
    setIsLoading(false)
  }, [])

  const login = async (email: string, password: string) => {
    const response = await apiLogin(email, password)
    sessionStorage.setItem('token', response.access_token)
    sessionStorage.setItem('user', JSON.stringify(response.user))
    setUser(response.user)
  }

  const register = async (email: string, username: string, password: string, fullName: string) => {
    const response = await apiRegister(email, username, password, fullName)
    sessionStorage.setItem('token', response.access_token)
    sessionStorage.setItem('user', JSON.stringify(response.user))
    setUser(response.user)
  }

  const googleLogin = async (credential: string) => {
    const response = await apiGoogleLogin(credential)
    sessionStorage.setItem('token', response.access_token)
    sessionStorage.setItem('user', JSON.stringify(response.user))
    setUser(response.user)
  }

  const logout = () => {
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, isAuthenticated: !!user, isLoading, login, register, googleLogin, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
