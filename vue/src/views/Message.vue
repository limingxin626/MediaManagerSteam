<template>
  <div class="h-screen flex transition-colors">
    <FilterSidebar
      :tags="tags"
      :collections="collections"
      :no-collection-count="noCollectionCount"
      :selected-tag-id="selectedTagId"
      :selected-collection-id="selectedCollectionId"
      :issues="issues"
      :no-issue-count="noIssueCount"
      :selected-issue-id="selectedIssueId"
      :on-create-issue="promptCreateIssue"
      @select-tag="selectTag"
      @select-collection="selectCollection"
      @select-issue="selectIssue"
    />

    <!-- Main Content -->
    <div class="flex-1 flex min-w-0">
      <!-- Left Feed Section -->
      <div class="flex-1 flex flex-col min-w-0 relative">
        <!-- Search Header -->
        <div class="shrink-0 border-b border-[var(--border-color)] bg-[var(--bg-card)]">
          <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <div class="flex gap-2 items-center justify-between max-w-6xl mx-auto pr-10">
              <h2 class="text-base font-semibold text-[var(--text-primary)] tracking-tight">消息流</h2>
              <!-- New message -->
              <button @click="openCreateDialog"
                class="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-[var(--radius-sm)] bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)] transition-colors"
                title="新建消息">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                新建
              </button>
              <!-- Refresh -->
              <button @click="resetAndFetch()" :disabled="loading"
                class="p-1.5 rounded-[var(--radius-sm)] transition-colors text-[var(--text-muted)] hover:text-[var(--color-primary-600)] hover:bg-[var(--bg-secondary)] disabled:opacity-50 disabled:cursor-not-allowed"
                title="刷新">
                <svg class="w-4 h-4" :class="{ 'animate-spin': loading }" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </button>
              <!-- Merge toggle -->
              <button @click="toggleMergeMode" class="px-2.5 py-1 text-xs font-medium rounded-[var(--radius-sm)] transition-colors" :class="mergeMode
                ? 'bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)]'
                : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]'">
                {{ mergeMode ? '取消合并' : '合并' }}
              </button>
              <!-- Layout toggle (grid / mosaic / card 三态循环) -->
              <button @click="toggleLayout"
                class="p-1.5 rounded-[var(--radius-sm)] transition-colors text-[var(--text-muted)] hover:text-[var(--color-primary-600)] hover:bg-[var(--bg-secondary)]"
                :title="layoutToggleTitle">
                <!-- 显示当前布局图标 -->
                <!-- grid：卡内媒体网格 -->
                <svg v-if="messageLayout === 'grid'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 5a1 1 0 011-1h6a1 1 0 011 1v14a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v5a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM14 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1h-4a1 1 0 01-1-1v-3z" />
                </svg>
                <!-- mosaic：拼图 -->
                <svg v-else-if="messageLayout === 'mosaic'" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
                </svg>
                <!-- card：页面级卡片网格(相册) -->
                <svg v-else class="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M4 4h7v7H4V4zm9 0h7v7h-7V4zM4 13h7v7H4v-7zm9 0h7v7h-7v-7z" />
                </svg>
              </button>
              <!-- Starred filter -->
              <button @click="starredFilter = !starredFilter; resetAndFetch()"
                class="p-1.5 rounded-[var(--radius-sm)] transition-colors" :class="starredFilter
                  ? 'text-amber-400 bg-amber-400/10'
                  : 'text-[var(--text-muted)] hover:text-amber-400 hover:bg-[var(--bg-secondary)]'" title="仅看收藏">
                <svg class="w-4 h-4" :fill="starredFilter ? 'currentColor' : 'none'" stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
              <!-- Search -->
              <SearchInput v-model="searchQuery" placeholder="搜索消息..." @search="onSearch" />
              <!-- Media panel toggle -->
              <button @click="toggleMediaPanel"
                class="p-1.5 rounded-[var(--radius-sm)] transition-colors" :class="showMediaPanel
                  ? 'text-[var(--color-primary-600)] bg-[var(--color-primary-600)]/10'
                  : 'text-[var(--text-muted)] hover:text-[var(--color-primary-600)] hover:bg-[var(--bg-secondary)]'"
                :title="showMediaPanel ? '隐藏媒体网格' : '显示媒体网格'">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm0 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zm0 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Issue pinned banner -->
        <IssuePinnedBanner
          v-if="selectedIssue"
          :issue="selectedIssue"
          @clear="selectIssue(null)"
          @updated="onIssueUpdated"
        />

        <!-- Scrollable Content Area -->
        <div ref="scrollContainer" class="flex-1 overflow-y-auto min-h-0 relative">
          <!-- Floating date badge (clickable to open calendar) -->
          <div v-if="currentVisibleDate" class="sticky top-0 z-20 flex justify-center py-2">
            <div class="relative">
              <button @click="toggleCalendar"
                class="px-3 py-1 text-xs font-medium text-[var(--text-secondary)] bg-[var(--bg-card)]/85 backdrop-blur-md rounded-full border border-[var(--border-color)] shadow-[var(--shadow-sm)] hover:text-[var(--text-primary)] transition-colors cursor-pointer flex items-center gap-1.5">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {{ currentVisibleDate }}
              </button>
              <!-- Calendar popover -->
              <div v-show="calendarOpen" ref="calendarPopover"
                class="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl shadow-xl p-3"
                @focusin.stop @focusout.stop>
                <Calendar
                  :attributes="calendarAttributes"
                  :is-dark="isDark"
                  @update:pages="onCalendarPageChange"
                  @dayclick="onCalendarDayClick"
                  borderless
                  transparent
                />
              </div>
            </div>
          </div>

          <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <!-- Loading skeleton (initial load) -->
            <div v-if="loading && messages.length === 0" class="flex flex-col gap-4 max-w-4xl mx-auto">
              <div v-for="i in 3" :key="i"
                class="bg-[var(--bg-card)] rounded-[var(--radius-lg)] border border-[var(--border-color)] p-4 animate-pulse">
                <div class="flex items-center gap-3 mb-3">
                  <div class="w-9 h-9 rounded-full bg-[var(--bg-secondary)]"></div>
                  <div class="flex-1">
                    <div class="h-4 w-20 bg-[var(--bg-secondary)] rounded"></div>
                    <div class="h-3 w-16 bg-[var(--bg-secondary)] rounded mt-1.5"></div>
                  </div>
                </div>
                <div class="aspect-video bg-[var(--bg-secondary)] rounded-[var(--radius-md)] mb-2"></div>
                <div class="h-3 w-3/4 bg-[var(--bg-secondary)] rounded"></div>
                <div class="h-3 w-1/2 bg-[var(--bg-secondary)] rounded mt-1.5"></div>
              </div>
            </div>
            <div v-if="loading && messages.length > 0" class="text-center py-4">
              <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
            </div>

            <!-- No more data -->
            <div v-if="!loading && !hasMoreData && messages.length > 0" class="text-center py-8">
              <p class="text-xs text-[var(--text-muted)]">已经到底了</p>
            </div>

            <!-- Card grid layout (页面级固定卡片网格) -->
            <div v-if="messageLayout === 'card' && messages.length > 0"
              class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3 max-w-7xl mx-auto">
              <div v-for="message in messages" :key="message.id"
                :data-message-id="message.id" :data-message-date="message.created_at.substring(0, 10)"
                class="rounded-[var(--radius-lg)] transition-shadow"
                :class="highlightMessageId === message.id ? 'ring-2 ring-[var(--color-primary-500)]' : ''">
                <MessageGridCard :message="message" :media-items="message.media_items" :tags="message.tags"
                  :selectable="mergeMode" :selected="selectedMessageIds.has(message.id)"
                  @click="openDetailPanel" @toggle-select="toggleSelectMessage" />
              </div>
            </div>

            <!-- Messages Feed (grid / mosaic 消息流) -->
            <div v-else-if="messages.length > 0" class="flex flex-col gap-4 max-w-6xl mx-auto">
              <template v-for="(message, idx) in messages" :key="message.id">
                <!-- Date separator -->
                <div v-if="idx === 0 || getDateStr(message.created_at) !== getDateStr(messages[idx - 1]?.created_at ?? '')"
                  class="flex justify-center py-2">
                  <span class="px-3 py-1 text-xs font-medium text-[var(--text-muted)] bg-[var(--bg-card)]/85 backdrop-blur-md rounded-full border border-[var(--border-color)] shadow-[var(--shadow-sm)]">{{ formatDateLabel(message.created_at) }}</span>
                </div>
                <div :data-message-id="message.id" :data-message-date="message.created_at.substring(0, 10)"
                  class="rounded-xl transition-shadow"
                  :class="highlightMessageId === message.id ? 'ring-2 ring-[var(--color-primary-500)]' : ''">
                  <MessageCard :message="message" :media-items="message.media_items" :tags="message.tags"
                    :all-tags="tags" :layout="messageLayout === 'mosaic' ? 'mosaic' : 'grid'"
                    :selectable="mergeMode" :selected="selectedMessageIds.has(message.id)"
                    @click="openDetailPanel"
                    @media-click="(index) => handleMediaClick(message.id, index)"
                    @delete="handleDeleteMessage" @find-messages-by-media="handleFindMessagesByMedia"
                    @toggle-select="toggleSelectMessage" @toggle-star="handleToggleStar"
                    @toggle-media-star="(mediaId, msgId) => handleToggleMediaStar(mediaId, msgId)" @edit="openEditDialog"
                    @add-tag="handleQuickAddTag" />
                </div>
              </template>
            </div>

            <!-- Empty State -->
            <div v-if="messages.length === 0 && !loading" class="flex flex-col items-center justify-center py-20">
              <div class="w-14 h-14 mb-4 rounded-2xl bg-[var(--bg-secondary)] border border-[var(--border-color)] flex items-center justify-center">
                <svg class="w-7 h-7 text-[var(--text-muted)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 class="text-sm font-medium text-[var(--text-primary)]">暂无消息</h3>
              <p class="mt-1 text-xs text-[var(--text-muted)]">还没有任何消息内容</p>
            </div>

            <!-- Loading indicator (bottom, for loading newer) -->
            <div v-if="loadingForward" class="text-center py-4">
              <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
            </div>
          </div>

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
      </div>

      <!-- Right Tag Media Panel (可切换显示/隐藏) -->
      <TagMediaPanel v-if="showMediaPanel" :tag-id="selectedTagId" :tag-name="selectedTagName ?? undefined"
        @preview="handlePanelPreview" @jump="handlePanelJump" />

      <MessageComposeDialog :visible="dialogVisible" :mode="dialogMode" :message-id="dialogMessageId"
        :initial-text="dialogInitialText" :initial-date="dialogInitialDate" :initial-media="dialogInitialMedia"
        :initial-tags="dialogInitialTags"
        :all-tags="tags" :tag-id="selectedTagId ?? null" :collection-id="selectedCollectionId ?? undefined"
        :issue-id="selectedIssueId ?? undefined" @close="dialogVisible = false"
        @created="onDialogCreated" @updated="onDialogUpdated" @media-changed="onMediaChanged" @tag-created="fetchTags" />

      <MediaPreview :is-open="previewOpen" :items="previewItems" :start-index="previewStartIndex"
        :starred="previewMessageStarred" :message-id="previewMessageId" :all-tags="tags"
        :prev-peek-items="previewPrevPeekItems" :next-peek-items="previewNextPeekItems"
        @close="closePreview" @navigate-prev="navigateToPrevMessage"
        @navigate-next="navigateToNextMessage" @toggle-star="handlePreviewToggleStar" @media-deleted="handleMediaDeleted"
        @media-rotated="handleMediaRotated" @media-tags-changed="handleMediaTagsChanged" />

      <!-- Message 详情面板(右侧滑入) -->
      <MessageDetailPanel v-if="detailMessageId !== null" :message-id="detailMessageId" :all-tags="tags"
        :preview-open="previewOpen"
        @close="detailMessageId = null" @edit="(id) => { detailMessageId = null; openEditDialog(id) }"
        @media-click="(items, index) => handlePanelPreview({ items, index })"
        @toggle-star="handleToggleStar" @tags-changed="handleDetailTagsChanged" />

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Calendar } from 'v-calendar'
import 'v-calendar/style.css'
import { type Collection, type Issue, type MessageDetail, type MessageMediaItem, type TagWithCount } from '../types'
import MessageCard from '../components/MessageCard.vue'
import MessageGridCard from '../components/MessageGridCard.vue'
import MediaPreview from '../components/MediaPreview.vue'
import SearchInput from '../components/SearchInput.vue'
import MessageComposeDialog from '../components/MessageComposeDialog.vue'
import FilterSidebar from '../components/FilterSidebar.vue'
import IssuePinnedBanner from '../components/IssuePinnedBanner.vue'
import TagMediaPanel from '../components/TagMediaPanel.vue'
import MessageDetailPanel from '../components/MessageDetailPanel.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { toggleMediaStar } from '../utils/media'
import { formatDateLabel } from '../utils/date'
import { useTheme } from '../composables/useTheme'
import { useMessageLayout } from '../composables/useMessageLayout'


