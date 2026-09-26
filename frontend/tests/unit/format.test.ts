import { describe, expect, it } from 'vitest'
import { formatDuration, formatQuantity } from '../../src/utils/format'

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

describe('formatQuantity', () => {
  it('drops useless trailing zeros', () => {
    expect(formatQuantity('200.00', 'g')).toBe('200')
    expect(formatQuantity('1.50', 'kg')).toBe('1.5')
    expect(formatQuantity('0.25', 'l')).toBe('0.25')
  })

  it('keeps at most two decimals', () => {
    expect(formatQuantity(333.3333, 'g')).toBe('333.33')
  })

  it('rounds integer-only units up', () => {
    expect(formatQuantity('2.00', 'piece')).toBe('2')
    expect(formatQuantity('1.50', 'piece')).toBe('2')
    expect(formatQuantity('0.50', 'pinch')).toBe('1')
  })

  it('returns an empty string for missing quantities', () => {
    expect(formatQuantity(null, 'g')).toBe('')
  })
})
