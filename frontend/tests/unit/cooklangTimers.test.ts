import { describe, expect, it } from 'vitest'
import { parseTimerMentions } from '../../src/utils/cooklangTimers'

describe('parseTimerMentions', () => {
  it('parses an anonymous timer in minutes', () => {
    const [timer] = parseTimerMentions('Laisser reposer ~{10%minutes}.')
    expect(timer.name).toBe('')
    expect(timer.quantity).toBe('10')
    expect(timer.unit).toBe('minutes')
    expect(timer.totalSeconds).toBe(600)
  })

  it('parses a named timer', () => {
    const [timer] = parseTimerMentions('Laisser ~repos{1%heure} au frigo.')
    expect(timer.displayName).toBe('repos')
    expect(timer.totalSeconds).toBe(3600)
  })

  it('parses a multi-word name joined with an underscore', () => {
    const [timer] = parseTimerMentions('~temps_de_repos{30%min} avant de servir.')
    expect(timer.displayName).toBe('temps de repos')
    expect(timer.totalSeconds).toBe(1800)
  })

  it('recognizes abbreviated and English unit spellings', () => {
    const [seconds] = parseTimerMentions('~{45%s}')
    const [hours] = parseTimerMentions('~{2%hours}')
    expect(seconds.totalSeconds).toBe(45)
    expect(hours.totalSeconds).toBe(7200)
  })

  it('parses several timers in the same text', () => {
    const timers = parseTimerMentions('Cuire ~{5%minutes} à couvert puis ~{10%minutes} à découvert.')
    expect(timers.map((t) => t.totalSeconds)).toEqual([300, 600])
  })

  it('returns null totalSeconds for an unrecognized unit', () => {
    const [timer] = parseTimerMentions('~{10%pouces}')
    expect(timer.totalSeconds).toBeNull()
  })

  it('returns null totalSeconds when the quantity is missing', () => {
    const [timer] = parseTimerMentions('~{%minutes}')
    expect(timer.totalSeconds).toBeNull()
  })

  it('returns no timers when there is no "~"', () => {
    expect(parseTimerMentions('Faire cuire 10 minutes.')).toEqual([])
  })

  it('exposes start/end offsets covering the full timer including {meta}', () => {
    const text = 'Laisser ~repos{10%minutes} au frigo.'
    const [timer] = parseTimerMentions(text)
    expect(text.slice(timer.start, timer.end)).toBe('~repos{10%minutes}')
  })
})
