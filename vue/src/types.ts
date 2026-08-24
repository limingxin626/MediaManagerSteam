import type { components } from './types/api.generated'

// --- 从 OpenAPI 生成的类型中派生 ---

// 消息相关
// MessageMediaItem 通过 MediaUrlMixin 获得 local_file_path / local_thumb_path,
// OpenAPI 尚未重新生成,手动扩展。
export type MessageMediaItem = components['schemas']['MessageMediaItem'] & {
  repo_id?: string
  local_file_path?: string
  local_thumb_path?: string
  source_message_id?: number | null
  // 后端 MediaResponse 带 people（媒体上标注的人物）；MessageMediaItem schema 未含，手动扩展
  people?: components['schemas']['MediaPersonItem'][]
}
type _Message = components['schemas']['MessageResponse']
type _MessageDetail = components['schemas']['MessageDetailResponse']

// 后端已新增 issue 关联字段，OpenAPI 尚未重新生成，手动扩展
export type Message = _Message & {
  issue_id?: number | null
  issue_title?: string | null
}
export type MessageDetail = _MessageDetail & {
  issue_id?: number | null
  issue_title?: string | null
  folder_count?: number
  primary_repo_id?: string | null
  primary_folder_path?: string | null
  folders?: {
    id: number
    repo_id: string
    rel_path: string
    name: string
    role: 'PRIMARY' | 'MIRROR' | string
  }[]
}

// 合集相关 —— CollectionResponse 自带 cover_abs_path（Electron file:// 用）
export type Collection = components['schemas']['CollectionResponse']

// 人物相关（类 Mac 照片「人物」，标注在 media 上，多对多）
export type Person = components['schemas']['PersonResponse']
export type MediaPersonItem = components['schemas']['MediaPersonItem']
// 媒体相关 —— 后端新增 local_file_path / local_thumb_path 两个绝对本地路径字段
// (Electron 走 file:// 直读),OpenAPI 尚未重新生成,手动扩展。
// `*_url` 字段是相对 URL,客户端拼自己的 backend baseUrl 后走 HTTP fallback。
export type Media = components['schemas']['MediaResponse'] & {
  repo_id?: string
  local_file_path?: string
  local_thumb_path?: string
  file_created_at?: string | null
  messages?: { id: number }[]
}

// 视频预览（章节）—— 后端尚未重新生成 OpenAPI 类型，先手写
export interface VideoPreviewItem {
  id: number
  repo_id?: string
  file_path: string
  local_file_path?: string
  local_thumb_path?: string
  file_url: string
  thumb_url: string
  mime_type: string | null
  frame_ms: number
  start_ms: number | null
  end_ms: number | null
}

export interface VideoPreviewCreate {
  preview_media_id: number
  frame_ms: number
  start_ms?: number | null
  end_ms?: number | null
}

export interface VideoPreviewUpdate {
  frame_ms?: number | null
  start_ms?: number | null
  end_ms?: number | null
}

// 标签相关
export type TagItem = components['schemas']['MessageTagItem']
export type TagWithCount = components['schemas']['TagResponse']

// 日历日期统计
export type MessageDateCount = components['schemas']['MessageDateCount']

// --- 游标分页（泛型，生成的类型不支持泛型，保留手写） ---
export interface CursorResponse<T> {
  items: T[]
  next_cursor: string | null
  prev_cursor?: string | null
  has_more: boolean
  has_more_before?: boolean
}

// --- Repository catalog（物理仓库目录） ---

export interface RepositoryFile {
  id: number
  repo_id: string
  folder_id: number
  rel_path: string
  name: string
  file_path: string
  file_url: string
  thumb_url: string
  local_file_path?: string
  local_thumb_path?: string
  mime_type: string | null
  media_type: 'VIDEO' | 'IMAGE'
  file_size: number | null
  mtime: number               // epoch 秒
  scanned_at: string
  media_id: number | null
  materialize_status: 'pending' | 'done' | 'failed'
  materialize_error: string | null
  width: number | null
  height: number | null
  duration_ms: number | null
  fps: number | null
  bitrate: number | null
  video_codec: string | null
  audio_codec: string | null
  has_audio: number | null
  taken_at: string | null
  gps_lat: number | null
  gps_lng: number | null
  orientation: number | null
  camera_make: string | null
  camera_model: string | null
  lens: string | null
  is_hdr: number | null
  color_transfer: string | null
}

export interface RepositoryFolder {
  id: number
  repo_id: string
  rel_path: string
  name: string
  parent_id: number | null
}

export interface RepositorySummary {
  repo_id: string
  root_path: string
  online: boolean
  folder_count: number
  file_count: number
  pending_count: number
}

export interface RepositoryBrowseResponse {
  repository: RepositorySummary
  folder: RepositoryFolder
  folders: RepositoryFolder[]
  files: RepositoryFile[]
}

// --- Folder（独立于 Message 的逻辑目录） ---

export interface FolderLocation {
  id: number
  repo_id: string
  rel_path: string
  name: string
  role: 'PRIMARY' | 'MIRROR' | string
}

export interface Folder {
  id: number
  name: string
  collection_id: number | null
  collection_name: string | null
  issue_id: number | null
  issue_title: string | null
  starred: boolean
  location_count: number
  media_count: number
  primary_repo_id: string | null
  primary_folder_path: string | null
  created_at: string
  updated_at: string
}

export interface FolderDetail extends Folder {
  locations: FolderLocation[]
  files: RepositoryFile[]
}

// --- 纯前端类型（后端无对应 schema） ---

export interface ViewMode {
  type: 'grid' | 'list'
}

export interface AdminStats {
  table_counts: Record<string, number>
  storage: {
    total_files: number
    total_size: number
  }
  db_size: number
  recent_messages: Array<{
    id: number
    text: string | null
    collection_id: number | null
    created_at: string | null
  }>
}

// ---------------------------------------------------------------------------
// Dashboard / Todo
// ---------------------------------------------------------------------------

export type TodoStatus = 'pending' | 'doing' | 'done'

export interface Todo {
  id: number
  title: string
  status: TodoStatus
  position: number
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface TodoBoard {
  pending: Todo[]
  doing: Todo[]
  done: Todo[]
}

// ---------------------------------------------------------------------------
// Issue (取代 Todo 看板)
// ---------------------------------------------------------------------------

export type IssueStatus = 'doing' | 'done' | 'archived' | 'abandoned'

export interface Issue {
  id: number
  title: string
  description: string | null
  status: IssueStatus
  position: number
  message_count: number
  created_at: string
  updated_at: string
  completed_at: string | null
}

export interface IssueBoard {
  doing: Issue[]
  done: Issue[]
  archived: Issue[]
  abandoned: Issue[]
}

export interface DashboardStats {
  message_count: number
  media_count: number
  media_this_month: number
  todo_doing_count: number
}

// ---------------------------------------------------------------------------
// Smart / CLIP
// ---------------------------------------------------------------------------

export interface TagSuggestion {
  tag_id: number
  name: string
  category: string | null
  score: number
}

export interface SmartStatus {
  available: boolean
  model: string
  reason: string | null
}
