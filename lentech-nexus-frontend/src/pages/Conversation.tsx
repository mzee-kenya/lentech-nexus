import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import Layout from '../components/Layout'
import ChatSidebar from '../components/ChatSidebar'
import UserPicker from '../components/UserPicker'
import { chat as chatApi } from '../api/services'
import { ApiError, getErrorMessage } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import type { ChatMessage, Conversation as ConversationType, PublicUser } from '../types/api'
import { conversationPeer } from '../utils/chat'
import { formatDateTime, initialsFor } from '../utils/format'
import './detail.css'
import './chat.css'

/**
 * An open conversation.
 *
 * Layout mirrors Facebook Messenger (list + thread); group chats borrow the
 * WhatsApp convention of showing the sender's name above incoming bubbles and
 * a members panel.
 */
function Conversation() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const conversationId = Number(id)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const [conversation, setConversation] = useState<ConversationType | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const [body, setBody] = useState('')
  const [sending, setSending] = useState(false)
  const [showAddMember, setShowAddMember] = useState(false)

  const load = useCallback(() => {
    return Promise.all([
      chatApi.get(conversationId),
      chatApi.messages(conversationId, { page_size: '100' }),
    ])
      .then(([conversationData, messageData]) => {
        setConversation(conversationData)
        setMessages(messageData.results)
      })
      .catch((err) =>
        setError(
          err instanceof ApiError && err.status === 404
            ? 'Conversation not found'
            : 'Failed to load conversation',
        ),
      )
      .finally(() => setLoading(false))
  }, [conversationId])

  useEffect(() => {
    void load()
  }, [load])

  // Keep the newest message in view after sending or loading.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ block: 'end' })
  }, [messages])

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!body.trim()) return
    setSending(true)
    setActionError(null)
    try {
      const created = await chatApi.sendMessage(conversationId, body.trim())
      setMessages((prev) => [...prev, created])
      setBody('')
    } catch (err) {
      setActionError(getErrorMessage(err))
    } finally {
      setSending(false)
    }
  }

  const addMember = async (person: PublicUser) => {
    setActionError(null)
    try {
      await chatApi.addMember(conversationId, person.id)
      setShowAddMember(false)
      await load()
    } catch (err) {
      setActionError(getErrorMessage(err))
    }
  }

  const removeMember = async (userId: number) => {
    setActionError(null)
    try {
      await chatApi.removeMember(conversationId, userId)
      await load()
    } catch (err) {
      setActionError(getErrorMessage(err))
    }
  }

  const leave = async () => {
    setActionError(null)
    try {
      await chatApi.leave(conversationId)
      navigate('/chat')
    } catch (err) {
      setActionError(getErrorMessage(err))
    }
  }

  if (loading) return <Layout><p style={{ padding: '40px' }}>Loading…</p></Layout>
  if (error) return <Layout><p style={{ padding: '40px' }}>{error}</p></Layout>
  if (!conversation) return <Layout><p style={{ padding: '40px' }}>Conversation not found</p></Layout>

  const isGroup = conversation.kind === 'group'
  const isOwner = conversation.viewer_role === 'owner'
  const peer = conversationPeer(conversation, user?.id)
  const memberIds = conversation.members.map((member) => member.user_id)

  return (
    <Layout>
      <section className="chat-shell">
        <div className="chat-layout">
          <ChatSidebar activeId={conversationId} />

          <div className="chat-main thread">
            <header className="thread-head">
              {peer.avatar ? (
                <img className="avatar" src={peer.avatar} alt="" />
              ) : (
                <span className={`avatar ${isGroup ? 'avatar-group' : 'avatar-fallback'}`}>
                  {initialsFor(peer.name)}
                </span>
              )}
              <div className="thread-title">
                <strong>{conversation.display_title}</strong>
                <small>
                  {isGroup
                    ? `${conversation.member_count} members`
                    : `@${conversation.members.find((m) => m.user_id !== user?.id)?.username ?? ''}`}
                </small>
              </div>
              <button
                type="button"
                className="thread-leave"
                onClick={() => void navigate('/chat')}
                title="Back to conversations"
              >
                ✕
              </button>
            </header>

            <div className="messages">
              {messages.length === 0 && (
                <p className="chat-status">No messages yet. Say hello!</p>
              )}
              {messages.map((message) => {
                const own = user?.id === message.sender_id
                return (
                  <div className={`message ${own ? 'own' : ''}`} key={message.id}>
                    {message.sender_avatar ? (
                      <img
                        className="avatar avatar-sm message-avatar"
                        src={message.sender_avatar}
                        alt=""
                      />
                    ) : (
                      <span className="avatar avatar-sm avatar-fallback message-avatar">
                        {initialsFor(message.sender_display_name || message.sender_username)}
                      </span>
                    )}
                    <div className="message-content">
                      {isGroup && !own && (
                        <span className="message-sender">
                          {message.sender_display_name || message.sender_username}
                        </span>
                      )}
                      <div className="message-bubble">{message.body}</div>
                      <span className="message-time">{formatDateTime(message.created_at)}</span>
                    </div>
                  </div>
                )
              })}
              <div ref={messagesEndRef} />
            </div>

            <form className="chat-composer" onSubmit={sendMessage}>
              <input
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Type a message…"
                aria-label="Message"
              />
              <button className="chat-send" type="submit" disabled={sending}>
                {sending ? '…' : 'Send'}
              </button>
            </form>

            {actionError && <p className="error-text chat-inline-error">{actionError}</p>}
          </div>

          <aside className="chat-info">
            <h2>{isGroup ? 'Group info' : 'Details'}</h2>

            <div className="chat-info-members">
              {conversation.members.map((member) => (
                <div className="member-row" key={member.user_id}>
                  <span className="member-name">
                    {member.avatar ? (
                      <img className="avatar avatar-sm" src={member.avatar} alt="" />
                    ) : (
                      <span className="avatar avatar-sm avatar-fallback">
                        {initialsFor(member.display_name || member.username)}
                      </span>
                    )}
                    {member.display_name || member.username}
                    {member.role === 'owner' && <span className="badge">owner</span>}
                  </span>
                  {isGroup && isOwner && member.user_id !== user?.id && (
                    <button
                      type="button"
                      className="member-remove"
                      onClick={() => void removeMember(member.user_id)}
                    >
                      Remove
                    </button>
                  )}
                </div>
              ))}
            </div>

            {isGroup && (
              <div className="chat-info-actions">
                {showAddMember ? (
                  <UserPicker
                    excludeIds={memberIds}
                    onPick={async (person) => {
                      await addMember(person)
                    }}
                    placeholder="Add people…"
                  />
                ) : (
                  <button
                    type="button"
                    className="button-ghost"
                    onClick={() => setShowAddMember(true)}
                  >
                    Add members
                  </button>
                )}
              </div>
            )}

            <div className="chat-info-actions">
              <button type="button" className="chat-leave" onClick={() => void leave()}>
                Leave conversation
              </button>
            </div>

            <Link to="/chat" className="link-muted">← All conversations</Link>
          </aside>
        </div>
      </section>
    </Layout>
  )
}

export default Conversation
