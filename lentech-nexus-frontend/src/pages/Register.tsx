import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import './auth.css'

export default function Register() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    password_confirm: '',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await register(form)
      navigate('/profile')
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
          <h1>Create an account</h1>
          {error && <p className="auth-error">{error}</p>}
          <label>
            Username
            <input name="username" value={form.username} onChange={handleChange} required />
          </label>
          <label>
            Email
            <input name="email" type="email" value={form.email} onChange={handleChange} required />
          </label>
          <label>
            Password
            <input name="password" type="password" value={form.password} onChange={handleChange} required />
          </label>
          <label>
            Confirm password
            <input
              name="password_confirm"
              type="password"
              value={form.password_confirm}
              onChange={handleChange}
              required
            />
          </label>
          <button type="submit" disabled={loading}>
            {loading ? 'Creating…' : 'Create account'}
          </button>
          <p>
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </form>
      </section>
    </Layout>
  )
}