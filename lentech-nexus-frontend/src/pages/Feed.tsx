import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import Layout from '../components/Layout'
import PostCard from '../components/PostCard'
import { posts as postsApi } from '../api/services'
import { useAuth } from '../contexts/AuthContext'
import type { Post } from '../types/api'
import './detail.css'
import './social.css'

/**
 * Public feed of community posts, newest first, with simple pagination.
 *
 * ``page`` drives the fetch: changing it re-runs the effect and either replaces
 * the list (page 1) or appends the next page.
 */
function Feed() {
  const { user } = useAuth()
  const [items, setItems] = useState<Post[]>([])
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    postsApi
      .list({ page: String(page), page_size: '10' })
      .then((data) => {
        if (!active) return
        // Replace on the first page, append afterwards.
        setItems((prev) => (page === 1 ? data.results : [...prev, ...data.results]))
        setHasNext(Boolean(data.next))
      })
      .catch(() => {
        if (active) setError('We could not load the feed right now.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [page])

  const loadMore = () => {
    setLoading(true)
    setPage((p) => p + 1)
  }

  return (
    <Layout>
      <section className="feed-section">
        <div className="feed-header">
          <div>
            <h1>Community Feed</h1>
            <p className="feed-subtitle">
              Share pictures, short videos and updates with the community.
            </p>
          </div>
          {user ? (
            <Link to="/feed/new" className="button-primary">Share a post</Link>
          ) : (
            <Link to="/login" className="button-ghost">Log in to post</Link>
          )}
        </div>

        {loading && items.length === 0 && <p className="feed-status">Loading feed…</p>}
        {error && <p className="feed-status">{error}</p>}
        {!loading && !error && items.length === 0 && (
          <p className="feed-status">No posts yet. Be the first to share something!</p>
        )}

        <div className="feed-list">
          {items.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>

        {hasNext && (
          <div className="feed-more">
            <button type="button" className="button-ghost" onClick={loadMore} disabled={loading}>
              {loading ? 'Loading…' : 'Load more'}
            </button>
          </div>
        )}
      </section>
    </Layout>
  )
}

export default Feed
