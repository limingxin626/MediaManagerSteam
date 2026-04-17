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
