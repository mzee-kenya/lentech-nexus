import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { chat as chatApi } from '../api/services'
import { useAuth } from '../contexts/AuthContext'
import type { Conversation } from '../types/api'
import { conversationPeer } from '../utils/chat'
import { initialsFor } from '../utils/format'

interface ChatSidebarProps {
  /** Conversation currently open, highlighted in the list. */
  activeId?: number
}

/**
 * Facebook-Messenger-style conversation list.
 *
 * Kept as its own component so both the "new chat" screen and an open thread
 * can render the same sidebar.
 */
function ChatSidebar({ activeId }: ChatSidebarProps) {
  const navigate = useNavigate()
  const { user } = useAuth()
  const [items, setItems] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  useEffect(() => {
    let active = true
    chatApi
      .list()
      .then((data) => {
        if (active) setItems(data.results)
      })
      .catch(() => {
        if (active) setError('Could not load conversations.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [activeId])

  const filtered = items.filter((conversation) =>
    conversation.display_title.toLowerCase().includes(query.trim().toLowerCase()),
  )

  return (
    <aside className="chat-sidebar">
      <div className="chat-sidebar-head">
        <h2>Chats</h2>
        <button
          type="button"
          className="chat-new-btn"
          onClick={() => navigate('/chat')}
          title="Start a new conversation"
        >
          +
        </button>
      </div>

      <input
        className="chat-sidebar-search"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search conversations"
        aria-label="Search conversations"
      />

      {loading && <p className="chat-status">Loading…</p>}
      {error && <p className="chat-status">{error}</p>}
      {!loading && !error && filtered.length === 0 && (
        <p className="chat-status">No conversations yet.</p>
      )}

      <ul className="chat-list">
        {filtered.map((conversation) => {
          const peer = conversationPeer(conversation, user?.id)
          const isActive = conversation.id === activeId
          return (
            <li key={conversation.id}>
              <Link
                to={`/chat/${conversation.id}`}
                className={isActive ? 'active' : undefined}
                aria-current={isActive ? 'page' : undefined}
              >
                {conversation.kind === 'group' ? (
                  <span className="avatar avatar-group">
                    {initialsFor(conversation.display_title)}
                  </span>
                ) : conversationPeer(conversation, user?.id).avatar ? (
                  <img className="avatar" src={conversationPeer(conversation, user?.id).avatar} alt="" />
                ) : (
                  <span className="avatar avatar-fallback">{initialsFor(peer.name)}</span>
                )}

                <span className="chat-sidebar-text">
                  <span className="chat-sidebar-title">{conversation.display_title}</span>
                  <span className="chat-sidebar-preview">
                    {conversation.last_message?.body ||
                      `${conversation.member_count} members`}
                  </span>
                </span>

                {conversation.unread_count > 0 && (
                  <span className="chat-unread-badge" aria-label="unread messages">
                    {conversation.unread_count > 99 ? '99+' : conversation.unread_count}
                  </span>
                )}
              </Link>
            </li>
          )
        })}
      </ul>
    </aside>
  )
}

export default ChatSidebar
