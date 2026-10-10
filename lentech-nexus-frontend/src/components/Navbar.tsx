import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import './Navbar.css'

function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)

  const handleLogout = async () => {
    await logout()
    setOpen(false)
    navigate('/')
  }

  return (
    <nav className="navbar">
      <Link to="/" className="brand" onClick={() => setOpen(false)}>
        Lentech Nexus
      </Link>

      <button
        type="button"
        className="nav-toggle"
        aria-label="Toggle navigation"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        ☰
      </button>

      <ul className={`nav-links ${open ? 'open' : ''}`}>
        <li>
          <Link to="/" onClick={() => setOpen(false)}>Home</Link>
        </li>
        <li>
          <Link to="/projects" onClick={() => setOpen(false)}>Projects</Link>
        </li>
        <li>
          <Link to="/ideas" onClick={() => setOpen(false)}>Ideas</Link>
        </li>
        <li>
          <Link to="/developers" onClick={() => setOpen(false)}>Developers</Link>
        </li>
        {user ? (
          <>
            <li>
              <Link to="/profile" onClick={() => setOpen(false)}>Profile</Link>
            </li>
            <li>
              <button type="button" className="nav-logout" onClick={handleLogout}>
                Log out
              </button>
            </li>
          </>
        ) : (
          <>
            <li>
              <Link to="/login" onClick={() => setOpen(false)}>Log in</Link>
            </li>
            <li>
              <Link to="/register" className="nav-cta" onClick={() => setOpen(false)}>
                Sign up
              </Link>
            </li>
          </>
        )}
      </ul>
    </nav>
  )
}

export default Navbar