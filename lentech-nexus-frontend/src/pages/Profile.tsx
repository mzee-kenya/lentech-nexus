import { useCallback, useEffect, useState } from 'react'
import Layout from '../components/Layout'
import { developers } from '../api/services'
import { getErrorMessage } from '../api/client'
import type { Developer } from '../types/api'
import { useAuth } from '../contexts/AuthContext'
import './profile.css'

export default function Profile() {
  const { user } = useAuth()
  const [profile, setProfile] = useState<Developer | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [imageUploading, setImageUploading] = useState(false)
  const [form, setForm] = useState({
    role: '',
    bio: '',
    skills: '',
    github_url: '',
    linkedin_url: '',
    website_url: '',
  })
  const [photoError, setPhotoError] = useState<string | null>(null)

  const load = useCallback(() => {
    return developers
      .me()
      .then((data) => {
        setProfile(data)
        setForm({
          role: data.role ?? '',
          bio: data.bio ?? '',
          skills: Array.isArray(data.skills) ? data.skills.join(', ') : '',
          github_url: data.github_url ?? '',
          linkedin_url: data.linkedin_url ?? '',
          website_url: data.website_url ?? '',
        })
      })
      .catch(() => setProfile(null))
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSaving(true)
    try {
      const payload = {
        role: form.role,
        bio: form.bio,
        skills: form.skills
          .split(',')
          .map((s) => s.trim())
          .filter(Boolean),
        github_url: form.github_url,
        linkedin_url: form.linkedin_url,
        website_url: form.website_url,
      }
      const data = await developers.update(profile?.id ?? (await developers.create({})).id, payload)
      setProfile(data)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const handlePhoto = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPhotoError(null)
    setImageUploading(true)
    try {
      const data = await developers.uploadPhoto(file)
      setProfile(data)
    } catch (err) {
      setPhotoError(getErrorMessage(err))
    } finally {
      setImageUploading(false)
    }
  }

  const handleRemovePhoto = async () => {
    setPhotoError(null)
    try {
      const data = await developers.removePhoto()
      setProfile(data)
    } catch (err) {
      setPhotoError(getErrorMessage(err))
    }
  }

  if (loading) return <Layout><p style={{padding:'40px'}}>Loading…</p></Layout>
  if (!user) return <Layout><p style={{padding:'40px'}}>Please sign in to edit your profile.</p></Layout>

  return (
    <Layout>
      <section className="profile-section">
        <div className="profile-card">
          <h1>Your profile</h1>
          {error && <p className="profile-error">{error}</p>}
          <div className="profile-header">
            <div className="avatar">
              {profile?.profile_image ? (
                <img src={profile.profile_image} alt={profile.name} />
              ) : (
                <span>{profile?.name?.[0]?.toUpperCase() ?? user.username[0].toUpperCase()}</span>
              )}
            </div>
            <div>
              <h2>{profile?.name ?? user.display_name}</h2>
              <p>{profile?.role || 'No role set'}</p>
              <div className="profile-actions">
                <label className="button-ghost">
                  {imageUploading ? 'Uploading…' : 'Upload photo'}
                  <input type="file" accept="image/*" hidden onChange={handlePhoto} />
                </label>
                {profile?.profile_image && (
                  <button type="button" className="button-ghost" onClick={handleRemovePhoto}>
                    Remove photo
                  </button>
                )}
              </div>
              {photoError && <p className="profile-error">{photoError}</p>}
            </div>
          </div>

          <form className="profile-form" onSubmit={handleSave}>
            <label>
              Role
              <input name="role" value={form.role} onChange={handleChange} placeholder="e.g. Full-stack Developer" />
            </label>
            <label>
              Bio
              <textarea name="bio" rows={4} value={form.bio} onChange={handleChange} />
            </label>
            <label>
              Skills (comma-separated)
              <input name="skills" value={form.skills} onChange={handleChange} placeholder="React, Python, Django" />
            </label>
            <label>
              GitHub URL
              <input name="github_url" value={form.github_url} onChange={handleChange} />
            </label>
            <label>
              LinkedIn URL
              <input name="linkedin_url" value={form.linkedin_url} onChange={handleChange} />
            </label>
            <label>
              Website URL
              <input name="website_url" value={form.website_url} onChange={handleChange} />
            </label>
            <button type="submit" disabled={saving}>
              {saving ? 'Saving…' : 'Save profile'}
            </button>
          </form>
        </div>
      </section>
    </Layout>
  )
}