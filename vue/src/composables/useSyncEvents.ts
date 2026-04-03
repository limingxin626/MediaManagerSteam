import { onMounted, onUnmounted } from 'vue'
import { API_BASE_URL } from '../utils/constants'

export type SyncEventCallback = (entityType: string, entityId: number, operation: string) => void

/**
 * SSE 实时同步事件订阅器
 *
 * 连接后端 GET /sync/events，收到变更通知后调用 onchange 回调。
 * 仅在组件挂载时连接，卸载时断开。自动重连（指数退避）。
 *
 * 用法：
 * ```ts
 * useSyncEvents((entityType, entityId, operation) => {
 *   if (entityType === 'MESSAGE' && operation === 'UPSERT') {
 *     refreshMessage(entityId)
 *   }
 * })
 * ```
 */
export function useSyncEvents(onchange: SyncEventCallback) {
  let es: EventSource | null = null
  let retryDelay = 2000
  let retryTimer: ReturnType<typeof setTimeout> | null = null
  let stopped = false

  function connect() {
    if (stopped) return
    es = new EventSource(`${API_BASE_URL}/sync/events`)

    es.onopen = () => {
      retryDelay = 2000
    }

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'connected') return
        onchange(data.entity_type, data.entity_id, data.operation)
      } catch {
        // ignore malformed messages
      }
    }

    es.onerror = () => {
      es?.close()
      es = null
      scheduleReconnect()
    }
  }

  function scheduleReconnect() {
    if (stopped) return
    retryTimer = setTimeout(() => {
      retryDelay = Math.min(retryDelay * 2, 30000)
      connect()
    }, retryDelay)
  }

  function disconnect() {
    stopped = true
    if (retryTimer) clearTimeout(retryTimer)
    es?.close()
    es = null
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return { disconnect }
}
