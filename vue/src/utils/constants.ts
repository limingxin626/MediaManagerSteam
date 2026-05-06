// API configuration
export const API_BASE_URL = 'http://127.0.0.1:8002'

export const IS_ELECTRON =
  typeof navigator !== 'undefined' && navigator.userAgent.includes('Electron')
