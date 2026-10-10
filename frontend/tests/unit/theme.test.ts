import { beforeEach, describe, expect, it } from 'vitest'
import {
  accentColor,
  DEFAULT_ACCENT,
  readableTextOn,
  resetAccentColor,
  setAccentColor,
  setThemeMode,
  setThemeShape,
  themeMode,
  themeShape,
  toggleThemeMode,
} from '../../src/utils/theme'

describe('theme', () => {
  beforeEach(() => {
    localStorage.clear()
    resetAccentColor()
    setThemeMode('light')
    setThemeShape('rounded')
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

  it('toggles data-shape and only persists the flat style', () => {
    expect(document.documentElement.getAttribute('data-shape')).toBe('rounded')
    setThemeShape('flat')
    expect(themeShape.value).toBe('flat')
    expect(document.documentElement.getAttribute('data-shape')).toBe('flat')
    expect(localStorage.getItem('theme-shape')).toBe('flat')
    setThemeShape('rounded')
    expect(localStorage.getItem('theme-shape')).toBeNull()
  })

  it('picks a readable text color', () => {
    expect(readableTextOn('#ffffff')).toBe('#241f1d')
    expect(readableTextOn('#000000')).toBe('#ffffff')
  })
})
