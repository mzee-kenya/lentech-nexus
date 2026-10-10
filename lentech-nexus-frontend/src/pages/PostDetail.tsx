import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import Layout from '../components/Layout'
import PostCard from '../components/PostCard'
import { posts as postsApi } from '../api/services'
import { ApiError, getErrorMessage } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import type { Post, PostComment } from '../types/api'
import { formatDateTime } from '../utils/format'
import './detail.css'
import './social.css'

/**
 * A single post with its full comment thread.
 *
 * The post and its comments are fetched together so the view renders in one
 * pass; adding or deleting a comment simply re-runs the same loader.
 */
function PostDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  const postId = Number(id)

  const [post, setPost] = useState<Post | null>(null)
  const [comments, setComments] = useState<PostComment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [commentBody, setCommentBody] = useState('')
  const [sending, setSending] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  const load = useCallback(() => {
    return Promise.all([
      postsApi.get(postId),
      postsApi.comments(postId, { page_size: '50' }),
    ])
      .then(([postData, commentData]) => {
        setPost(postData)
        setComments(commentData.results)
      })
      .catch((err) =>
        setError(
          err instanceof ApiError && err.status === 404
            ? 'Post not found'
            : 'Failed to load post',
        ),
      )
      .finally(() => setLoading(false))
  }, [postId])

  useEffect(() => {
    void load()
  }, [load])

  const submitComment = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!commentBody.trim()) return
    setSending(true)
    setActionError(null)
    try {
      await postsApi.addComment(postId, commentBody.trim())
      setCommentBody('')
      await load()
    } catch (err) {
      setActionError(getErrorMessage(err))
    } finally {
      setSending(false)
    }
  }

  const deleteComment = async (commentId: number) => {
    setActionError(null)
    try {
      await postsApi.removeComment(commentId)
      await load()
    } catch (err) {
      setActionError(getErrorMessage(err))
    }
  }

  const deletePost = async () => {
    setActionError(null)
    try {
      await postsApi.remove(postId)
      navigate('/feed')
    } catch (err) {
      setActionError(getErrorMessage(err))
    }
  }

  if (loading) return <Layout><p style={{ padding: '40px' }}>Loading…</p></Layout>
  if (error) return <Layout><p style={{ padding: '40px' }}>{error}</p></Layout>
  if (!post) return <Layout><p style={{ padding: '40px' }}>Post not found</p></Layout>

  return (
    <Layout>
      <section className="feed-section">
        <div className="feed-list">
          <PostCard post={post} />

          {post.viewer_is_author && (
            <div className="form-actions">
              <button
                type="button"
                className="button-ghost"
                onClick={() => void navigate('/feed')}
              >
                Back to feed
              </button>
              <button
                type="button"
                className="comment-delete"
                onClick={() => void deletePost()}
              >
                Delete post
              </button>
            </div>
          )}
        </div>

        <div className="comments">
          <h2>Comments ({comments.length})</h2>

          {comments.length === 0 && (
            <p className="comments-empty">No comments yet.</p>
          )}

          {comments.map((comment) => (
            <div className="comment" key={comment.id}>
              <div className="comment-head">
                <span className="comment-author">
                  {comment.author_display_name || comment.author_username}
                </span>
                <span className="comment-time">{formatDateTime(comment.created_at)}</span>
              </div>
              <p className="comment-body">{comment.body}</p>
              {user && user.id === comment.author_id && (
                <button
                  type="button"
                  className="comment-delete"
                  onClick={() => void deleteComment(comment.id)}
                >
                  Delete
                </button>
              )}
            </div>
          ))}

          {user ? (
            <form className="comment-form" onSubmit={submitComment}>
              <textarea
                rows={3}
                value={commentBody}
                onChange={(e) => setCommentBody(e.target.value)}
                placeholder="Write a comment…"
              />
              <div className="form-actions">
                <button className="button-primary" type="submit" disabled={sending}>
                  {sending ? 'Sending…' : 'Comment'}
                </button>
              </div>
            </form>
          ) : (
            <p className="comments-empty">
              <Link to="/login" className="link-muted">Log in</Link> to join the conversation.
            </p>
          )}

          {actionError && <p className="error-text">{actionError}</p>}
        </div>
      </section>
    </Layout>
  )
}

export default PostDetail
