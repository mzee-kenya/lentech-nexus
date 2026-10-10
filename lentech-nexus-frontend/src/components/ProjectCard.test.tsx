import { describe, expect, it } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import ProjectCard from './ProjectCard'

describe('ProjectCard', () => {
  it('renders the project name and description', () => {
    render(
      <MemoryRouter>
        <ProjectCard id={7} name="Nexus" description="A collaboration platform" />
      </MemoryRouter>,
    )

    expect(screen.getByText('Nexus')).toBeInTheDocument()
    expect(screen.getByText('A collaboration platform')).toBeInTheDocument()
  })

  it('links to the project detail page when no external link is given', () => {
    render(
      <MemoryRouter>
        <ProjectCard id={7} name="Nexus" description="A collaboration platform" />
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: /view project/i })).toHaveAttribute('href', '/projects/7')
  })

  it('uses an external link when provided', () => {
    render(
      <MemoryRouter>
        <ProjectCard
          id={7}
          name="Nexus"
          description="A collaboration platform"
          link="https://example.com"
        />
      </MemoryRouter>,
    )

    expect(screen.getByRole('link', { name: /view project/i })).toHaveAttribute(
      'href',
      'https://example.com',
    )
  })
})
