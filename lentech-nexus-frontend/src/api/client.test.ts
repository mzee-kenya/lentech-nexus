import { describe, expect, it } from 'vitest'
import { ApiError, getErrorMessage } from './client'

describe('ApiError', () => {
  it('captures status and data', () => {
    const err = new ApiError(400, { detail: 'Bad request' })
    expect(err.status).toBe(400)
    expect(err.data).toEqual({ detail: 'Bad request' })
    expect(err.name).toBe('ApiError')
  })
})

describe('getErrorMessage', () => {
  it('returns the detail field when present', () => {
    expect(getErrorMessage(new ApiError(403, { detail: 'Not allowed' }))).toBe('Not allowed')
  })

  it('returns the first validation error from field errors', () => {
    const err = new ApiError(400, { username: ['This field is required.'], email: [] })
    expect(getErrorMessage(err)).toBe('This field is required.')
  })

  it('returns a plain string payload', () => {
    expect(getErrorMessage(new ApiError(500, 'Server exploded'))).toBe('Server exploded')
  })

  it('falls back to the status for unknown object payloads', () => {
    expect(getErrorMessage(new ApiError(418, { weird: { nested: true } }))).toBe('Request failed (418)')
  })

  it('handles generic errors', () => {
    expect(getErrorMessage(new Error('boom'))).toBe('boom')
  })

  it('handles unknown values', () => {
    expect(getErrorMessage(undefined)).toBe('Something went wrong')
  })
})
