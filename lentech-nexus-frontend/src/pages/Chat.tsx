import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import Layout from '../components/Layout'
import ChatSidebar from '../components/ChatSidebar'
import UserPicker from '../components/UserPicker'
import { chat as chatApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import type { PublicUser } from '../types/api'
import './detail.css'
import './chat.css'

/**
 * Chat home: the conversation list on the left and a "new conversation" panel
 * on the right.
 *
 * * Direct mode — picking a person immediately opens (or reuses) a 1:1 chat.
 * * Group mode — pick several people, name the group, then create it.
 */
function Chat() {
  const navigate = useNavigate()
  const [mode, setMode] = useState<'direct' | 'group'>('direct')
  const [selected, setSelected] = useState<PublicUser[]>([])
  const [title, setTitle] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  const startDirect = async (person: PublicUser) => {
    setBusy(true)
    setError(null)
    try {
      const conversation = await chatApi.create({ kind: 'direct', member_ids: [person.id] })
      navigate(`/chat/${conversation.id}`)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  const toggleMember = (person: PublicUser) => {
    setSelected((prev) =>
      prev.some((u) => u.id === person.id)
        ? prev.filter((u) => u.id !== person.id)
        : [...prev, person],
    )
  }

  const createGroup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || selected.length === 0) {
      setError('Add a group name and at least one member.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const conversation = await chatApi.create({
        kind: 'group',
        title: title.trim(),
        member_ids: selected.map((u) => u.id),
      })
      navigate(`/chat/${conversation.id}`)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Layout>
      <section className="chat-shell">
        <div className="chat-layout">
          <ChatSidebar />

          <div className="chat-main">
            <div className="chat-main-head">
              <h1>New conversation</h1>
            </div>

            <div className="chat-tabs">
              <button
                type="button"
                className={mode === 'direct' ? 'active' : ''}
                onClick={() => {
                  setMode('direct')
                  setError(null)
                }}
              >
                Direct message
              </button>
              <button
                type="button"
                className={mode === 'group' ? 'active' : ''}
                onClick={() => {
                  setMode('group')
                  setError(null)
                }}
              >
                New group
              </button>
            </div>

            {error && <p className="error-text chat-inline-error">{error}</p>}

            {mode === 'group' && (
              <form className="group-compose" onSubmit={createGroup}>
                <div className="selected-chips">
                  {selected.map((person) => (
                    <button
                      type="button"
                      key={person.id}
                      className="selected-chip"
                      onClick={() => toggleMember(person)}
                      title="Remove"
                    >
                      {person.display_name || person.username}
                      <span aria-hidden="true">×</span>
                    </button>
                  ))}
                </div>
                <div className="group-compose-row">
                  <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Group name"
                    aria-label="Group name"
                  />
                  <button className="button-primary" type="submit" disabled={busy}>
                    {busy ? 'Creating…' : 'Create group'}
                  </button>
                </div>
              </form>
            )}

            <p className="chat-hint">
              {mode === 'direct'
                ? 'Choose someone to start chatting.'
                : 'Tap people to add them to the group.'}
            </p>

            <UserPicker
              selectedIds={mode === 'group' ? selected.map((u) => u.id) : []}
              onPick={mode === 'direct' ? startDirect : toggleMember}
            />
          </div>
        </div>
      </section>
    </Layout>
  )
}

export default Chat