defineOptions({ name: 'Message' })

const route = useRoute()
const pendingRestore = ref<{ messageId: number; scrollOffset: number } | null>(null)

const toast = useToast()
const { confirm } = useConfirm()
const { theme } = useTheme()
const isDark = computed(() => theme.value === 'dark')
const { layout: messageLayout, toggleLayout, initLayout } = useMessageLayout()

// toggle 循环 grid → mosaic → card，title 提示下一个目标布局
const layoutToggleTitle = computed(() => {
  switch (messageLayout.value) {
    case 'grid': return '切换到拼图布局'
    case 'mosaic': return '切换到卡片网格'
    default: return '切换到网格布局'
  }
})

// --- Calendar date jump ---
const calendarOpen = ref(false)
const calendarPopover = ref<HTMLElement | null>(null)
const calendarDatesCache = new Map<string, Set<string>>() // "YYYY-MM" -> Set of "YYYY-MM-DD"
let calendarAttributesUpdating = false

const calendarAttributes = ref<Array<{ key: string; dot: { color: string }; dates: Date[] }>>([])

const toggleCalendar = () => {
  calendarOpen.value = !calendarOpen.value
}

const loadCalendarMonth = async (year: number, month: number) => {
  const key = `${year}-${String(month).padStart(2, '0')}`
  if (calendarDatesCache.has(key)) {
    return
  }
  try {
    const data = await api.get<{ dates: Array<{ date: string; count: number }> }>('/messages/dates', {
      year,
      month,
      tag_id: selectedTagId.value ?? undefined,
      collection_id: selectedCollectionId.value ?? undefined,
      issue_id: selectedIssueId.value ?? undefined,
      query_text: searchQuery.value || undefined,
    })
    const dateSet = new Set(data.dates.map(d => d.date))
    calendarDatesCache.set(key, dateSet)
    updateCalendarAttributes()
  } catch {
    // silent fail
  }
}

