import { API_BASE_URL, IS_ELECTRON } from './constants'
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

/** 把系统绝对路径转成 file:// URL（处理 Windows 反斜杠 + # 编码） */
function toFileUrl(absPath: string): string {
  return 'file:///' + absPath.replace(/\\/g, '/').replace(/#/g, '%23')
}

/** 缩略图地址：Electron 走 file://，浏览器走 HTTP。
 *  thumb_url 上的 ?t=xxx 缓存戳会自动转移到 file:// URL，保留刷新语义。 */
export function resolveThumb(item: { thumb_path?: string; thumb_url: string }): string {
  if (IS_ELECTRON && item.thumb_path) {
    const qIdx = item.thumb_url.indexOf('?')
    const query = qIdx >= 0 ? item.thumb_url.slice(qIdx) : ''
    return toFileUrl(item.thumb_path) + query
  }
  return resolveUrl(item.thumb_url)
}

/** 头像地址：Electron 走 file://，浏览器走 HTTP */
export function resolveAvatar(actor: { avatar_abs_path?: string; avatar_url: string }): string {
  if (IS_ELECTRON && actor.avatar_abs_path) {
    const qIdx = actor.avatar_url.indexOf('?')
    const query = qIdx >= 0 ? actor.avatar_url.slice(qIdx) : ''
    return toFileUrl(actor.avatar_abs_path) + query
  }
  return resolveUrl(actor.avatar_url)
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
