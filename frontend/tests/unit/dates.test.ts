import { describe, expect, it } from 'vitest'
import { addDays, startOfWeek, toISODate } from '../../src/utils/dates'

describe('startOfWeek', () => {
  it('returns the same Monday when given a Monday', () => {
    const monday = new Date(2026, 0, 5) // 5 janvier 2026 est un lundi
    expect(toISODate(startOfWeek(monday))).toBe('2026-01-05')
  })

  it('rolls back to Monday when given a Wednesday', () => {
    const wednesday = new Date(2026, 0, 7)
    expect(toISODate(startOfWeek(wednesday))).toBe('2026-01-05')
  })

  it('rolls back to Monday when given a Sunday', () => {
    const sunday = new Date(2026, 0, 11)
    expect(toISODate(startOfWeek(sunday))).toBe('2026-01-05')
  })
})

describe('addDays', () => {
  it('adds days without mutating the input', () => {
    const start = new Date(2026, 0, 5)
    const result = addDays(start, 6)
    expect(toISODate(result)).toBe('2026-01-11')
    expect(toISODate(start)).toBe('2026-01-05')
  })
})

describe('toISODate', () => {
  it('pads single-digit months and days', () => {
    expect(toISODate(new Date(2026, 0, 5))).toBe('2026-01-05')
  })
})
