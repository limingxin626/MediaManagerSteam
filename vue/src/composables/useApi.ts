import { ref, onUnmounted, type Ref } from 'vue'
import { API_BASE_URL } from '../utils/constants'

// ---------------------------------------------------------------------------
// ApiError
// ---------------------------------------------------------------------------

export class ApiError extends Error {
  status: number
  constructor(
    status: number,
    message: string,
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// ---------------------------------------------------------------------------
// Core fetch wrapper
// ---------------------------------------------------------------------------

type Params = Record<string, string | number | boolean | undefined | null>

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  params?: Params,
): Promise<T> {
  let url = `${API_BASE_URL}${path}`

  if (params) {
    const sp = new URLSearchParams()
    for (const [k, v] of Object.entries(params)) {
      if (v != null && v !== '') sp.set(k, String(v))
    }
    const qs = sp.toString()
    if (qs) url += `?${qs}`
  }

  const init: RequestInit = { method }
  if (body !== undefined) {
    init.headers = { 'Content-Type': 'application/json' }
    init.body = JSON.stringify(body)
  }

  const res = await fetch(url, init)

  if (!res.ok) {
    let msg = res.statusText
    try {
      const errBody = await res.json()
      msg = errBody.detail ?? errBody.message ?? msg
    } catch { /* ignore parse errors */ }
    throw new ApiError(res.status, msg)
  }

  // 204 No Content
  if (res.status === 204) return null as T

  return res.json() as Promise<T>
}

// ---------------------------------------------------------------------------
// API methods
// ---------------------------------------------------------------------------

export const api = {
  get<T>(path: string, params?: Params) {
    return request<T>('GET', path, undefined, params)
  },
  post<T>(path: string, body?: unknown) {
    return request<T>('POST', path, body)
  },
  put<T>(path: string, body?: unknown) {
    return request<T>('PUT', path, body)
  },
  patch<T>(path: string, body?: unknown) {
    return request<T>('PATCH', path, body)
  },
  del<T = null>(path: string) {
    return request<T>('DELETE', path)
  },
}

// ---------------------------------------------------------------------------
// useInfiniteScroll composable
// ---------------------------------------------------------------------------

interface InfiniteScrollOptions<T> {
  /** Fetch function — receives cursor & limit, returns paginated data */
  fetchFn: (params: { cursor: string | null; limit: number }) => Promise<{
    items: T[]
    next_cursor: string | null
    has_more: boolean
  }>
  /** Ref to the sentinel element */
  sentinel: Ref<HTMLElement | null>
  /** Items per page */
  limit?: number
  /** IntersectionObserver rootMargin */
  rootMargin?: string
}

export function useInfiniteScroll<T>(options: InfiniteScrollOptions<T>) {
  const { fetchFn, sentinel, limit = 20, rootMargin = '200px' } = options

  const items = ref<T[]>([]) as Ref<T[]>
  const loading = ref(false)
  const hasMore = ref(true)
  const nextCursor = ref<string | null>(null)

  let observer: IntersectionObserver | null = null

  const load = async (reset = false) => {
    if (loading.value) return
    if (!reset && !hasMore.value) return

    if (reset) {
      items.value = []
      nextCursor.value = null
      hasMore.value = true
    }

    loading.value = true
    try {
      const data = await fetchFn({ cursor: reset ? null : nextCursor.value, limit })
      if (reset) {
        items.value = data.items
      } else {
        items.value.push(...data.items)
      }
      nextCursor.value = data.next_cursor
      hasMore.value = data.has_more
    } finally {
      loading.value = false
    }
  }

  const setupObserver = () => {
    observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting && !loading.value && hasMore.value) {
          load()
        }
      },
      { rootMargin },
    )
    if (sentinel.value) observer.observe(sentinel.value)
  }

  const reset = () => load(true)

  onUnmounted(() => {
    observer?.disconnect()
  })

  return { items, loading, hasMore, load, reset, setupObserver }
}
