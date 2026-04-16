<template>
  <div class="h-screen flex transition-colors">
    <!-- Left Tag Column -->
    <div class="flex flex-col w-48 shrink-0 border-r border-[var(--border-color)] overflow-y-auto">
      <div class="px-3 pt-4 pb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider shrink-0">标签</div>
      <div class="flex flex-col gap-0.5 px-2 pb-4">
        <button @click="selectTag(null)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left" :class="selectedTagId === null
            ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
          <span>全部</span>
        </button>
        <button v-for="tag in tags" :key="tag.id" @click="selectTag(tag.id)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left" :class="selectedTagId === tag.id
            ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
          <span class="truncate">{{ tag.name }}</span>
          <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ tag.message_count }}</span>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex min-w-0">
      <!-- Left Feed Section -->
      <div class="flex flex-col min-w-0 relative" :class="selectedMessage ? 'w-1/2' : 'flex-1'">
        <!-- Search Header -->
        <div class="shrink-0 border-b border-[var(--border-color)] shadow-sm">
          <div class="w-full mx-auto px-3 py-2">
            <div class="flex gap-2 items-center max-w-4xl mx-auto">
              <h2 class="text-base font-semibold text-gray-900 dark:text-white">消息流</h2>
              <!-- Merge toggle -->
              <button @click="toggleMergeMode" class="px-2 py-1 text-xs rounded-md transition-colors" :class="mergeMode
                ? 'bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)]'
                : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-white/20'">
                {{ mergeMode ? '取消合并' : '合并' }}
              </button>
              <!-- Starred filter -->
              <button @click="starredFilter = !starredFilter; resetAndFetch()"
                class="p-1 rounded-md transition-colors" :class="starredFilter
                  ? 'text-yellow-400 bg-yellow-900/20'
                  : 'text-gray-400 hover:text-yellow-400 bg-gray-100 dark:bg-white/10'" title="仅看收藏">
                <svg class="w-4 h-4" :fill="starredFilter ? 'currentColor' : 'none'" stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
              <!-- Search -->
              <SearchInput v-model="searchQuery" placeholder="搜索消息..." @search="onSearch" />
            </div>
          </div>
        </div>

        <!-- Scrollable Content Area -->
        <div ref="scrollContainer" class="flex-1 overflow-y-auto min-h-0 relative">
          <!-- Floating date badge -->
          <div v-if="currentVisibleDate" class="sticky top-0 z-20 flex justify-center py-2 pointer-events-none">
            <span class="px-3 py-1 text-xs text-[var(--text-secondary)] bg-[var(--bg-card)]/80 dark:bg-white/10 backdrop-blur-md rounded-full border border-[var(--border-color)] shadow-sm">{{ currentVisibleDate }}</span>
          </div>
          <!-- Scroll sentinel for loading older messages -->
          <div ref="topSentinel" class="h-1"></div>

          <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <!-- Loading skeleton (initial load) -->
            <div v-if="loading && messages.length === 0" class="flex flex-col gap-4 max-w-4xl mx-auto">
              <div v-for="i in 3" :key="i"
                class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-4 animate-pulse">
                <div class="flex items-center gap-3 mb-3">
                  <div class="w-10 h-10 rounded-full bg-gray-200 dark:bg-white/10"></div>
                  <div class="flex-1">
                    <div class="h-4 w-20 bg-gray-200 dark:bg-white/10 rounded"></div>
                    <div class="h-3 w-16 bg-gray-200 dark:bg-white/10 rounded mt-1.5"></div>
                  </div>
                </div>
                <div class="aspect-video bg-gray-200 dark:bg-white/10 rounded-xl mb-2"></div>
                <div class="h-3 w-3/4 bg-gray-200 dark:bg-white/10 rounded"></div>
                <div class="h-3 w-1/2 bg-gray-200 dark:bg-white/10 rounded mt-1.5"></div>
              </div>
            </div>
            <div v-if="loading && messages.length > 0" class="text-center py-4">
              <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
            </div>

            <!-- No more data -->
            <div v-if="!loading && !hasMoreData && messages.length > 0" class="text-center py-8">
              <p class="text-sm text-gray-400">已经到底了</p>
            </div>

            <!-- Messages Feed -->
            <div v-if="messages.length > 0" class="flex flex-col gap-4 max-w-4xl mx-auto">
              <template v-for="(message, idx) in messages" :key="message.id">
                <!-- Date separator -->
                <div v-if="idx === 0 || getDateStr(message.created_at) !== getDateStr(messages[idx - 1]?.created_at ?? '')"
                  class="flex justify-center py-2">
                  <span class="px-3 py-1 text-xs text-[var(--text-secondary)] bg-[var(--bg-card)]/80 dark:bg-white/10 backdrop-blur-md rounded-full border border-[var(--border-color)] shadow-sm">{{ formatDateLabel(message.created_at) }}</span>
                </div>
                <div :data-message-date="message.created_at.substring(0, 10)">
                  <MessageCard :message="message" :media-items="message.media_items" :tags="message.tags"
                    :selectable="mergeMode" :selected="selectedMessageIds.has(message.id)"
                    @click="handleMessageClick(message)" @media-click="(index) => handleMediaClick(message.id, index)"
                    @delete="handleDeleteMessage" @find-messages-by-media="handleFindMessagesByMedia"
                    @toggle-select="toggleSelectMessage" @toggle-star="handleToggleStar"
                    @toggle-media-star="handleToggleMediaStar" @edit="openEditDialog" />
                </div>
              </template>
            </div>

            <!-- Empty State -->
            <div v-if="messages.length === 0 && !loading" class="flex flex-col items-center justify-center py-20">
              <div class="relative w-24 h-24 mb-4">
                <div class="absolute inset-0 rounded-2xl bg-[var(--color-primary-500)]/10 rotate-6"></div>
                <div class="absolute inset-0 rounded-2xl bg-[var(--color-primary-500)]/5 -rotate-3"></div>
                <div class="absolute inset-0 flex items-center justify-center">
                  <svg class="w-10 h-10 text-[var(--color-primary-500)]/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
              </div>
              <h3 class="text-sm font-medium text-[var(--text-primary)]">暂无消息</h3>
              <p class="mt-1 text-sm text-[var(--text-muted)]">还没有任何消息内容</p>
            </div>

            <!-- Loading indicator (bottom, for loading newer) -->
            <div v-if="loadingForward" class="text-center py-4">
              <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
            </div>
          </div>

          <!-- Scroll sentinel for loading newer messages -->
          <div ref="bottomSentinel" class="h-1"></div>

          <!-- Merge action bar -->
          <div v-if="mergeMode && selectedMessageIds.size > 0"
            class="sticky bottom-4 z-50 flex items-center justify-center pointer-events-none">
            <div
              class="pointer-events-auto flex items-center gap-3 px-5 py-3 bg-gray-900/90 backdrop-blur-sm rounded-full shadow-xl text-white text-sm">
              <span>已选 {{ selectedMessageIds.size }} 条</span>
              <button @click="handleMerge" :disabled="selectedMessageIds.size < 2"
                class="px-4 py-1.5 bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-700)] disabled:bg-gray-600 rounded-full font-medium transition-colors">
                合并
              </button>
              <button @click="toggleMergeMode"
                class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-full transition-colors">
                取消
              </button>
            </div>
          </div>

          <!-- "回到最新" floating button -->
          <button v-if="isViewingHistory" @click="backToLatest"
            class="sticky bottom-4 left-full -translate-x-6 z-50 flex items-center gap-2 px-4 py-2 bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-700)] text-white text-sm font-medium rounded-full shadow-lg transition-colors w-fit ml-auto mr-6">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
            回到最新
          </button>
        </div>

        <!-- Bottom Input Bar -->
        <div class="shrink-0 px-4 py-3 border-t border-[var(--border-color)] mb-20 md:mb-0">
          <div class="max-w-4xl mx-auto">
            <button @click="openCreateDialog"
              class="w-full flex items-center gap-3 px-4 py-3 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-full text-sm text-[var(--text-muted)] hover:border-[var(--color-primary-500)] transition-colors cursor-text">
              <span class="flex-1 text-left">写点什么...</span>
              <svg class="w-5 h-5 text-[var(--color-primary-500)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Right Detail Panel -->
      <div v-if="selectedMessage" class="flex-1 min-w-0 border-l border-[var(--border-color)] flex flex-col overflow-hidden">
        <!-- Header -->
        <div class="px-4 py-3 border-b border-[var(--border-color)] flex items-center justify-between shrink-0">
          <span class="text-sm font-semibold text-gray-900 dark:text-white">消息详情</span>
          <div class="flex items-center gap-2">
            <div v-if="selectedMessageLoading"
              class="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-[var(--color-primary-500)]">
            </div>
            <button @click="selectedMessage = null"
              class="p-1 text-gray-400 hover:text-gray-200 rounded transition-colors" title="关闭">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <!-- Scrollable body -->
        <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
          <!-- Full text -->
          <div v-if="selectedMessage.text"
            class="prose dark:prose-invert prose-sm max-w-none text-gray-700 dark:text-gray-300"
            v-html="renderDetailText(selectedMessage.text)">
          </div>
          <!-- Tags -->
          <div v-if="selectedMessage.tags && selectedMessage.tags.length > 0" class="flex flex-wrap gap-1.5">
            <span v-for="t in selectedMessage.tags" :key="t.id"
              class="tag-chip">
              {{ t.name }}
            </span>
          </div>
          <!-- All media -->
          <div v-if="selectedMessage.media_items && selectedMessage.media_items.length > 0"
            class="grid grid-cols-3 gap-1">
            <div v-for="(media, index) in selectedMessage.media_items" :key="media.id"
              class="group aspect-square overflow-hidden relative rounded cursor-pointer hover:opacity-90 transition-opacity"
              @click="handleSelectedMessageMediaClick(index)">
              <img :src="resolveUrl(media.thumb_url)" class="w-full h-full object-cover" />
              <div v-if="media.mime_type && media.mime_type.startsWith('video')"
                class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div class="w-8 h-8 bg-black/40 rounded-full flex items-center justify-center border border-white/30">
                  <svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
              </div>
              <div v-if="media.duration_ms"
                class="absolute bottom-1 right-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
                {{ formatDuration(media.duration_ms) }}
              </div>
              <button @click.stop="handleToggleMediaStar(media.id)"
                class="absolute top-1 right-1 p-1 rounded-full transition-all" :class="media.starred
                  ? 'text-yellow-400'
                  : 'text-white/70 hover:text-yellow-400 opacity-0 group-hover:opacity-100'">
                <svg class="w-4 h-4" :fill="media.starred ? 'currentColor' : 'none'" stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
            </div>
          </div>
          <!-- Date -->
          <p class="text-xs text-gray-500">{{ formatDateLabel(selectedMessage.created_at) }}</p>
        </div>
      </div>

      <MessageComposeDialog :visible="dialogVisible" :mode="dialogMode" :message-id="dialogMessageId"
        :initial-text="dialogInitialText" :initial-date="dialogInitialDate" :all-tags="tags"
        :tag-id="selectedTagId ?? null" :actor-id="undefined" @close="dialogVisible = false"
        @created="onDialogCreated" @updated="onDialogUpdated" />

      <MediaPreview :is-open="previewOpen" :items="previewItems" :start-index="previewStartIndex"
        :starred="previewMessageStarred" @close="closePreview" @navigate-prev="navigateToPrevMessage"
        @navigate-next="navigateToNextMessage" @toggle-star="handlePreviewToggleStar" />

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { marked } from 'marked'
import { type MessageDetail, type MessageMediaItem, type TagWithCount } from '../types'
import MessageCard from '../components/MessageCard.vue'
import MediaPreview from '../components/MediaPreview.vue'
import SearchInput from '../components/SearchInput.vue'
import MessageComposeDialog from '../components/MessageComposeDialog.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { resolveUrl, formatDuration } from '../utils/media'
import { formatDateLabel } from '../utils/date'


