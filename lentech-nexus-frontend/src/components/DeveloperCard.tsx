import { Link } from 'react-router-dom'

// Defines the information required to display a developer card.
type DeveloperCardProps = {
  id: number
  name: string
  role: string
  initials: string
  skills: string[]
  avatarUrl?: string
}

function DeveloperCard({
  id,
  name,
  role,
  initials,
  skills,
  avatarUrl,
}: DeveloperCardProps) {
  return (
    <div className="developer-card">

      <div className="developer-avatar">
        {avatarUrl ? <img src={avatarUrl} alt={name} /> : initials}
      </div>

      <h3>{name}</h3>

      <p>{role}</p>

      {/* Display each developer's skills as small tags. */}
      <div className="developer-skills">
        {skills.map((skill) => (
          <span key={skill}>{skill}</span>
        ))}
      </div>

      <Link to={`/developers/${id}`}>View Profile</Link>

    </div>
  )
}
export default DeveloperCard