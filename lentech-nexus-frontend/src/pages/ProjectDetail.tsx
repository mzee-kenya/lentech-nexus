import { useCallback, useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import Layout from '../components/Layout'
import { joinRequests, projects } from '../api/services'
import { ApiError, getErrorMessage } from '../api/client'
import type { Project, JoinRequest } from '../types/api'
import { useAuth } from '../contexts/AuthContext'
import './detail.css'

export default function ProjectDetail() {
  const { id } = useParams()
  const { user } = useAuth()
  const [project, setProject] = useState<Project | null>(null)
  const [requests, setRequests] = useState<JoinRequest[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [joining, setJoining] = useState(false)
  const [leaving, setLeaving] = useState(false)
  const [removingUser, setRemovingUser] = useState<number | null>(null)

  const load = useCallback(() => {
    return projects
      .get(Number(id))
      .then((data) => {
        setProject(data)
        if (data.viewer_is_owner) {
          projects
            .requests(Number(id))
            .then((reqs) => setRequests(reqs))
            .catch(() => setRequests([]))
        }
      })
      .catch((err) =>
        setError(
          err instanceof ApiError && err.status === 404
            ? 'Project not found'
            : 'Failed to load project',
        ),
      )
      .finally(() => setLoading(false))
  }, [id])

  useEffect(() => {
    void load()
  }, [load])

  const handleJoin = async () => {
    setJoining(true)
    setActionError(null)
    try {
      await projects.join(Number(id))
      await load()
    } catch (err) {
      setActionError(getErrorMessage(err))
    } finally {
      setJoining(false)
    }
  }

  const handleLeave = async () => {
    setLeaving(true)
    setActionError(null)
    try {
      await projects.leave(Number(id))
      await load()
    } catch (err) {
      setActionError(getErrorMessage(err))
    } finally {
      setLeaving(false)
    }
  }

  const handleRemoveMember = async (userId: number) => {
    setRemovingUser(userId)
    setActionError(null)
    try {
      await projects.removeMember(Number(id), userId)
      await load()
    } catch (err) {
      setActionError(getErrorMessage(err))
    } finally {
      setRemovingUser(null)
    }
  }

  const handleApprove = async (reqId: number) => {
    setActionError(null)
    try {
      await joinRequests.approve(reqId)
      await load()
    } catch {
      setActionError('Failed to approve request')
    }
  }

  const handleReject = async (reqId: number) => {
    setActionError(null)
    try {
      await joinRequests.reject(reqId)
      await load()
    } catch {
      setActionError('Failed to reject request')
    }
  }

  if (loading) return <Layout><p style={{padding:'40px'}}>Loading…</p></Layout>
  if (error) return <Layout><p style={{padding:'40px'}}>{error}</p></Layout>
  if (!project) return <Layout><p style={{padding:'40px'}}>Project not found</p></Layout>

  const canJoin = user && !project.viewer_is_owner && !project.viewer_is_member && project.viewer_request_status !== 'pending'
  const canLeave = user && !project.viewer_is_owner && project.viewer_is_member

  return (
    <Layout>
      <section className="detail-section">
        <div className="detail-card">
          <div>
            <h1>{project.title}</h1>
            <p className="detail-subtitle">Owned by {project.owner_display_name}</p>
            <p className="detail-text">{project.summary}</p>
          </div>
          {project.description && (
            <div>
              <h2>Description</h2>
              <p className="detail-text">{project.description}</p>
            </div>
          )}
          {project.technologies?.length > 0 && (
            <div>
              <h2>Technologies</h2>
              <div className="chip-row">
                {project.technologies.map((tech) => (
                  <span className="chip" key={tech}>{tech}</span>
                ))}
              </div>
            </div>
          )}
          <div className="detail-links">
            {project.repo_url && <a href={project.repo_url} target="_blank" rel="noreferrer">Repository</a>}
            {project.live_url && <a href={project.live_url} target="_blank" rel="noreferrer">Live demo</a>}
          </div>
          <div className="form-actions">
            {!user && <Link to="/login" className="button-ghost">Log in to collaborate</Link>}
            {canJoin && (
              <button className="button-primary" onClick={handleJoin} disabled={joining}>
                {joining ? 'Requesting…' : 'Request to join'}
              </button>
            )}
            {project.viewer_request_status === 'pending' && (
              <span className="link-muted">Join request pending</span>
            )}
            {canLeave && (
              <button className="button-ghost" onClick={handleLeave} disabled={leaving}>
                {leaving ? 'Leaving…' : 'Leave project'}
              </button>
            )}
          </div>
          {actionError && <p className="error-text">{actionError}</p>}
          <div>
            <h2>Members ({project.members?.length ?? 0})</h2>
            <ul>
              {project.members?.map((m) => (
                <li key={m.id}>
                  {m.display_name} ({m.role})
                  {project.viewer_is_owner && m.role !== 'owner' && (
                    <button className="link-muted" style={{marginLeft:12}} onClick={() => handleRemoveMember(m.user)}>
                      {removingUser === m.user ? 'Removing…' : 'Remove'}
                    </button>
                  )}
                </li>
              ))}
            </ul>
          </div>
          {project.viewer_is_owner && requests.length > 0 && (
            <div>
              <h2>Join requests</h2>
              <ul>
                {requests.map((req) => (
                  <li key={req.id}>
                    {req.requester_display_name}: {req.message || '—'}
                    <button className="button-primary" style={{marginLeft:12}} onClick={() => handleApprove(req.id)}>Approve</button>
                    <button className="button-ghost" style={{marginLeft:8}} onClick={() => handleReject(req.id)}>Reject</button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          <Link to="/projects" className="link-muted">← Back to projects</Link>
        </div>
      </section>
    </Layout>
  )
}