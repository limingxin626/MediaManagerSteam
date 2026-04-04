<template>
  <div class="h-screen flex 2xl:pr-72 transition-colors">
    <!-- Left Tag Column -->
    <div class="flex flex-col w-48 shrink-0 border-r border-white/10 overflow-y-auto">
      <div class="px-3 pt-4 pb-2 text-xs font-semibold text-gray-400 uppercase tracking-wider shrink-0">标签</div>
      <div class="flex flex-col gap-0.5 px-2 pb-4">
        <button
          @click="selectTag(null)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left"
          :class="selectedTagId === null
            ? 'bg-indigo-600/30 text-indigo-300'
            : 'text-gray-300 hover:bg-white/10'"
        >
          <span>全部</span>
        </button>
        <button
          v-for="tag in tags"
          :key="tag.id"
          @click="selectTag(tag.id)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left"
          :class="selectedTagId === tag.id
            ? 'bg-indigo-600/30 text-indigo-300'
            : 'text-gray-300 hover:bg-white/10'"
        >
          <span class="truncate">{{ tag.name }}</span>
          <span class="ml-1 text-xs text-gray-500 shrink-0">{{ tag.message_count }}</span>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0">
    <!-- Search Header -->
    <div class="shrink-0 border-b border-white/10 shadow-sm">
      <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex gap-4 items-center max-w-2xl mx-auto">
          <h2 class="text-2xl font-bold text-white">消息流</h2>
          <!-- Merge toggle -->
          <button
            @click="toggleMergeMode"
            class="px-3 py-1.5 text-sm rounded-lg transition-colors"
            :class="mergeMode
              ? 'bg-indigo-600 text-white hover:bg-indigo-700'
              : 'bg-white/10 text-gray-300 hover:bg-white/20'"
          >
            {{ mergeMode ? '取消合并' : '合并' }}
          </button>
          <!-- Starred filter -->
          <button
            @click="starredFilter = !starredFilter; resetAndFetch()"
            class="p-1.5 rounded-lg transition-colors"
            :class="starredFilter
              ? 'text-yellow-400 bg-yellow-900/20'
              : 'text-gray-400 hover:text-yellow-400 bg-white/10'"
            title="仅看收藏"
          >
            <svg class="w-5 h-5" :fill="starredFilter ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
            </svg>
          </button>
          <!-- Search -->
          <SearchInput v-model="searchQuery" placeholder="搜索消息..." @search="onSearch" />
        </div>
      </div>
    </div>

    <!-- Scrollable Content Area -->
    <div ref="scrollContainer" class="flex-1 overflow-y-auto min-h-0 relative">
      <!-- Scroll sentinel for loading older messages -->
      <div ref="topSentinel" class="h-1"></div>

      <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <!-- Loading skeleton (initial load) -->
        <div v-if="loading && messages.length === 0" class="flex flex-col gap-4 max-w-2xl mx-auto">
          <div v-for="i in 3" :key="i" class="bg-(--color-card-bg) rounded-xl border border-white/10 p-4 animate-pulse">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-10 h-10 rounded-full bg-white/10"></div>
              <div class="flex-1">
                <div class="h-4 w-20 bg-white/10 rounded"></div>
                <div class="h-3 w-16 bg-white/10 rounded mt-1.5"></div>
              </div>
            </div>
            <div class="aspect-video bg-white/10 rounded-xl mb-2"></div>
            <div class="h-3 w-3/4 bg-white/10 rounded"></div>
            <div class="h-3 w-1/2 bg-white/10 rounded mt-1.5"></div>
          </div>
        </div>
        <div v-if="loading && messages.length > 0" class="text-center py-4">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-indigo-500"></div>
        </div>

        <!-- No more data -->
        <div v-if="!loading && !hasMoreData && messages.length > 0" class="text-center py-8">
          <p class="text-sm text-gray-400">已经到底了</p>
        </div>

        <!-- Messages Feed -->
        <div v-if="messages.length > 0" class="flex flex-col gap-4 max-w-2xl mx-auto">
          <template
            v-for="(message, idx) in messages"
            :key="message.id"
          >
            <!-- Date separator -->
            <div
              v-if="idx === 0 || getDateStr(message.created_at) !== getDateStr(messages[idx - 1].created_at)"
              class="flex items-center gap-3 py-2"
            >
              <div class="flex-1 h-px bg-white/10"></div>
              <span class="text-xs text-gray-400 whitespace-nowrap">{{ formatDateLabel(message.created_at) }}</span>
              <div class="flex-1 h-px bg-white/10"></div>
            </div>
            <div :data-message-date="message.created_at.substring(0, 10)">
              <MessageCard
                :message="message"
                :media-items="message.media_items"
                :tags="message.tags"
                :selectable="mergeMode"
                :selected="selectedMessageIds.has(message.id)"
                @media-click="(index) => handleMediaClick(message.id, index)"
                @delete="handleDeleteMessage"
                @find-messages-by-media="handleFindMessagesByMedia"
                @toggle-select="toggleSelectMessage"
                @toggle-star="handleToggleStar"
                @toggle-media-star="handleToggleMediaStar"
              />
            </div>
          </template>
        </div>

        <!-- Empty State -->
        <div v-if="messages.length === 0 && !loading" class="text-center py-12">
          <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <h3 class="mt-2 text-sm font-medium text-white">暂无消息</h3>
          <p class="mt-1 text-sm text-gray-400">还没有任何消息内容</p>
        </div>

        <!-- Loading indicator (bottom, for loading newer) -->
        <div v-if="loadingForward" class="text-center py-4">
          <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-indigo-500"></div>
        </div>
      </div>

      <!-- Scroll sentinel for loading newer messages -->
      <div ref="bottomSentinel" class="h-1"></div>

      <!-- Merge action bar -->
      <div
        v-if="mergeMode && selectedMessageIds.size > 0"
        class="sticky bottom-4 z-50 flex items-center justify-center pointer-events-none"
      >
        <div class="pointer-events-auto flex items-center gap-3 px-5 py-3 bg-gray-900/90 backdrop-blur-sm rounded-full shadow-xl text-white text-sm">
          <span>已选 {{ selectedMessageIds.size }} 条</span>
          <button
            @click="handleMerge"
            :disabled="selectedMessageIds.size < 2"
            class="px-4 py-1.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 rounded-full font-medium transition-colors"
          >
            合并
          </button>
          <button
            @click="toggleMergeMode"
            class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-full transition-colors"
          >
            取消
          </button>
        </div>
      </div>

      <!-- "回到最新" floating button -->
      <button
        v-if="isViewingHistory"
        @click="backToLatest"
        class="sticky bottom-4 left-full -translate-x-6 z-50 flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-full shadow-lg transition-colors w-fit ml-auto mr-6"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
        </svg>
        回到最新
      </button>
    </div>

    <!-- Input Area at Bottom -->
    <MessageCompose
      :tag-id="selectedTagId ?? null"
      @sent="onMessageSent"
    />

    <MediaPreview
      :is-open="previewOpen"
      :items="previewItems"
      :start-index="previewStartIndex"
      :starred="previewMessageStarred"
      @close="closePreview"
      @navigate-prev="navigateToPrevMessage"
      @navigate-next="navigateToNextMessage"
      @toggle-star="handlePreviewToggleStar"
    />

    <!-- Calendar Sidebar (wide screens only) -->
    <aside class="hidden 2xl:block fixed top-0 right-0 bottom-0 w-72 border-l border-white/10 backdrop-blur-sm z-40 overflow-y-auto p-4 pt-6">
      <CalendarSidebar
        :active-filters="calendarFilters"
        @date-selected="handleDateSelected"
      />
    </aside>
  </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { type MessageDetail, type MessageMediaItem, type TagWithCount } from '../types'
