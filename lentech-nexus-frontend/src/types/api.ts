export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface User {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  display_name: string
  role: string
  is_staff: boolean
  date_joined: string
}

export interface Developer {
  id: number
  user_id: number | null
  username: string | null
  name: string
  role: string
  bio: string
  profile_image: string
  skills: string[]
  github_url: string
  linkedin_url: string
  website_url: string
  created_at: string
  updated_at: string
}

export interface Project {
  id: number
  title: string
  summary: string
  status: string
  technologies: string[]
  owner_username: string
  owner_display_name: string
  member_count: number
  created_at: string
  viewer_is_member?: boolean
  viewer_is_owner?: boolean
  viewer_request_status?: string | null
  description?: string
  repo_url?: string
  live_url?: string
  owner_id?: number
  members?: Array<{
    id: number
    user: number
    username: string
    display_name: string
    role: string
    created_at: string
  }>
}

export interface Idea {
  id: number
  title: string
  summary: string
  status: string
  tags: string[]
  author_username: string
  author_display_name: string
  interest_count: number
  created_at: string
  description?: string
  author_id?: number
  viewer_is_author?: boolean
  viewer_interest_status?: string | null
}

export interface JoinRequest {
  id: number
  project: number
  project_title: string
  requester: number
  requester_username: string
  requester_display_name: string
  message: string
  status: string
  reviewed_at: string | null
  created_at: string
}
