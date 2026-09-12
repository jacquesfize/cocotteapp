import { describe, expect, it } from 'vitest'
import { formatDuration } from '../../src/utils/format'

describe('formatDuration', () => {
  it('returns 0 min for falsy input', () => {
    expect(formatDuration(0)).toBe('0 min')
  })

  it('formats minutes under an hour', () => {
    expect(formatDuration(25)).toBe('25 min')
  })

  it('formats exact hours', () => {
    expect(formatDuration(120)).toBe('2 h')
  })

  it('formats hours and minutes', () => {
    expect(formatDuration(95)).toBe('1 h 35 min')
  })
})
