import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import DeveloperCard from './DeveloperCard'

describe('DeveloperCard', () => {
  const baseProps = {
    id: 3,
    name: 'Ada Lovelace',
    role: 'Backend Engineer',
    initials: 'AL',
    skills: ['Python', 'Django'],
  }

  it('renders the developer details and skills', () => {
    render(
      <MemoryRouter>
        <DeveloperCard {...baseProps} />
      </MemoryRouter>,
    )

    expect(screen.getByText('Ada Lovelace')).toBeInTheDocument()
    expect(screen.getByText('Backend Engineer')).toBeInTheDocument()
    expect(screen.getByText('Python')).toBeInTheDocument()
    expect(screen.getByText('Django')).toBeInTheDocument()
  })

  it('shows initials when no avatar is available', () => {
    render(
      <MemoryRouter>
        <DeveloperCard {...baseProps} />
      </MemoryRouter>,
    )

    expect(screen.getByText('AL')).toBeInTheDocument()
  })

  it('renders an avatar image when provided', () => {
    render(
      <MemoryRouter>
        <DeveloperCard {...baseProps} avatarUrl="https://example.com/avatar.png" />
      </MemoryRouter>,
    )

    expect(screen.getByRole('img', { name: 'Ada Lovelace' })).toHaveAttribute(
      'src',
      'https://example.com/avatar.png',
    )
  })

  it('links to the developer profile', () => {
    render(
      <MemoryRouter>
        <DeveloperCard {...baseProps} />
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: /view profile/i })).toHaveAttribute(
      'href',
      '/developers/3',
    )
  })
})
