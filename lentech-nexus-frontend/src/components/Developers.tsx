import { useEffect, useState } from 'react'
import './Developers.css'
import DeveloperCard from './DeveloperCard'
import { developers as developersApi } from '../api/services'
import type { Developer } from '../types/api'

function initialsFor(name: string) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

function Developers() {
  const [items, setItems] = useState<Developer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    developersApi
      .list({ page_size: '6' })
      .then((data) => {
        if (active) setItems(data.results)
      })
      .catch(() => {
        if (active) setError('We could not load developers right now.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [])

  return (
    <section className="developers">

      <h2>Meet the Builders</h2>

      <p>
        Connect with developers, designers, and problem solvers building
        meaningful solutions.
      </p>

      {loading && <p className="developers-status">Loading developers…</p>}
      {error && <p className="developers-status">{error}</p>}
      {!loading && !error && items.length === 0 && (
        <p className="developers-status">No developer profiles yet.</p>
      )}

      <div className="developer-grid">

        {items.map((developer) => (
          <DeveloperCard
            key={developer.id}
            id={developer.id}
            name={developer.name}
            role={developer.role}
            initials={initialsFor(developer.name)}
            skills={developer.skills}
            avatarUrl={developer.profile_image || undefined}
          />
        ))}

      </div>

    </section>
  )
}

export default Developers