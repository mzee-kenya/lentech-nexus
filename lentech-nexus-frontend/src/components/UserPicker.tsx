import { useEffect, useState } from 'react'

import { users as usersApi } from '../api/services'
import type { PublicUser } from '../types/api'
import { initialsFor } from '../utils/format'

interface UserPickerProps {
  /** Ids shown with a checkmark (e.g. members already chosen). */
  selectedIds?: number[]
  /** Ids hidden from the list (e.g. people already in the group). */
  excludeIds?: number[]
  onPick: (user: PublicUser) => void
  placeholder?: string
}

/**
 * Searchable directory of other members.
 *
 * The parent decides what a pick means: start a direct chat, or toggle a member
 * on/off while composing a group. Re-fetches as the search box changes.
 */
function UserPicker({
  selectedIds = [],
  excludeIds = [],
  onPick,
  placeholder,
}: UserPickerProps) {
  const [query, setQuery] = useState('')
  const [items, setItems] = useState<PublicUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    usersApi
      .list({ search: query, page_size: '30' })
      .then((data) => {
        if (active) {
          setItems(data.results)
          setError(null)
        }
      })
      .catch(() => {
        if (active) setError('Could not load people right now.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [query])

  const visible = items.filter((user) => !excludeIds.includes(user.id))

  return (
    <div className="user-picker">
      <input
        className="user-picker-search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder={placeholder ?? 'Search people…'}
        aria-label="Search people"
      />

      {loading && <p className="user-picker-status">Loading…</p>}
      {error && <p className="user-picker-status">{error}</p>}
      {!loading && !error && visible.length === 0 && (
        <p className="user-picker-status">No people found.</p>
      )}

      <ul className="user-picker-list">
        {visible.map((user) => {
          const selected = selectedIds.includes(user.id)
          return (
            <li key={user.id}>
              <button
                type="button"
                className={`user-row ${selected ? 'selected' : ''}`}
                onClick={() => onPick(user)}
              >
                {user.avatar ? (
                  <img className="avatar" src={user.avatar} alt="" />
                ) : (
                  <span className="avatar avatar-fallback">
                    {initialsFor(user.display_name || user.username)}
                  </span>
                )}
                <span className="user-row-text">
                  <strong>{user.display_name || user.username}</strong>
                  <small>@{user.username}</small>
                </span>
                {selected && <span className="user-row-check" aria-hidden="true">✓</span>}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

export default UserPicker
