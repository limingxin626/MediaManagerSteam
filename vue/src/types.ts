import type { components } from './types/api.generated'

// --- 从 OpenAPI 生成的类型中派生 ---

// 消息相关
export type MessageMediaItem = components['schemas']['MessageMediaItem']
export type Message = components['schemas']['MessageResponse']
export type MessageDetail = components['schemas']['MessageDetailResponse']

// 演员相关
export type Actor = components['schemas']['ActorResponse']
// 媒体相关
export type Media = components['schemas']['MediaResponse']

// 视频预览（章节）—— 后端尚未重新生成 OpenAPI 类型，先手写
export interface VideoPreviewItem {
  id: number
  file_path: string
  file_url: string
  thumb_url: string
  thumb_path?: string
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
    actor_id: number | null
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

export interface DashboardStats {
  message_count: number
  media_count: number
  media_this_month: number
  todo_doing_count: number
}