defineOptions({ name: 'Message' })

const toast = useToast()
const { confirm } = useConfirm()

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
const selectedMessage = ref<MessageDetail | null>(null)
const selectedMessageLoading = ref(false)

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

// --- Scroll helpers ---

const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
  const el = scrollContainer.value
  if (el) el.scrollTo({ top: el.scrollHeight, behavior })
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

// --- Compose dialog state ---

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const dialogMessageId = ref<number | undefined>(undefined)
const dialogInitialText = ref('')
const dialogInitialDate = ref('')

const openCreateDialog = () => {
  dialogMode.value = 'create'
  dialogMessageId.value = undefined
  dialogInitialText.value = ''
  dialogInitialDate.value = ''
  dialogVisible.value = true
}

const openEditDialog = (messageId: number) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (!msg) return

  dialogMode.value = 'edit'
  dialogMessageId.value = messageId
  dialogInitialText.value = msg.text || ''

  const dateStr = msg.created_at
  if (dateStr) {
    const date = new Date(dateStr)
    if (!isNaN(date.getTime())) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      dialogInitialDate.value = `${year}-${month}-${day}T${hours}:${minutes}`
    }
  }

  dialogVisible.value = true
}

const onDialogCreated = async (message: MessageDetail) => {
  messages.value.push(message)
  await nextTick()
  scrollToBottom()
}

