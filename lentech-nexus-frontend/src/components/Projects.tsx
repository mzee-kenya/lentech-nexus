import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import ProjectCard from './ProjectCard'
import { projects as projectsApi } from '../api/services'
import type { Project } from '../types/api'
import './Projects.css'

function Projects() {
  const [items, setItems] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    projectsApi
      .list({ page_size: '6' })
      .then((data) => {
        if (active) setItems(data.results)
      })
      .catch(() => {
        if (active) setError('We could not load projects right now.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <section className="projects">
      <h2>Featured Projects</h2>

      <p>
        Discover projects being built by the Lentech Nexus community.
      </p>

      {loading && <p className="projects-status">Loading projects…</p>}
      {error && <p className="projects-status">{error}</p>}
      {!loading && !error && items.length === 0 && (
        <p className="projects-status">No projects yet. Be the first to publish one.</p>
      )}

      <div className="project-grid">
        {items.map((project) => (
          <ProjectCard
            key={project.id}
            id={project.id}
            name={project.title}
            description={project.summary || project.technologies.join(', ')}
          />
        ))}
      </div>

      <div className="section-actions">
        <Link to="/projects" className="section-link">Browse all projects →</Link>
        <Link to="/projects/new" className="section-link">Publish a project</Link>
      </div>
    </section>
  )
}

export default Projects