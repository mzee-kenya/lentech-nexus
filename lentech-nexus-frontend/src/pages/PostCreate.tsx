import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import Layout from '../components/Layout'
import { posts as postsApi } from '../api/services'
import { getErrorMessage } from '../api/client'
import './detail.css'
import './social.css'

/**
 * Compose a new post. Text, an image and a short video can be combined; at
 * least one of them is required (mirrors the backend rule).
 */
function PostCreate() {
  const navigate = useNavigate()
  const [body, setBody] = useState('')
  const [image, setImage] = useState<File | null>(null)
  const [video, setVideo] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!body.trim() && !image && !video) {
      setError('Add some text, an image or a video.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const data = await postsApi.create({ body: body.trim(), image, video })
      navigate(`/feed/${data.id}`)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <section className="detail-section">
        <div className="detail-card">
          <h1>Share a post</h1>
          {error && <p className="error-text">{error}</p>}
          <form className="form-grid" onSubmit={handleSubmit}>
            <label>
              What&apos;s on your mind?
              <textarea
                rows={4}
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder="Share an update…"
              />
            </label>

            <label>
              Image <span className="file-hint">(JPEG, PNG, WEBP or GIF)</span>
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setImage(e.target.files?.[0] ?? null)}
              />
            </label>
            {image && (
              <img
                className="post-create-preview"
                src={URL.createObjectURL(image)}
                alt="Selected image preview"
              />
            )}

            <label>
              Short video <span className="file-hint">(MP4, WEBM, OGG or MOV)</span>
              <input
                type="file"
                accept="video/*"
                onChange={(e) => setVideo(e.target.files?.[0] ?? null)}
              />
            </label>
            {video && (
              <video className="post-create-preview" src={URL.createObjectURL(video)} controls />
            )}

            <div className="form-actions">
              <button className="button-primary" type="submit" disabled={loading}>
                {loading ? 'Posting…' : 'Post'}
              </button>
              <Link to="/feed" className="button-ghost">Cancel</Link>
            </div>
          </form>
        </div>
      </section>
    </Layout>
  )
}

export default PostCreate
