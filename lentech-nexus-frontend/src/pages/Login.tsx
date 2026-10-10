import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import './auth.css'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const state = location.state as { from?: { pathname?: string } } | null
  const from = state?.from?.pathname ?? '/profile'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await login(username, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <section className="auth-section">
        <form className="auth-form" onSubmit={handleSubmit}>
          <h1>Log in</h1>
          {error && <p className="auth-error">{error}</p>}
          <label>
            Username or email
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
          <p>
            New to Lentech Nexus? <Link to="/register">Create an account</Link>
          </p>
        </form>
      </section>
    </Layout>
  )
}