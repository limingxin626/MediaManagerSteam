import { API_BASE_URL } from './constants'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'

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
  // 对 URL 进行编码处理，特别是对 # 字符进行编码
  return `${API_BASE_URL}${path.replace(/#/g, '%23')}`
}

/** Toggle media starred state via API, updates item.starred in-place */
export async function toggleMediaStar(item: { id: number; starred: boolean }): Promise<void> {
  const toast = useToast()
  try {
    await api.put(`/media/${item.id}/starred`, undefined, { starred: !item.starred })
    item.starred = !item.starred
  } catch {
    toast.error('操作失败')
  }
}
