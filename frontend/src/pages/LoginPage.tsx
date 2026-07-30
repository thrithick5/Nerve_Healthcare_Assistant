import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
import { Link } from 'react-router-dom'
import { CredentialResponse } from '@react-oauth/google'
import { GoogleSignInButton } from '../components/GoogleSignInButton'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, googleLogin } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
    } catch (err: any) {
      setError(err.message || 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSuccess = async (response: CredentialResponse) => {
    if (response.credential) {
      try {
        await googleLogin(response.credential)
      } catch (err: any) {
        setError(err.message || 'Google sign-in failed')
      }
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-white dark:bg-[#212121]">
      <div className="w-full max-w-sm px-8 py-10">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Sign in</h1>
          <p className="mt-2 text-sm text-gray-500 dark:text-neutral-400">to continue to Nerve</p>
        </div>

        <div className="space-y-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 text-sm text-center">
                {error}
              </div>
            )}

            <div className="space-y-3">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
                required
                className="w-full px-4 py-3 rounded-xl border text-sm bg-white dark:bg-[#212121] border-gray-200 dark:border-[#383838] text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-neutral-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
              />

              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                className="w-full px-4 py-3 rounded-xl border text-sm bg-white dark:bg-[#212121] border-gray-200 dark:border-[#383838] text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-neutral-500 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl text-sm font-semibold text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-sm"
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <div className="flex items-center gap-3 py-1">
            <div className="flex-1 h-px bg-gray-200 dark:bg-[#383838]" />
            <span className="text-xs text-gray-400 dark:text-neutral-500">or continue with</span>
            <div className="flex-1 h-px bg-gray-200 dark:bg-[#383838]" />
          </div>

          <GoogleSignInButton
            onSuccess={handleGoogleSuccess}
            onError={() => setError('Google sign-in failed')}
          />
        </div>

        <p className="text-center text-sm mt-8 text-gray-500 dark:text-neutral-400">
          No account?{' '}
          <Link to="/register" className="text-blue-600 hover:text-blue-700 font-medium">Sign up</Link>
        </p>
      </div>
    </div>
  )
}
