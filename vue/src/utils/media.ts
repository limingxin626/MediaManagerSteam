import { IS_ELECTRON } from './constants'
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

/** Resolve a backend-relative path to a full absolute path */
export function resolveUrl(path: string): string {
  if (IS_ELECTRON) {
    return `file://${path.replace(/#/g, '%23')}`
  }
  return `${path.replace(/#/g, '%23')}`
}

/** Resolve media thumb_url to absolute path */
export function resolveThumb(item: { thumb_url: string | null; thumb_path?: string | null } | null): string {
  if (!item) return ''
  if (item.thumb_path) return resolveUrl(item.thumb_path)
  if (item.thumb_url) return resolveUrl(item.thumb_url)
  return ''
}

/** Resolve media file_url to absolute path, preferring file_path if available */
export function resolveMediaUrl(item: { file_url: string | null; file_path?: string | null } | null): string {
  if (!item) return ''
  if (item.file_path) return resolveUrl(item.file_path)
  if (item.file_url) return resolveUrl(item.file_url)
  return ''
}

/** Resolve actor avatar to absolute path */
export function resolveAvatar(actor: { avatar_url?: string | null; avatar_abs_path?: string | null } | null): string {
  if (!actor) return ''
  if (actor.avatar_abs_path) return resolveUrl(actor.avatar_abs_path)
  if (actor.avatar_url) return resolveUrl(actor.avatar_url)
  return ''
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

/** Rotate media file on server, returns updated media data */
export async function rotateMedia(mediaId: number, degrees: number): Promise<any> {
  return api.post(`/media/${mediaId}/rotate`, { degrees })
}