const updateCalendarAttributes = () => {
  if (calendarAttributesUpdating) return
  calendarAttributesUpdating = true
  const dotDates: Date[] = []
  for (const [, dateSet] of calendarDatesCache) {
    for (const dateStr of dateSet) {
      dotDates.push(new Date(dateStr + 'T12:00:00'))
    }
  }
  calendarAttributes.value = dotDates.length > 0
    ? [{ key: 'messages', dot: { color: 'indigo' }, dates: dotDates }]
    : []
  queueMicrotask(() => { calendarAttributesUpdating = false })
}

const onCalendarPageChange = (pages: Array<{ year: number; month: number }>) => {
  for (const page of pages) {
    loadCalendarMonth(page.year, page.month)
  }
}

const onCalendarDayClick = (day: { id: string; date: Date }) => {
  // day.id is "YYYY-MM-DD"
  const monthKey = day.id.substring(0, 7)
  const dateSet = calendarDatesCache.get(monthKey)
  if (!dateSet || !dateSet.has(day.id)) return // disabled date

  calendarOpen.value = false
  jumpToDate(day.id)
}

const jumpToDate = async (dateStr: string) => {
  // Use end-of-day as cursor to get messages from this date (desc order)
  const cursor = `${dateStr}T23:59:59.999999`
  loading.value = true
  try {
    const data = await api.get<{ items: MessageDetail[]; next_cursor: string | null; has_more: boolean }>(
      '/messages/with-detail',
      {
        limit: pageSize,
        cursor,
        query_text: searchQuery.value || undefined,
        media_id: activeMediaFilter.value ?? undefined,
        starred: starredFilter.value || undefined,
        tag_id: selectedTagId.value ?? undefined,
        collection_id: selectedCollectionId.value ?? undefined,
        issue_id: selectedIssueId.value ?? undefined,
      },
    )

    hasMoreData.value = data.has_more
    nextCursor.value = data.next_cursor
    messages.value = data.items.reverse()

    // Enable forward scrolling from the last message's time
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1]
      forwardCursor.value = lastMsg.created_at
      hasMoreForward.value = true
      isViewingHistory.value = true
    }

    await nextTick()
    // Scroll to bottom where the target date's messages are
    scrollToBottom('auto')
  } catch {
    toast.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

// Close calendar on outside click
const onDocumentClick = (e: MouseEvent) => {
  if (calendarOpen.value && calendarPopover.value && !calendarPopover.value.contains(e.target as Node)) {
    // Check if click was on the toggle button
    const btn = calendarPopover.value.parentElement?.querySelector('button')
    if (btn && btn.contains(e.target as Node)) return
    calendarOpen.value = false
  }
}

const tags = ref<TagWithCount[]>([])
const selectedTagId = ref<number | null>(null)

const collections = ref<Collection[]>([])
const noCollectionCount = ref(0)
const selectedCollectionId = ref<number | null>(null)

const issues = ref<Issue[]>([])
const noIssueCount = ref(0)
const selectedIssueId = ref<number | null>(null)

interface FilterScrollCache {
  messageId: number
  scrollOffset: number
  nextCursor: string | null
  cachedMessages: MessageDetail[]
  hasMoreData: boolean
  forwardCursor: string | null
  hasMoreForward: boolean
}

const scrollPositionCache = new Map<string, FilterScrollCache>()

const getFilterKey = (): string => {
  if (selectedTagId.value !== null) return `tag:${selectedTagId.value}`
  if (selectedCollectionId.value !== null) return `collection:${selectedCollectionId.value}`
  if (selectedIssueId.value !== null) return `issue:${selectedIssueId.value}`
  return 'all'
}

const getFirstVisibleMessageId = (): { messageId: number; scrollOffset: number } | null => {
  const container = scrollContainer.value
  if (!container) return null
  const containerRect = container.getBoundingClientRect()
  const elements = container.querySelectorAll<HTMLElement>('[data-message-id]')
  for (const el of elements) {
    const rect = el.getBoundingClientRect()
    if (rect.bottom > containerRect.top) {
      return { messageId: parseInt(el.dataset.messageId!), scrollOffset: rect.top - containerRect.top }
    }
  }
  return null
}

const saveScrollPosition = () => {
  const visible = getFirstVisibleMessageId()
  if (!visible) return
  const key = getFilterKey()
  scrollPositionCache.set(key, {
    messageId: visible.messageId,
    scrollOffset: visible.scrollOffset,
    nextCursor: nextCursor.value,
    cachedMessages: [...messages.value],
    hasMoreData: hasMoreData.value,
    forwardCursor: forwardCursor.value,
    hasMoreForward: hasMoreForward.value,
  })
}

const restoreFromCache = (key: string): boolean => {
  const cached = scrollPositionCache.get(key)
  if (!cached) return false
  messages.value = [...cached.cachedMessages]
  nextCursor.value = cached.nextCursor
  hasMoreData.value = cached.hasMoreData
  forwardCursor.value = cached.forwardCursor
  hasMoreForward.value = cached.hasMoreForward
  isViewingHistory.value = false
  nextTick(() => {
    const container = scrollContainer.value
    if (!container) return
    const el = container.querySelector<HTMLElement>(`[data-message-id="${cached.messageId}"]`)
    if (el) {
      const containerRect = container.getBoundingClientRect()
      const elRect = el.getBoundingClientRect()
      container.scrollTo({ top: container.scrollTop + (elRect.top - containerRect.top) - cached.scrollOffset, behavior: 'auto' })
    }
  })
  return true
}

const SCROLL_POS_KEY = 'msg_scroll_pos'

const saveScrollPositionToStorage = () => {
  const visible = getFirstVisibleMessageId()
  if (!visible || messages.value.length === 0) return
  const msg = messages.value.find(m => m.id === visible.messageId)
  if (!msg) return
  localStorage.setItem(SCROLL_POS_KEY, JSON.stringify({
    messageId: msg.id,
    createdAt: msg.created_at,
    scrollOffset: visible.scrollOffset,
  }))
}

let scrollSaveTimer: ReturnType<typeof setTimeout> | null = null
const debouncedSaveToStorage = () => {
  if (scrollSaveTimer) clearTimeout(scrollSaveTimer)
  scrollSaveTimer = setTimeout(saveScrollPositionToStorage, 500)
}

const fetchTags = async () => {
  try {
    tags.value = await api.get<TagWithCount[]>('/tags')
  } catch {
    // Tags are non-critical; silent fail
  }
}

const fetchCollections = async () => {
  try {
    const data = await api.get<{ items: Collection[]; no_collection_count: number }>('/collections')
    collections.value = data.items
    noCollectionCount.value = data.no_collection_count
  } catch {
    // silent fail
  }
}

const fetchIssues = async () => {
  try {
    const list = await api.get<Issue[]>('/issues/list', { status: 'doing' })
    issues.value = list
    // no_issue_count: messages without issue_id — fetch via /messages list with issue_id=0 count is not free,
    // so we don't show count when 0. Keep at 0 unless user toggles to it.
    noIssueCount.value = 0
  } catch {
    // silent
  }
}

const selectedIssue = computed<Issue | null>(() => {
  if (selectedIssueId.value === null) return null
  return issues.value.find(i => i.id === selectedIssueId.value) ?? null
})

const selectedTagName = computed<string | null>(() => {
  if (selectedTagId.value === null) return null
  return tags.value.find(t => t.id === selectedTagId.value)?.name ?? null
})

const onIssueUpdated = (updated: Issue) => {
  const idx = issues.value.findIndex(i => i.id === updated.id)
  if (idx !== -1) issues.value[idx] = updated
}

const promptCreateIssue = async () => {
  const title = window.prompt('新建 issue 标题：')
  if (!title || !title.trim()) return
  try {
    const issue = await api.post<Issue>('/issues', { title: title.trim() })
    issues.value.unshift(issue)
    selectIssue(issue.id)
    toast.success('已创建 issue')
  } catch {
    toast.error('创建 issue 失败')
  }
}

const resetFilters = () => {
  searchQuery.value = ''
  starredFilter.value = false
  activeMediaFilter.value = null
}

const selectTag = (tagId: number | null) => {
  saveScrollPosition()
  selectedTagId.value = tagId
  selectedCollectionId.value = null
  selectedIssueId.value = null
  resetFilters()
  if (!restoreFromCache(getFilterKey())) {
    resetAndFetch()
  }
}

const selectCollection = (collectionId: number | null) => {
  saveScrollPosition()
  selectedCollectionId.value = collectionId
  selectedTagId.value = null
  selectedIssueId.value = null
  resetFilters()
  if (!restoreFromCache(getFilterKey())) {
    resetAndFetch()
  }
}

const selectIssue = (issueId: number | null) => {
  saveScrollPosition()
  selectedIssueId.value = issueId
  selectedTagId.value = null
  selectedCollectionId.value = null
  resetFilters()
  if (!restoreFromCache(getFilterKey())) {
    resetAndFetch()
  }
}

const messages = ref<MessageDetail[]>([])
const loading = ref(false)
const searchQuery = ref('')

const pageSize = 20
const hasMoreData = ref(true)
const nextCursor = ref<string | null>(null)
const activeMediaFilter = ref<number | null>(null)
const starredFilter = ref(false)

// 右侧媒体网格默认隐藏,持久化到 localStorage
const showMediaPanel = ref(localStorage.getItem('message_show_media_panel') === '1')
function toggleMediaPanel() {
  showMediaPanel.value = !showMediaPanel.value
  localStorage.setItem('message_show_media_panel', showMediaPanel.value ? '1' : '0')
}

const scrollContainer = ref<HTMLElement | null>(null)

const previewOpen = ref(false)
const previewItems = ref<MessageMediaItem[]>([])
const previewStartIndex = ref(0)
const previewMessageId = ref<number | undefined>(undefined)
const currentMessageIndex = ref(-1)

// 右侧 tag media panel 点击「跳转到消息」后临时高亮该 message
const highlightMessageId = ref<number | null>(null)
let highlightTimer: ReturnType<typeof setTimeout> | null = null

const previewMessageStarred = computed(() => {
  if (currentMessageIndex.value < 0) return false
  return messages.value[currentMessageIndex.value]?.starred ?? false
})

// 邻居 message 的 media items 用于 preview 缩略图条边缘的"窥视"
const PEEK_COUNT = 5
const previewPrevPeekItems = computed<MessageMediaItem[]>(() => {
  if (currentMessageIndex.value <= 0) return []
  for (let i = currentMessageIndex.value - 1; i >= 0; i--) {
    const items = messages.value[i]?.media_items
    if (items?.length) {
      // 上一个 message 的 items 顺序保持原序；末尾 PEEK_COUNT 项与当前 message 首项最相邻
      return items.slice(-PEEK_COUNT)
    }
  }
  return []
})
const previewNextPeekItems = computed<MessageMediaItem[]>(() => {
  if (currentMessageIndex.value < 0 || currentMessageIndex.value >= messages.value.length - 1) return []
  for (let i = currentMessageIndex.value + 1; i < messages.value.length; i++) {
    const items = messages.value[i]?.media_items
    if (items?.length) {
      return items.slice(0, PEEK_COUNT)
    }
  }
  return []
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
      collection_id: selectedCollectionId.value ?? undefined,
      issue_id: selectedIssueId.value ?? undefined,
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
const dialogInitialMedia = ref<MessageMediaItem[]>([])
const dialogInitialTags = ref<{ id: number; name: string }[]>([])

const openCreateDialog = () => {
  dialogMode.value = 'create'
  dialogMessageId.value = undefined
  dialogInitialText.value = ''
  dialogInitialDate.value = ''
  dialogInitialMedia.value = []
  dialogInitialTags.value = []
  dialogVisible.value = true
}

const openEditDialog = (messageId: number) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (!msg) return

  dialogMode.value = 'edit'
  dialogMessageId.value = messageId
  dialogInitialText.value = msg.text || ''
  dialogInitialMedia.value = msg.media_items || []
  dialogInitialTags.value = msg.tags ? msg.tags.map(t => ({ id: t.id, name: t.name })) : []

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
  fetchTags()
}

const onDialogUpdated = async (messageId: number, text: string, date: string, tagIds: number[]) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (!msg) return

  try {
    const updateData: Record<string, unknown> = { text, tag_ids: tagIds }
    if (date) updateData.created_at = date

    const updated = await api.patch<MessageDetail>(`/messages/${messageId}`, updateData)
    msg.text = updated.text
    msg.created_at = updated.created_at
    msg.updated_at = updated.updated_at
    if (updated.tags) msg.tags = updated.tags
    toast.success('消息已更新')
    fetchTags()
  } catch {
    toast.error('更新消息失败')
  }
}

const onMediaChanged = async (messageId: number) => {
  try {
    const updated = await api.get<MessageDetail>(`/messages/${messageId}`)
    const msg = messages.value.find(m => m.id === messageId)
    if (msg) {
      msg.media_items = updated.media_items
      msg.media_count = updated.media_count
    }
  } catch {
    // silent
  }
}

// --- Message 详情面板 ---
const detailMessageId = ref<number | null>(null)

const openDetailPanel = (messageId: number) => {
  detailMessageId.value = messageId
}

// 详情面板里改了标签,同步回 feed 列表里对应的卡片
const handleDetailTagsChanged = (
  messageId: number,
  tagList: { id: number; name: string; category?: string | null }[],
) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (msg) msg.tags = tagList as MessageDetail['tags']
  fetchTags()
}

