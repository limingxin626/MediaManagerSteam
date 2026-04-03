import { API_BASE_URL } from './constants'

export function formatDuration(ms: number | null): string {
  if (!ms) return ''
  const seconds = Math.floor(ms / 1000)
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
  return `${m}:${String(s).padStart(2, '0')}`
}

export function isVideo(mimeType: string | null): boolean {
  return mimeType?.startsWith('video/') ?? false
}

export function isImage(mimeType: string | null): boolean {
  return mimeType?.startsWith('image/') ?? false
}

/** Resolve a backend-relative URL (e.g. /data/thumbs/1.webp) to a full URL */
export function resolveUrl(path: string): string {
  return `${API_BASE_URL}${path}`
}
