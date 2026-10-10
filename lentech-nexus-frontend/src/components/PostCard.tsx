import { useState } from 'react'
import { Link } from 'react-router-dom'

import { posts as postsApi } from '../api/services'
import { useAuth } from '../contexts/AuthContext'
import type { Post } from '../types/api'
import { formatDateTime, initialsFor } from '../utils/format'
import './PostCard.css'

interface PostCardProps {
  post: Post
}

/**
 * A single feed post with an inline like button.
 *
 * Like state is held locally so tapping "like" feels instant; the server
 * response is the source of truth and overwrites the optimistic values.
 */
function PostCard({ post }: PostCardProps) {
  const { user } = useAuth()
  const [likeCount, setLikeCount] = useState(post.like_count)
  const [hasLiked, setHasLiked] = useState(post.viewer_has_liked)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const toggleLike = async () => {
    if (!user || busy) return
    setBusy(true)
    setError(null)
    try {
      const state = hasLiked
        ? await postsApi.unlike(post.id)
        : await postsApi.like(post.id)
      setLikeCount(state.like_count)
      setHasLiked(state.viewer_has_liked)
    } catch {
      setError('Could not update like.')
    } finally {
      setBusy(false)
    }
  }

  return (
    <article className="post-card">
      <header className="post-head">
        {post.author_avatar ? (
          <img className="post-avatar" src={post.author_avatar} alt="" />
        ) : (
          <span className="post-avatar post-avatar-fallback">
            {initialsFor(post.author_display_name || post.author_username)}
          </span>
        )}
        <div className="post-meta">
          <strong>{post.author_display_name || post.author_username}</strong>
          <small>
            @{post.author_username} · {formatDateTime(post.created_at)}
          </small>
        </div>
      </header>

      {post.body && <p className="post-body">{post.body}</p>}

      {post.image_url && (
        <img className="post-media" src={post.image_url} alt="Post attachment" />
      )}
      {post.video_url && (
        <video className="post-media" src={post.video_url} controls preload="metadata" />
      )}

      <footer className="post-actions">
        <button
          type="button"
          className={`post-like ${hasLiked ? 'liked' : ''}`}
          onClick={toggleLike}
          disabled={!user || busy}
          aria-pressed={hasLiked}
          title={user ? 'Like this post' : 'Log in to like'}
        >
          <span aria-hidden="true">{hasLiked ? '♥' : '♡'}</span> {likeCount}
        </button>
        <Link to={`/feed/${post.id}`} className="post-comment-link">
          <span aria-hidden="true">💬</span> {post.comment_count}
        </Link>
      </footer>

      {error && <p className="error-text">{error}</p>}
    </article>
  )
}

export default PostCard