const handleQuickAddTag = async (messageId: number, tagId: number) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (!msg) return

  if (msg.tags?.some(t => t.id === tagId)) {
    toast.error('该 Tag 已存在')
    return
  }

  const tagIds = [...(msg.tags || []).map(t => t.id), tagId]

  try {
    const updated = await api.patch<MessageDetail>(`/messages/${messageId}`, { tag_ids: tagIds })
    msg.updated_at = updated.updated_at
    if (updated.tags) msg.tags = updated.tags
    toast.success('标签已添加')
    fetchTags()
  } catch {
    toast.error('添加标签失败')
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
  calendarDatesCache.clear()
  calendarAttributes.value = []
  fetchMessages()
}

const fetchMessages = async (isLoadingMore = false) => {
  if (loading.value) return
  if (isLoadingMore && !hasMoreData.value) return

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
        collection_id: selectedCollectionId.value ?? undefined,
        issue_id: selectedIssueId.value ?? undefined,
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
  previewMessageId.value = messageId
  previewOpen.value = true
}
const closePreview = () => {
  previewOpen.value = false
  previewItems.value = []
  currentMessageIndex.value = -1
}

const handlePreviewToggleStar = async (mediaId: number) => {
  const currentItem = previewItems.value.find(item => item.id === mediaId)
  if (!currentItem) return

  await toggleMediaStar(currentItem)

  if (currentMessageIndex.value >= 0) {
    const msg = messages.value[currentMessageIndex.value]
    const mediaItem = msg?.media_items?.find(item => item.id === mediaId)
    if (mediaItem) {
      mediaItem.starred = currentItem.starred
    }
  }
}

