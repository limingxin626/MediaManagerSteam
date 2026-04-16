import type { CursorResponse } from '../../types'
import { api } from '../../composables/useApi'

export interface ColumnDef {
  key: string
  label: string
  type: 'string' | 'number' | 'datetime' | 'text'
  editable?: boolean
  truncate?: number
}

export interface TableDef {
  name: string
  label: string
  columns: ColumnDef[]
  apiList: (params: { cursor: string | null; limit: number; search?: string }) => Promise<CursorResponse<Record<string, unknown>>>
  apiUpdate?: (id: number, data: Record<string, unknown>) => Promise<unknown>
  apiDelete?: (id: number) => Promise<unknown>
  idField?: string
}

const messageDef: TableDef = {
  name: 'message',
  label: 'Message',
  columns: [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'text', label: '文本', type: 'text', editable: true, truncate: 80 },
    { key: 'actor_id', label: 'Actor ID', type: 'number' },
    { key: 'actor_name', label: '演员', type: 'string' },
    { key: 'media_count', label: '媒体数', type: 'number' },
    { key: 'starred', label: '收藏', type: 'number', editable: true },
    { key: 'created_at', label: '创建时间', type: 'datetime' },
    { key: 'updated_at', label: '更新时间', type: 'datetime' },
  ],
  apiList: ({ cursor, limit }) =>
    api.get<CursorResponse<Record<string, unknown>>>('/messages', { cursor, limit }),
  apiUpdate: (id, data) => api.patch(`/messages/${id}`, data),
  apiDelete: (id) => api.del(`/messages/${id}`),
}

const mediaDef: TableDef = {
  name: 'media',
  label: 'Media',
  columns: [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'file_path', label: '文件路径', type: 'string', truncate: 60 },
    { key: 'file_hash', label: '文件哈希', type: 'string', truncate: 16 },
    { key: 'file_size', label: '大小', type: 'number' },
    { key: 'mime_type', label: '类型', type: 'string' },
    { key: 'width', label: '宽', type: 'number' },
    { key: 'height', label: '高', type: 'number' },
    { key: 'duration_ms', label: '时长(ms)', type: 'number' },
    { key: 'rating', label: '评分', type: 'number', editable: true },
    { key: 'starred', label: '收藏', type: 'number', editable: true },
    { key: 'view_count', label: '播放数', type: 'number' },
    { key: 'created_at', label: '创建时间', type: 'datetime' },
  ],
  apiList: ({ cursor, limit }) =>
    api.get<CursorResponse<Record<string, unknown>>>('/media', { cursor, limit }),
  apiDelete: undefined,
}

const actorDef: TableDef = {
  name: 'actor',
  label: 'Actor',
  columns: [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'name', label: '名称', type: 'string', editable: true },
    { key: 'description', label: '简介', type: 'text', editable: true, truncate: 60 },
    { key: 'message_count', label: '消息数', type: 'number' },
    { key: 'created_at', label: '创建时间', type: 'datetime' },
    { key: 'updated_at', label: '更新时间', type: 'datetime' },
  ],
  apiList: ({ search }) =>
    // Actor API 不分页，包装为 CursorResponse
    api.get<Record<string, unknown>[]>('/actors', { name: search || undefined }).then(items => ({
      items, next_cursor: null, has_more: false,
    })),
  apiUpdate: (id, data) => api.put(`/actors/${id}`, data),
  apiDelete: (id) => api.del(`/actors/${id}`),
}

const tagDef: TableDef = {
  name: 'tag',
  label: 'Tag',
  columns: [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'name', label: '名称', type: 'string' },
    { key: 'category', label: '分类', type: 'string' },
    { key: 'message_count', label: '消息数', type: 'number' },
  ],
  apiList: ({ search }) =>
    api.get<Record<string, unknown>[]>('/tags', { name: search || undefined }).then(items => ({
      items, next_cursor: null, has_more: false,
    })),
}

const syncLogDef: TableDef = {
  name: 'sync_log',
  label: 'SyncLog',
  columns: [
    { key: 'id', label: 'ID', type: 'number' },
    { key: 'entity_type', label: '实体类型', type: 'string' },
    { key: 'entity_id', label: '实体ID', type: 'number' },
    { key: 'operation', label: '操作', type: 'string' },
    { key: 'timestamp', label: '时间', type: 'datetime' },
  ],
  apiList: ({ cursor, limit }) =>
    api.get<CursorResponse<Record<string, unknown>>>('/admin/sync-logs', { cursor, limit }),
}

export const tableDefs: TableDef[] = [messageDef, mediaDef, actorDef, tagDef, syncLogDef]