import MessageCard from '../components/MessageCard.vue'
import MediaPreview from '../components/MediaPreview.vue'
import CalendarSidebar from '../components/CalendarSidebar.vue'
import SearchInput from '../components/SearchInput.vue'
import MessageCompose from '../components/MessageCompose.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'

defineOptions({ name: 'Message' })

const toast = useToast()

const tags = ref<TagWithCount[]>([])
const selectedTagId = ref<number | null | undefined>(undefined)

const fetchTags = async () => {
  try {
    tags.value = await api.get<TagWithCount[]>('/tags')
  } catch {
    // Tags are non-critical; silent fail
  }
}

const selectTag = (tagId: number | null) => {
  selectedTagId.value = tagId
  resetAndFetch()
}

const messages = ref<MessageDetail[]>([])
const loading = ref(false)
const searchQuery = ref('')

const pageSize = 20
const hasMoreData = ref(true)
const nextCursor = ref<string | null>(null)
const activeMediaFilter = ref<number | null>(null)
const starredFilter = ref(false)

const scrollContainer = ref<HTMLElement | null>(null)
const topSentinel = ref<HTMLElement | null>(null)
const bottomSentinel = ref<HTMLElement | null>(null)

const previewOpen = ref(false)
const previewItems = ref<MessageMediaItem[]>([])
const previewStartIndex = ref(0)
const currentMessageIndex = ref(-1)