const handleMediaDeleted = (mediaId: number) => {
  // 更新消息中的媒体项（API调用已在MediaPreview中完成）
  if (currentMessageIndex.value >= 0) {
    const msg = messages.value[currentMessageIndex.value]
    if (msg?.media_items) {
      const itemIndex = msg.media_items.findIndex(item => item.id === mediaId)
      if (itemIndex !== -1) {
        msg.media_items.splice(itemIndex, 1)
        if (typeof msg.media_count === 'number') msg.media_count = msg.media_items.length
      }
    }
  }
}

const handleMediaRotated = (mediaId: number) => {
  const t = Date.now()
  const bust = (item: any) => {
    item.thumb_url = (item.thumb_url || '').split('?')[0] + `?t=${t}`
    if (item.local_file_path) {
      item.local_file_path = item.local_file_path.split('?')[0] + `?t=${t}`
    }
  }
  for (const msg of messages.value) {
    if (!msg.media_items) continue
    for (const item of msg.media_items) {
      if (item.id === mediaId) bust(item)
    }
  }
  for (const item of previewItems.value) {
    if (item.id === mediaId) bust(item)
  }
}

const handleMediaTagsChanged = (mediaId: number, newTags: { id: number; name: string; category?: string | null }[]) => {
  for (const msg of messages.value) {
    if (!msg.media_items) continue
    for (const item of msg.media_items) {
      if (item.id === mediaId) {
        item.tags = newTags
      }
    }
  }
  fetchTags()
}