const onDialogUpdated = async (messageId: number, text: string, date: string) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (!msg) return

  try {
    const updateData: Record<string, unknown> = { text: text || null }
    if (date) updateData.created_at = date

    const updated = await api.patch<MessageDetail>(`/messages/${messageId}`, updateData)
    msg.text = updated.text
    msg.created_at = updated.created_at
    msg.updated_at = updated.updated_at
    if (updated.tags) msg.tags = updated.tags
    toast.success('消息已更新')
  } catch {
    toast.error('更新消息失败')
  }
}

// --- Fetch messages (unified) ---

const resetAndFetch = (params?: { mediaId?: number }) => {
  nextCursor.value = null
  hasMoreData.value = true
  activeMediaFilter.value = params?.mediaId ?? null
  forwardCursor.value = null
  hasMoreForward.value = false
  isViewingHistory.value = false
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
  const ok = await confirm({ title: '确认删除', message: '确定要删除这条消息吗？', danger: true })
  if (!ok) return

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
  const ok = await confirm({
    title: '确认合并',
    message: `确定要合并这 ${selectedMessageIds.value.size} 条消息吗？合并后不可撤销。`,
    danger: true,
  })
  if (!ok) return

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

const handleSelectedMessageMediaClick = (mediaIndex: number) => {
  if (!selectedMessage.value?.media_items) return
  currentMessageIndex.value = messages.value.findIndex(m => m.id === selectedMessage.value!.id)
  previewItems.value = selectedMessage.value.media_items
  previewStartIndex.value = mediaIndex
  previewOpen.value = true
}

const handleMessageClick = async (message: MessageDetail) => {
  selectedMessage.value = message
  selectedMessageLoading.value = true
  try {
    const full = await api.get<MessageDetail>(`/messages/${message.id}`)
    if (selectedMessage.value?.id === message.id) {
      selectedMessage.value = full
    }
  } catch {
    // keep preview data on failure
  } finally {
    selectedMessageLoading.value = false
  }
}

const renderDetailText = (text: string) => {
  const normalized = text.replace(/([^\n])\n([-=]{2,})\n/g, '$1\n\n$2\n\n')
  marked.setOptions({ breaks: true })
  return marked.parse(normalized) as string
}

// --- Search debounce ---


// --- Date helpers ---

const getDateStr = (dateString: string) => dateString.substring(0, 10)

// --- Floating date badge ---
const currentVisibleDate = ref('')

const updateVisibleDate = () => {
  const container = scrollContainer.value
  if (!container || messages.value.length === 0) return

  // Find the first message element whose top is at or below the container's scroll top
  const containerRect = container.getBoundingClientRect()
  // offset to account for the sticky date badge height (~36px)
  const probeY = containerRect.top + 40

  const dateEls = container.querySelectorAll<HTMLElement>('[data-message-date]')
  let found = ''
  for (const el of dateEls) {
    const rect = el.getBoundingClientRect()
    if (rect.top <= probeY) {
      found = el.dataset.messageDate || ''
    } else {
      break
    }
  }

  if (!found && dateEls.length > 0) {
    found = dateEls[0].dataset.messageDate || ''
  }

  if (found) {
    currentVisibleDate.value = formatDateLabel(found + 'T00:00:00')
  }
}

let scrollRaf = 0
const onScrollForDate = () => {
  if (scrollRaf) cancelAnimationFrame(scrollRaf)
  scrollRaf = requestAnimationFrame(updateVisibleDate)
}

function onSearch() {
  activeMediaFilter.value = null
  resetAndFetch()
}

// --- Infinite scroll via IntersectionObserver ---

let topObserver: IntersectionObserver | null = null
let bottomObserver: IntersectionObserver | null = null

const setupObservers = () => {
  teardownObservers()
  const root = scrollContainer.value

  topObserver = new IntersectionObserver(
    (entries) => {
      const container = scrollContainer.value
      if (entries[0]?.isIntersecting && !loading.value && hasMoreData.value && container && container.scrollTop > 0) {
        fetchMessages(true)
      }
    },
    { root, rootMargin: '200px' }
  )
  if (topSentinel.value) topObserver.observe(topSentinel.value)

  bottomObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && !loadingForward.value && hasMoreForward.value) {
        fetchForwardMessages()
      }
    },
    { root, rootMargin: '200px' }
  )
  if (bottomSentinel.value) bottomObserver.observe(bottomSentinel.value)
}

const teardownObservers = () => {
  topObserver?.disconnect()
  topObserver = null
  bottomObserver?.disconnect()
  bottomObserver = null
}

onMounted(() => {
  fetchTags()
  fetchMessages()
  setupObservers()
  scrollContainer.value?.addEventListener('scroll', onScrollForDate, { passive: true })
})

onUnmounted(() => {
  teardownObservers()
  scrollContainer.value?.removeEventListener('scroll', onScrollForDate)
  if (scrollRaf) cancelAnimationFrame(scrollRaf)
})

// Update floating date after messages change
watch(messages, () => nextTick(updateVisibleDate), { flush: 'post' })
</script>
