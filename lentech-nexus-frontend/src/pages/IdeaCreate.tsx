import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { ideas } from '../api/services'
import { getErrorMessage } from '../api/client'
import './detail.css'

export default function IdeaCreate() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    title: '',
    summary: '',
    description: '',
    tags: '',
    status: 'open',
  })
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const payload = {
        ...form,
        tags: form.tags
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      }
      const data = await ideas.create(payload)
      navigate(`/ideas/${data.id}`)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <section className="detail-section">
        <div className="detail-card">
          <h1>Share an idea</h1>
          {error && <p className="error-text">{error}</p>}
          <form className="form-grid" onSubmit={handleSubmit}>
            <label>
              Title
              <input name="title" value={form.title} onChange={handleChange} required />
            </label>
            <label>
              Summary
              <input name="summary" value={form.summary} onChange={handleChange} />
            </label>
            <label>
              Description
              <textarea name="description" rows={5} value={form.description} onChange={handleChange} />
            </label>
            <label>
              Tags (comma-separated)
              <input name="tags" value={form.tags} onChange={handleChange} />
            </label>
            <label>
              Status
              <select name="status" value={form.status} onChange={handleChange}>
                <option value="open">Open</option>
                <option value="in_progress">In Progress</option>
                <option value="realized">Realized</option>
                <option value="archived">Archived</option>
              </select>
            </label>
            <div className="form-actions">
              <button className="button-primary" type="submit" disabled={loading}>
                {loading ? 'Submitting…' : 'Submit idea'}
              </button>
              <Link to="/ideas" className="button-ghost">Cancel</Link>
            </div>
          </form>
        </div>
      </section>
    </Layout>
  )
}