const handleToggleMediaStar = async (mediaId: number, messageId?: number) => {
  const msg = messageId
    ? messages.value.find(m => m.id === messageId)
    : messages.value.find(m => m.media_items?.some(item => item.id === mediaId))
  const mediaItem = msg?.media_items?.find(item => item.id === mediaId)
  if (mediaItem) {
    await toggleMediaStar(mediaItem)
  }
}

const navigateToPrevMessage = () => {
  for (let i = currentMessageIndex.value - 1; i >= 0; i--) {
    const msg = messages.value[i]
    if (msg?.media_items?.length) {
      currentMessageIndex.value = i
      previewItems.value = msg.media_items
      previewStartIndex.value = msg.media_items.length - 1
      previewMessageId.value = msg.id
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
      previewMessageId.value = msg.id
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
    fetchTags()
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
    fetchTags()
  } catch (error) {
    toast.error('合并消息失败')
  }
}

// --- Find by media ---

const handleFindMessagesByMedia = (mediaId: number) => {
  resetAndFetch({ mediaId })
}

// --- Right tag media panel handlers ---

const handlePanelPreview = (payload: { items: MessageMediaItem[]; index: number }) => {
  currentMessageIndex.value = -1  // panel 场景不做跨 message 导航
  previewItems.value = payload.items
  previewStartIndex.value = payload.index
  previewMessageId.value = undefined
  previewOpen.value = true
}

const highlightMessage = (messageId: number) => {
  highlightMessageId.value = messageId
  if (highlightTimer) clearTimeout(highlightTimer)
  highlightTimer = setTimeout(() => { highlightMessageId.value = null }, 1600)
}

const scrollToLoadedMessage = (messageId: number): boolean => {
  const container = scrollContainer.value
  const el = container?.querySelector<HTMLElement>(`[data-message-id="${messageId}"]`)
  if (!el || !container) return false
  el.scrollIntoView({ behavior: 'smooth', block: 'center' })
  highlightMessage(messageId)
  return true
}

const handlePanelJump = async (messageId: number) => {
  // 已在当前列表里：直接滚动 + 高亮
  if (scrollToLoadedMessage(messageId)) return

  // 否则按该 message 的时间加载一个窗口再定位（复用 jumpToDate 的加载范式）
  loading.value = true
  try {
    const target = await api.get<MessageDetail>(`/messages/${messageId}`)
    const cursor = target.created_at
    const data = await api.get<{ items: MessageDetail[]; next_cursor: string | null; has_more: boolean }>(
      '/messages/with-detail',
      {
        limit: pageSize,
        cursor,
        inclusive: true,  // 让 target 自己也被包含在返回窗口里
        query_text: searchQuery.value || undefined,
        media_id: activeMediaFilter.value ?? undefined,
        starred: starredFilter.value || undefined,
        tag_id: selectedTagId.value ?? undefined,
        collection_id: selectedCollectionId.value ?? undefined,
        issue_id: selectedIssueId.value ?? undefined,
      },
    )

    hasMoreData.value = data.has_more
    nextCursor.value = data.next_cursor
    messages.value = data.items.reverse()

    // 从最后一条时间开启向前（更新）分页
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1]
      forwardCursor.value = lastMsg.created_at
      hasMoreForward.value = true
      isViewingHistory.value = true
    }

    await nextTick()
    if (!scrollToLoadedMessage(messageId)) {
      // 极少数：target 命中当前过滤器为空（例如 tag/actor 过滤把它挡掉）
      toast.info('该消息不在当前筛选范围内')
    }
  } catch {
    toast.error('加载消息失败')
  } finally {
    loading.value = false
  }
}


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

