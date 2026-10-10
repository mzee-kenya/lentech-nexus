import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { chat } from '../api/services'
import {
  ChatIcon,
  CloseIcon,
  DevelopersIcon,
  FeedIcon,
  HomeIcon,
  IdeasIcon,
  LogoutIcon,
  MenuIcon,
  ProfileIcon,
  ProjectsIcon,
} from './icons'
import './Navbar.css'

type NavItemProps = {
  to: string
  label: string
  icon: ReactNode
  onClick: () => void
  badge?: number
}

function NavItem({ to, label, icon, onClick, badge = 0 }: NavItemProps) {
  return (
    <li>
      <NavLink
        to={to}
        end={to === '/'}
        className={({ isActive }) =>
          ['nav-link', isActive ? 'active' : '', badge > 0 ? 'has-badge' : '']
            .filter(Boolean)
            .join(' ')
        }
        onClick={onClick}
        aria-label={badge > 0 ? `${label}, ${badge} unread` : label}
      >
        <span className="nav-icon">{icon}</span>
        <span className="nav-label">{label}</span>
        {badge > 0 && <span className="nav-badge">{badge > 99 ? '99+' : badge}</span>}
      </NavLink>
    </li>
  )
}

function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [unread, setUnread] = useState(0)

  // Poll the unread total so the Messages icon can show a live badge. We stop
  // as soon as the user logs out and clean up the interval on unmount.
  useEffect(() => {
    if (!user) return
    let active = true
    const load = async () => {
      try {
        const data = await chat.unreadCount()
        if (active) setUnread(data.unread)
      } catch {
        // Network hiccups should never break navigation; keep the last value.
      }
    }
    void load()
    const timer = window.setInterval(load, 25000)
    return () => {
      active = false
      window.clearInterval(timer)
    }
  }, [user])

  const close = () => setOpen(false)

  const handleLogout = async () => {
    await logout()
    close()
    navigate('/')
  }

  return (
    <nav className="navbar">
      <Link to="/" className="brand" onClick={close}>
        <span className="brand-mark">LN</span>
        <span className="brand-name">Lentech Nexus</span>
      </Link>

      <button
        type="button"
        className="nav-toggle"
        aria-label="Toggle navigation"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        {open ? <CloseIcon size={22} /> : <MenuIcon size={22} />}
      </button>

      <ul className={`nav-links ${open ? 'open' : ''}`}>
        <NavItem to="/" label="Home" icon={<HomeIcon />} onClick={close} />
        <NavItem to="/projects" label="Projects" icon={<ProjectsIcon />} onClick={close} />
        <NavItem to="/ideas" label="Ideas" icon={<IdeasIcon />} onClick={close} />
        <NavItem to="/feed" label="Feed" icon={<FeedIcon />} onClick={close} />
        <NavItem to="/developers" label="Developers" icon={<DevelopersIcon />} onClick={close} />

        {user ? (
          <>
            <NavItem
              to="/chat"
              label="Messages"
              icon={<ChatIcon />}
              onClick={close}
              badge={unread}
            />
            <NavItem to="/profile" label="Profile" icon={<ProfileIcon />} onClick={close} />
            <li>
              <button type="button" className="nav-logout" onClick={handleLogout}>
                <span className="nav-icon">
                  <LogoutIcon />
                </span>
                <span className="nav-label">Log out</span>
              </button>
            </li>
          </>
        ) : (
          <>
            <li>
              <Link to="/login" className="nav-link" onClick={close}>
                <span className="nav-icon">
                  <ProfileIcon />
                </span>
                <span className="nav-label">Log in</span>
              </Link>
            </li>
            <li>
              <Link to="/register" className="nav-link nav-cta" onClick={close}>
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