const previewMessageStarred = computed(() => {
  if (currentMessageIndex.value < 0) return false
  return messages.value[currentMessageIndex.value]?.starred ?? false
})


// --- Merge selection mode ---
const mergeMode = ref(false)
const selectedMessageIds = ref<Set<number>>(new Set())

// --- Forward (newer) pagination state ---
const forwardCursor = ref<string | null>(null)
const hasMoreForward = ref(false)
const loadingForward = ref(false)
const isViewingHistory = ref(false)

const calendarFilters = computed(() => ({
  queryText: searchQuery.value || null,
  mediaId: activeMediaFilter.value,
}))

// --- Scroll helpers ---

const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
  const el = scrollContainer.value
  if (el) el.scrollTo({ top: el.scrollHeight, behavior })
}

// --- Calendar date jump ---

const handleDateSelected = async (dateStr: string) => {
  // Check if any loaded message is on this date
  const target = messages.value.find(m => m.created_at.startsWith(dateStr))
  if (target) {
    const el = document.querySelector(`[data-message-date="${dateStr}"]`)
    el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    return
  }

  // Load messages up to the end of the selected date (desc order, like default)
  // Use next day T00:00:00 as cursor so created_at < next day covers the whole day
  const nextDay = new Date(dateStr + 'T00:00:00')
  nextDay.setDate(nextDay.getDate() + 1)
  const cursorValue = nextDay.toISOString().slice(0, 19) // YYYY-MM-DDTHH:MM:SS

  loading.value = true
  try {
    const data = await api.get<{
      items: MessageDetail[]
      next_cursor: string | null
      has_more: boolean
    }>('/messages/with-detail', {
      cursor: cursorValue,
      limit: pageSize,
      query_text: searchQuery.value || undefined,
      media_id: activeMediaFilter.value ?? undefined,
      starred: starredFilter.value || undefined,
      tag_id: selectedTagId.value ?? undefined,
    })

    // desc order returned, reverse for chat layout (newest at bottom)
    messages.value = data.items.reverse()
    hasMoreData.value = data.has_more
    nextCursor.value = data.next_cursor

    // There are newer messages after this date
    const today = new Date().toISOString().slice(0, 10)
    hasMoreForward.value = dateStr < today
    forwardCursor.value = messages.value.length
      ? messages.value[messages.value.length - 1].created_at
      : null
    isViewingHistory.value = hasMoreForward.value

    await nextTick()
    const el = document.querySelector(`[data-message-date="${dateStr}"]`)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' })
    } else {
      scrollToBottom()
    }
  } catch {
    toast.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

const fetchForwardMessages = async () => {
  if (loadingForward.value || !hasMoreForward.value || !forwardCursor.value) return

  loadingForward.value = true
  try {
    const data = await api.get<{
      items: MessageDetail[]
      next_cursor: string | null
      has_more: boolean
    }>('/messages/with-detail', {
      cursor: forwardCursor.value,
      direction: 'forward',
      limit: pageSize,
      query_text: searchQuery.value || undefined,
      media_id: activeMediaFilter.value ?? undefined,
      starred: starredFilter.value || undefined,
      tag_id: selectedTagId.value ?? undefined,
    })

    const container = scrollContainer.value
    const previousScrollY = container?.scrollTop ?? 0
    const previousHeight = container?.scrollHeight ?? 0

    messages.value.push(...data.items)
    hasMoreForward.value = data.has_more
    forwardCursor.value = data.next_cursor

    if (!data.has_more) {
      isViewingHistory.value = false
    }

    await nextTick()
    if (container) {
      const scrollDelta = container.scrollHeight - previousHeight
      if (scrollDelta > 0 && previousScrollY + container.clientHeight < previousHeight) {
        container.scrollTo({ top: previousScrollY, behavior: 'auto' })
      }
    }
  } catch {
    toast.error('加载消息失败')
  } finally {
    loadingForward.value = false
  }
}

const backToLatest = () => {
  isViewingHistory.value = false
  hasMoreForward.value = false
  forwardCursor.value = null
  resetAndFetch()
}

// --- Send message ---

const onMessageSent = async (message: MessageDetail) => {
  messages.value.push(message)
  await nextTick()
  scrollToBottom()
}

// --- Fetch messages (unified) ---

const resetAndFetch = (params?: { mediaId?: number }) => {
  messages.value = []
  nextCursor.value = null
  hasMoreData.value = true
  activeMediaFilter.value = params?.mediaId ?? null
  fetchMessages()
}

const fetchMessages = async (isLoadingMore = false) => {
  if (loading.value) return
  if (isLoadingMore && !hasMoreData.value) return
  if (selectedTagId.value === undefined) return

  loading.value = true
  try {
    const data = await api.get<{ items: MessageDetail[]; next_cursor: string | null; has_more: boolean }>(
      '/messages/with-detail',
      {
        limit: pageSize,
        cursor: isLoadingMore ? nextCursor.value : undefined,
        query_text: searchQuery.value || undefined,
        media_id: activeMediaFilter.value ?? undefined,
        starred: starredFilter.value || undefined,
        tag_id: selectedTagId.value ?? undefined,
      },
    )

    hasMoreData.value = data.has_more
    nextCursor.value = data.next_cursor

    const container = scrollContainer.value
    const previousScrollY = container?.scrollTop ?? 0
    const previousHeight = container?.scrollHeight ?? 0

    if (isLoadingMore) {
      messages.value = [...data.items.reverse(), ...messages.value]
    } else {
      messages.value = data.items.reverse()
    }

    await nextTick()
    if (!isLoadingMore) {
      scrollToBottom('auto')
    } else if (container) {
      const scrollDelta = container.scrollHeight - previousHeight
      container.scrollTo({ top: previousScrollY + scrollDelta, behavior: 'auto' })
    }
  } catch (error) {
    toast.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

// --- Media preview ---

const handleMediaClick = (messageId: number, mediaIndex: number) => {
  const message = messages.value.find(m => m.id === messageId)
  if (!message?.media_items) return

  currentMessageIndex.value = messages.value.findIndex(m => m.id === messageId)
  previewItems.value = message.media_items
  previewStartIndex.value = mediaIndex
  previewOpen.value = true
}

const closePreview = () => {
  previewOpen.value = false
  previewItems.value = []
  currentMessageIndex.value = -1
}

const handlePreviewToggleStar = async (mediaId: number) => {
  try {
    const currentItem = previewItems.value.find(item => item.id === mediaId)
    if (!currentItem) return
    
    const newStarredState = !currentItem.starred
    await api.put(`/media/${mediaId}/starred?starred=${newStarredState}`)
    
    // 更新当前预览项的状态
    currentItem.starred = newStarredState
    
    // 更新消息中的媒体项状态
    if (currentMessageIndex.value >= 0) {
      const msg = messages.value[currentMessageIndex.value]
      if (msg?.media_items) {
        const mediaItem = msg.media_items.find(item => item.id === mediaId)
        if (mediaItem) {
          mediaItem.starred = newStarredState
        }
      }
    }
  } catch (error) {
    console.error('切换收藏状态失败:', error)
    toast.error('操作失败')
  }
}

const handleToggleMediaStar = async (mediaId: number) => {
  try {
    // 找到包含该媒体的消息
    for (const message of messages.value) {
      if (message.media_items) {
        const mediaItem = message.media_items.find(item => item.id === mediaId)
        if (mediaItem) {
          const newStarredState = !mediaItem.starred
          await api.put(`/media/${mediaId}/starred?starred=${newStarredState}`)
          mediaItem.starred = newStarredState
          return
        }
      }
    }
  } catch (error) {
    console.error('切换媒体收藏状态失败:', error)
    toast.error('操作失败')
  }
}

const navigateToPrevMessage = () => {
  for (let i = currentMessageIndex.value - 1; i >= 0; i--) {
    const msg = messages.value[i]
    if (msg?.media_items?.length) {
      currentMessageIndex.value = i
      previewItems.value = msg.media_items
      previewStartIndex.value = msg.media_items.length - 1
      return
    }
  }
}

const navigateToNextMessage = () => {
  for (let i = currentMessageIndex.value + 1; i < messages.value.length; i++) {
    const msg = messages.value[i]
    if (msg?.media_items?.length) {
      currentMessageIndex.value = i
      previewItems.value = msg.media_items
      previewStartIndex.value = 0
      return
    }
  }
}

// --- Star toggle ---

const handleToggleStar = async (messageId: number) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (!msg) return

  try {
    const updated = await api.patch<MessageDetail>(`/messages/${messageId}`, {
      starred: !msg.starred,
    })
    msg.starred = updated.starred
  } catch {
    toast.error('操作失败')
  }
}

// --- Delete ---

const handleDeleteMessage = async (messageId: number) => {
  if (!confirm('确定要删除这条消息吗？')) return

  try {
    await api.del(`/messages/${messageId}`)
    messages.value = messages.value.filter((m: MessageDetail) => m.id !== messageId)
    toast.success('消息已删除')
  } catch (error) {
    toast.error('删除消息失败')
  }
}

// --- Merge ---

const toggleMergeMode = () => {
  mergeMode.value = !mergeMode.value
  selectedMessageIds.value.clear()
}

const toggleSelectMessage = (id: number) => {
  if (selectedMessageIds.value.has(id)) {
    selectedMessageIds.value.delete(id)
  } else {
    selectedMessageIds.value.add(id)
  }
}

const handleMerge = async () => {
  if (selectedMessageIds.value.size < 2) {
    toast.error('请至少选择两条消息')
    return
  }
  if (!confirm(`确定要合并这 ${selectedMessageIds.value.size} 条消息吗？合并后不可撤销。`)) return

  try {
    const merged = await api.post<MessageDetail>('/messages/merge', {
      message_ids: Array.from(selectedMessageIds.value),
    })

    // 移除被合并的消息，替换为合并结果
    const mergedIds = selectedMessageIds.value
    const firstIdx = messages.value.findIndex(m => mergedIds.has(m.id))
    messages.value = messages.value.filter(m => !mergedIds.has(m.id))
    messages.value.splice(firstIdx >= 0 ? firstIdx : 0, 0, merged)

    mergeMode.value = false
    selectedMessageIds.value.clear()
    toast.success('消息合并成功')
  } catch (error) {
    toast.error('合并消息失败')
  }
}

// --- Find by media ---

const handleFindMessagesByMedia = (mediaId: number) => {
  resetAndFetch({ mediaId })
}

// --- Search debounce ---


// --- Date helpers ---

const getDateStr = (dateString: string) => dateString.substring(0, 10)

const formatDateLabel = (dateString: string) => {
  const date = new Date(dateString)
  const now = new Date()
  const todayStr = now.toISOString().substring(0, 10)
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  const yesterdayStr = yesterday.toISOString().substring(0, 10)
  const ds = dateString.substring(0, 10)

  if (ds === todayStr) return '今天'
  if (ds === yesterdayStr) return '昨天'
  if (date.getFullYear() === now.getFullYear()) {
    return `${date.getMonth() + 1}月${date.getDate()}日`
  }
  return `${date.getFullYear()}年${date.getMonth() + 1}月${date.getDate()}日`
}

function onSearch() {
  activeMediaFilter.value = null
  resetAndFetch()
}

// --- Infinite scroll via IntersectionObserver ---

let topObserver: IntersectionObserver | null = null
let bottomObserver: IntersectionObserver | null = null

onMounted(() => {
  fetchTags()
  fetchMessages()

  const root = scrollContainer.value

  topObserver = new IntersectionObserver(
    (entries) => {
      const container = scrollContainer.value
      if (entries[0].isIntersecting && !loading.value && hasMoreData.value && container && container.scrollTop > 0) {
        fetchMessages(true)
      }
    },
    { root, rootMargin: '200px' }
  )
  if (topSentinel.value) topObserver.observe(topSentinel.value)

  bottomObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && !loadingForward.value && hasMoreForward.value) {
        fetchForwardMessages()
      }
    },
    { root, rootMargin: '200px' }
  )
  if (bottomSentinel.value) bottomObserver.observe(bottomSentinel.value)
})

onUnmounted(() => {
  topObserver?.disconnect()
  bottomObserver?.disconnect()
})
</script>