// --- Infinite scroll: prefetch when N-th item from edge enters viewport ---
// 与 Android Paging 3 的 prefetchDistance 对齐：还剩 N 项就预取下一页，
// 不受滚动速度和卡片高度差异影响。
const PREFETCH_DISTANCE = 10

let topObserver: IntersectionObserver | null = null
let bottomObserver: IntersectionObserver | null = null

const setupObservers = () => {
  teardownObservers()
  const root = scrollContainer.value
  if (!root) return

  topObserver = new IntersectionObserver(
    (entries) => {
      const container = scrollContainer.value
      if (entries[0]?.isIntersecting && !loading.value && hasMoreData.value && container && container.scrollTop > 0) {
        fetchMessages(true)
      }
    },
    { root }
  )

  bottomObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && !loadingForward.value && hasMoreForward.value) {
        fetchForwardMessages()
      }
    },
    { root }
  )

  rebindPrefetchTargets()
}

const rebindPrefetchTargets = () => {
  const container = scrollContainer.value
  if (!container || !topObserver || !bottomObserver) return
  const els = container.querySelectorAll<HTMLElement>('[data-message-id]')
  if (els.length === 0) return
  const topIdx = Math.min(PREFETCH_DISTANCE, els.length - 1)
  const bottomIdx = Math.max(0, els.length - 1 - PREFETCH_DISTANCE)
  topObserver.disconnect()
  bottomObserver.disconnect()
  topObserver.observe(els[topIdx])
  bottomObserver.observe(els[bottomIdx])
}

