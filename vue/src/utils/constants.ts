// API configuration
const currentHostApiUrl = typeof window !== 'undefined' && window.location.protocol !== 'file:'
  ? `${window.location.protocol}//${window.location.hostname}:8002`
  : 'http://127.0.0.1:8002'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || currentHostApiUrl

export const IS_ELECTRON =
  typeof navigator !== 'undefined' && navigator.userAgent.includes('Electron')
