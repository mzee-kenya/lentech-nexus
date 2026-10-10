import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { projects } from '../api/services'
import { getErrorMessage } from '../api/client'
import './detail.css'

export default function ProjectCreate() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    title: '',
    summary: '',
    description: '',
    technologies: '',
    repo_url: '',
    live_url: '',
    status: 'planning',
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
        technologies: form.technologies
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
      }
      const data = await projects.create(payload)
      navigate(`/projects/${data.id}`)
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
          <h1>Create a project</h1>
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
              Technologies (comma-separated)
              <input name="technologies" value={form.technologies} onChange={handleChange} />
            </label>
            <label>
              Repository URL
              <input name="repo_url" value={form.repo_url} onChange={handleChange} />
            </label>
            <label>
              Live URL
              <input name="live_url" value={form.live_url} onChange={handleChange} />
            </label>
            <label>
              Status
              <select name="status" value={form.status} onChange={handleChange}>
                <option value="planning">Planning</option>
                <option value="in_progress">In Progress</option>
                <option value="completed">Completed</option>
                <option value="archived">Archived</option>
              </select>
            </label>
            <div className="form-actions">
              <button className="button-primary" type="submit" disabled={loading}>
                {loading ? 'Creating…' : 'Create project'}
              </button>
              <Link to="/projects" className="button-ghost">Cancel</Link>
            </div>
          </form>
        </div>
      </section>
    </Layout>
  )
}