const teardownObservers = () => {
  topObserver?.disconnect()
  topObserver = null
  bottomObserver?.disconnect()
  bottomObserver = null
}

const tryRestoreScroll = () => {
  if (!pendingRestore.value) return
  const container = scrollContainer.value
  if (!container) return
  const { messageId, scrollOffset } = pendingRestore.value
  const attempt = (n: number) => {
    if (!pendingRestore.value) return
    const el = container.querySelector<HTMLElement>(`[data-message-id="${messageId}"]`)
    // 容器不可见（v-show: none）时 scrollHeight 为 0，等可见再试
    if (!el || container.scrollHeight === 0 || container.clientHeight === 0) {
      if (n < 60) requestAnimationFrame(() => attempt(n + 1))
      return
    }
    const containerRect = container.getBoundingClientRect()
    const elRect = el.getBoundingClientRect()
    const targetTop = container.scrollTop + (elRect.top - containerRect.top) - scrollOffset
    container.scrollTo({ top: targetTop, behavior: 'auto' })
    pendingRestore.value = null
  }
  attempt(0)
}

watch(() => route.path, (path) => {
  if (path === '/messages' && pendingRestore.value) {
    nextTick(tryRestoreScroll)
  }
}, { immediate: true })

onMounted(() => {
  initLayout()
  fetchTags()
  fetchCollections()
  fetchIssues()
  const saved = localStorage.getItem(SCROLL_POS_KEY)
  if (saved) {
    try {
      const { messageId, createdAt, scrollOffset } = JSON.parse(saved) as { messageId: number; createdAt: string; scrollOffset?: number }
      loading.value = true
      Promise.all([
        api.get<{ items: MessageDetail[]; next_cursor: string | null; has_more: boolean }>(
          '/messages/with-detail',
          {
            limit: pageSize,
            cursor: createdAt,
            inclusive: true,
            query_text: searchQuery.value || undefined,
            media_id: activeMediaFilter.value ?? undefined,
            starred: starredFilter.value || undefined,
            tag_id: selectedTagId.value ?? undefined,
            collection_id: selectedCollectionId.value ?? undefined,
            issue_id: selectedIssueId.value ?? undefined,
          },
        ),
        api.get<{ items: MessageDetail[]; next_cursor: string | null; has_more: boolean }>(
          '/messages/with-detail',
          {
            limit: pageSize,
            cursor: createdAt,
            query_text: searchQuery.value || undefined,
            media_id: activeMediaFilter.value ?? undefined,
            starred: starredFilter.value || undefined,
            tag_id: selectedTagId.value ?? undefined,
            collection_id: selectedCollectionId.value ?? undefined,
            issue_id: selectedIssueId.value ?? undefined,
            direction: 'forward',
          },
        ),
      ]).then(([backwardData, forwardData]) => {
        const allItems = [...backwardData.items.reverse(), ...forwardData.items]
        const seen = new Set<number>()
        messages.value = allItems.filter(m => {
          if (seen.has(m.id)) return false
          seen.add(m.id)
          return true
        })
        nextCursor.value = backwardData.next_cursor
        hasMoreData.value = backwardData.has_more
        if (forwardData.items.length > 0) {
          const lastMsg = forwardData.items[forwardData.items.length - 1]
          forwardCursor.value = lastMsg.created_at
          hasMoreForward.value = forwardData.has_more
          isViewingHistory.value = forwardData.has_more
        } else {
          forwardCursor.value = null
          hasMoreForward.value = false
          isViewingHistory.value = false
        }
        nextTick(() => {
          pendingRestore.value = { messageId, scrollOffset: scrollOffset ?? 0 }
          tryRestoreScroll()
          setupObservers()
        })
      }).catch(() => {
        fetchMessages()
        setupObservers()
      }).finally(() => {
        loading.value = false
      })
    } catch {
      fetchMessages()
      setupObservers()
    }
  } else {
    fetchMessages()
    setupObservers()
  }
  scrollContainer.value?.addEventListener('scroll', onScrollForDate, { passive: true })
  scrollContainer.value?.addEventListener('scroll', debouncedSaveToStorage, { passive: true })
  document.addEventListener('click', onDocumentClick, true)
})

onUnmounted(() => {
  teardownObservers()
  scrollContainer.value?.removeEventListener('scroll', onScrollForDate)
  scrollContainer.value?.removeEventListener('scroll', debouncedSaveToStorage)
  document.removeEventListener('click', onDocumentClick, true)
  if (scrollRaf) cancelAnimationFrame(scrollRaf)
  if (scrollSaveTimer) clearTimeout(scrollSaveTimer)
  if (highlightTimer) clearTimeout(highlightTimer)
})

// Update floating date after messages change
watch(messages, () => nextTick(() => {
  updateVisibleDate()
  rebindPrefetchTargets()
}), { flush: 'post' })
</script>

