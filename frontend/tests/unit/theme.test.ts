import { beforeEach, describe, expect, it } from 'vitest'
import {
  accentColor,
  DEFAULT_ACCENT,
  readableTextOn,
  resetAccentColor,
  setAccentColor,
  setThemeMode,
  themeMode,
  toggleThemeMode,
} from '../../src/utils/theme'

describe('theme', () => {
  beforeEach(() => {
    localStorage.clear()
    resetAccentColor()
    setThemeMode('light')
  })

  it('toggles data-theme and persists the mode', () => {
    toggleThemeMode()
    expect(themeMode.value).toBe('dark')
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(localStorage.getItem('theme-mode')).toBe('dark')
  })

  it('applies and persists a valid accent, ignores invalid ones', () => {
    setAccentColor('#2F80ED')
    expect(accentColor.value).toBe('#2f80ed')
    expect(document.documentElement.style.getPropertyValue('--color-primary')).toBe('#2f80ed')
    setAccentColor('red')
    expect(accentColor.value).toBe('#2f80ed')
    resetAccentColor()
    expect(accentColor.value).toBe(DEFAULT_ACCENT)
    expect(localStorage.getItem('theme-accent')).toBeNull()
  })

  it('picks a readable text color', () => {
    expect(readableTextOn('#ffffff')).toBe('#241f1d')
    expect(readableTextOn('#000000')).toBe('#ffffff')
  })
})
