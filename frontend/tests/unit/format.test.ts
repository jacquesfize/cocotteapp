import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { i18n } from '../../src/i18n'
import { formatDuration, formatNumber, formatQuantity } from '../../src/utils/format'

describe('formatDuration', () => {
  it('returns a dash for missing (null/0) durations instead of "0 min"', () => {
    expect(formatDuration(0)).toBe('—')
    expect(formatDuration(null)).toBe('—')
    expect(formatDuration(undefined)).toBe('—')
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

  it('keeps decimals for piece (now allowed) but rounds pinch up', () => {
    expect(formatQuantity('2.00', 'piece')).toBe('2')
    expect(formatQuantity('1.50', 'piece')).toBe('1.5')
    expect(formatQuantity('0.50', 'pinch')).toBe('1')
  })

  it('returns an empty string for missing quantities', () => {
    expect(formatQuantity(null, 'g')).toBe('')
  })
})

describe('formatNumber', () => {
  let previous: string

  beforeEach(() => {
    previous = i18n.global.locale.value
  })

  afterEach(() => {
    i18n.global.locale.value = previous as typeof i18n.global.locale.value
  })

  it('uses a decimal comma in French', () => {
    i18n.global.locale.value = 'fr'
    expect(formatNumber(1.25, 1)).toBe('1,3')
    expect(formatNumber(9.2, 1, { fixed: true })).toBe('9,2')
    expect(formatNumber(65, 1, { fixed: true })).toBe('65,0')
  })

  it('uses a decimal point in English', () => {
    i18n.global.locale.value = 'en'
    expect(formatNumber(1.25, 2)).toBe('1.25')
    expect(formatNumber(2, 1)).toBe('2')
  })

  it('returns a dash for missing values', () => {
    expect(formatNumber(null)).toBe('—')
    expect(formatNumber(undefined)).toBe('—')
  })
})
