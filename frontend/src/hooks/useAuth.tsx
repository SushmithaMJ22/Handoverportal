import { createContext, useContext, useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const AuthContext = createContext<any>(null)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<any>(null)
  const [token, setToken] = useState<string | null>(null)
  const navigate = useNavigate()

  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    if (storedToken && storedUser) {
      setToken(storedToken)
      setUser(JSON.parse(storedUser))
    }
  }, [])

  const login = (tokenValue: string, userValue: any, refreshTokenValue?: string) => {
    localStorage.setItem('token', tokenValue)
    localStorage.setItem('user', JSON.stringify(userValue))
    if (refreshTokenValue) {
      localStorage.setItem('refresh_token', refreshTokenValue)
    }
    setToken(tokenValue)
    setUser(userValue)
  }

  const logout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    setToken(null)
    setUser(null)
    navigate('/login')
  }

  /** Display name: full_name if set, otherwise username */
  const displayName: string = user?.full_name || user?.username || ''

  const isSuperAdmin = user?.role === 'super_admin'
  const isAdmin = user?.role === 'admin' || user?.role === 'super_admin'
  const isUser = user?.role === 'user'

  return (
    <AuthContext.Provider value={{ user, token, login, logout, displayName, isSuperAdmin, isAdmin, isUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
