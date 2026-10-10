import { useCallback, useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { ideas } from '../api/services'
import { ApiError, getErrorMessage } from '../api/client'
import type { Idea } from '../types/api'
import { useAuth } from '../contexts/AuthContext'
import './detail.css'

export default function IdeaDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const [idea, setIdea] = useState<Idea | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [interested, setInterested] = useState(false)

  const load = useCallback(() => {
    return ideas
      .get(Number(id))
      .then((data) => setIdea(data))
      .catch((err) =>
        setError(
          err instanceof ApiError && err.status === 404 ? 'Idea not found' : 'Failed to load idea',
        ),
      )
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const handleInterest = async () => {
    setInterested(true)
    setActionError(null)
    try {
      await ideas.interest(Number(id))
      await load()
    } catch (err) {
      setActionError(getErrorMessage(err))
    } finally {
      setInterested(false)
    }
  }

  if (loading) return <Layout><p style={{padding:'40px'}}>Loading…</p></Layout>
  if (error) return <Layout><p style={{padding:'40px'}}>{error}</p></Layout>
  if (!idea) return <Layout><p style={{padding:'40px'}}>Idea not found</p></Layout>

  const canExpress = user && !idea.viewer_is_author && idea.viewer_interest_status !== 'pending' && (idea.status === 'open' || idea.status === 'in_progress')

  return (
    <Layout>
      <section className="detail-section">
        <div className="detail-card">
          <div>
            <h1>{idea.title}</h1>
            <p className="detail-subtitle">Shared by {idea.author_display_name}</p>
            <p className="detail-text">{idea.summary}</p>
          </div>
          {idea.description && (
            <div>
              <h2>Description</h2>
              <p className="detail-text">{idea.description}</p>
            </div>
          )}
          {idea.tags?.length > 0 && (
            <div>
              <h2>Tags</h2>
              <div className="chip-row">
                {idea.tags.map((tag) => (
                  <span className="chip" key={tag}>{tag}</span>
                ))}
              </div>
            </div>
          )}
          <div className="form-actions">
            {!user && <Link to="/login" className="button-ghost">Log in to get involved</Link>}
            {canExpress && (
              <button className="button-primary" onClick={handleInterest} disabled={interested}>
                {interested ? 'Submitting…' : 'Express interest'}
              </button>
            )}
            {idea.viewer_interest_status === 'pending' && (
              <span className="link-muted">Interest request pending</span>
            )}
          </div>
          {actionError && <p className="error-text">{actionError}</p>}
          <Link to="/ideas" className="link-muted">← Back to ideas</Link>
        </div>
      </section>
    </Layout>
  )
}