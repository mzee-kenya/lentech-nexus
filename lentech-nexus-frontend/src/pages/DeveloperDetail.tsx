import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { developers } from '../api/services'
import { ApiError } from '../api/client'
import type { Developer } from '../types/api'
import './detail.css'

export default function DeveloperDetail() {
  const { id } = useParams()
  const [dev, setDev] = useState<Developer | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    developers
      .get(Number(id))
      .then((data) => {
        if (active) setDev(data)
      })
      .catch((err) => {
        if (!active) return
        setError(
          err instanceof ApiError && err.status === 404
            ? 'Developer not found'
            : 'Failed to load developer',
        )
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [id])

  if (loading) return <Layout><p style={{padding:'40px'}}>Loading…</p></Layout>
  if (error) return <Layout><p style={{padding:'40px'}}>{error}</p></Layout>
  if (!dev) return <Layout><p style={{padding:'40px'}}>Developer not found</p></Layout>

  return (
    <Layout>
      <section className="detail-section">
        <div className="detail-card">
          <div className="detail-header">
            <div className="avatar">
              {dev.profile_image ? <img src={dev.profile_image} alt={dev.name} /> : <span>{dev.name[0]?.toUpperCase()}</span>}
            </div>
            <div>
              <h1>{dev.name}</h1>
              <p className="detail-subtitle">{dev.role || '—'}</p>
              <div className="detail-links">
                {dev.github_url && <a href={dev.github_url} target="_blank" rel="noreferrer">GitHub</a>}
                {dev.linkedin_url && <a href={dev.linkedin_url} target="_blank" rel="noreferrer">LinkedIn</a>}
                {dev.website_url && <a href={dev.website_url} target="_blank" rel="noreferrer">Website</a>}
              </div>
            </div>
          </div>
          {dev.bio && (
            <div>
              <h2>Bio</h2>
              <p className="detail-text">{dev.bio}</p>
            </div>
          )}
          {dev.skills.length > 0 && (
            <div>
              <h2>Skills</h2>
              <div className="chip-row">
                {dev.skills.map((skill) => (
                  <span className="chip" key={skill}>{skill}</span>
                ))}
              </div>
            </div>
          )}
          <Link to="/developers" className="link-muted">← Back to developers</Link>
        </div>
      </section>
    </Layout>
  )
}