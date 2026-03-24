// 消息相关类型
export interface MessageMediaItem {
  id: number
  file_path: string
  mime_type: string | null
  duration: number | null
}

export interface Message {
  id: number
  text: string | null
  actor_id: number | null
  actor_name: string | null
  media_count: number
  created_at: string
  updated_at: string
}

export interface MessageDetail extends Message {
  media_items: MessageMediaItem[]
}

// 演员相关类型
export interface Actor {
  id: number
  name: string
  description: string | null
  avatar_path: string | null
  message_count: number
  created_at: string
  updated_at: string
}

export interface ActorDetail extends Actor {
  messages: Array<{
    id: number
    text: string | null
    media_count: number
    created_at: string
  }>
}

// 媒体相关类型
export interface Media {
  id: number
  file_path: string
  file_hash: string | null
  file_size: number | null
  mime_type: string | null
  width: number | null
  height: number | null
  duration: number | null
  rating: number
  view_count: number
  last_viewed_at: string | null
  created_at: string
  updated_at: string
}

// 分组相关类型
export interface Group {
  id: number
  name: string
  description: string | null
  cover_image: string | null
  serial_number: string | null
  release_date: string | null
  rating: number | null
  actor_id: number
  size: number
  media_cnt: number
  created_at: string
  updated_at: string
}

// 标签相关类型
export interface Tag {
  id: number
  type: string
  name: string
}

// 通用类型
export interface ViewMode {
  type: 'grid' | 'list'
}