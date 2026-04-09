<template>
  <div class="h-screen flex transition-colors">
    <!-- Left Actor Column -->
    <div class="flex flex-col w-48 shrink-0 border-r border-[var(--border-color)] overflow-y-auto">
      <div class="px-3 pt-4 pb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider shrink-0">演员列表</div>
      <div class="flex flex-col gap-0.5 px-2 pb-4">
        <button
          v-for="actor in actorsData"
          :key="actor.id"
          @click="selectActor(actor.id)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left"
          :class="selectedActorId === actor.id
            ? 'bg-indigo-600/30 text-indigo-600 dark:text-indigo-300'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'"
        >
          <span class="truncate">{{ actor.name }}</span>
          <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ actor.message_count }}</span>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col min-w-0">
      <!-- Search Header -->
      <div class="shrink-0 border-b border-[var(--border-color)] shadow-sm">
        <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div class="flex gap-4 items-center max-w-2xl mx-auto">
            <h2 class="text-2xl font-bold text-gray-900 dark:text-white">演员消息</h2>
            <!-- Search -->
            <SearchInput v-model="filterName" placeholder="搜索演员..." @search="resetAndFetch" />
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
            <div v-for="i in 3" :key="i" class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-4 animate-pulse">
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
            <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-indigo-500"></div>
          </div>

          <!-- Messages Feed -->
          <div v-if="messages.length > 0" class="flex flex-col gap-4 max-w-2xl mx-auto">
            <template
              v-for="(message, idx) in messages"
              :key="message.id"
            >
              <!-- Date separator -->
              <div
                v-if="idx === 0 || getDateStr(message.created_at) !== getDateStr(messages[idx - 1]?.created_at ?? '')"
                class="flex items-center gap-3 py-2"
              >
                <div class="flex-1 h-px bg-[var(--divider)]"></div>
                <span class="text-xs text-gray-400 whitespace-nowrap">{{ formatDateLabel(message.created_at) }}</span>
                <div class="flex-1 h-px bg-[var(--divider)]"></div>
              </div>
              <div :data-message-date="message.created_at.substring(0, 10)">
                <MessageCard
                  :message="message"
                  :media-items="message.media_items"
                  :tags="message.tags"
                  @media-click="(index) => handleMediaClick(message.id, index)"
                  @delete="handleDeleteMessage"
                  @toggle-star="handleToggleStar"
                  @toggle-media-star="handleToggleMediaStar"
                />
              </div>
            </template>
          </div>

          <!-- No more data -->
          <div v-if="!loading && !hasMoreMessages && messages.length > 0" class="text-center py-8">
            <p class="text-sm text-gray-400">已经到底了</p>
          </div>

          <!-- Empty State -->
          <div v-if="messages.length === 0 && !loading" class="text-center py-12">
            <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">暂无消息</h3>
            <p class="mt-1 text-sm text-gray-400">选择一个演员查看消息</p>
          </div>
        </div>

        <!-- Scroll sentinel for loading newer messages -->
        <div class="h-1"></div>
      </div>

      <!-- Input Area at Bottom -->
      <MessageCompose
        v-if="selectedActorId != null"
        :actor-id="selectedActorId"
        @sent="onMessageSent"
      />
    </div>

    <!-- Right Actor Detail Column -->
    <aside class="w-72 shrink-0 border-l border-[var(--border-color)] overflow-y-auto">
      <div v-if="selectedActor" class="p-6">
        <!-- Actor Avatar -->
        <div class="flex flex-col items-center mb-6">
          <div class="w-32 h-32 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700 mb-4">
            <img
              :src="resolveUrl(selectedActor.avatar_url)"
              :alt="selectedActor.name"
              class="w-full h-full object-cover"
            />
          </div>
          <h3 class="text-xl font-bold text-gray-900 dark:text-white mb-1">{{ selectedActor.name }}</h3>
          <p class="text-sm text-gray-400">{{ selectedActor.message_count }} 条消息</p>
        </div>

        <!-- Actor Description -->
        <div v-if="selectedActor.description" class="mb-6">
          <h4 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">简介</h4>
          <p class="text-sm text-gray-600 dark:text-gray-300">{{ selectedActor.description }}</p>
        </div>

        <!-- Actor Info -->
        <div class="space-y-4">
          <div>
            <h4 class="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2">信息</h4>
            <div class="space-y-2">
              <div class="flex justify-between text-sm">
                <span class="text-gray-400">ID</span>
                <span class="text-gray-600 dark:text-gray-300">{{ selectedActor.id }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-400">创建时间</span>
                <span class="text-gray-600 dark:text-gray-300">{{ formatDateTime(selectedActor.created_at) }}</span>
              </div>
              <div class="flex justify-between text-sm">
                <span class="text-gray-400">更新时间</span>
                <span class="text-gray-600 dark:text-gray-300">{{ formatDateTime(selectedActor.updated_at) }}</span>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="pt-4 border-t border-[var(--border-color)]">
            <button
              @click="editActor(selectedActor)"
              class="w-full px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors mb-2"
            >
              编辑
            </button>
            <button
              @click="deleteActor(selectedActor.id)"
              class="w-full px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              删除
            </button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="flex flex-col items-center justify-center h-full text-gray-400">
        <svg class="w-12 h-12 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p class="text-sm">选择一个演员查看详情</p>
      </div>
    </aside>

    <!-- Add/Edit Modal -->
    <ActorEditModal
      :is-open="showModal"
      :title="editMode ? '编辑数据' : '添加新数据'"
      :form-data="formData"
      @close="closeModal"
      @save="saveActor"
    />

    <!-- Media Preview -->
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import type { Actor, MessageDetail, MessageMediaItem } from '../types'
import ActorEditModal from '../components/ActorEditModal.vue'
import MessageCard from '../components/MessageCard.vue'
import MediaPreview from '../components/MediaPreview.vue'
import SearchInput from '../components/SearchInput.vue'
import MessageCompose from '../components/MessageCompose.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { resolveUrl } from '../utils/media'
import { formatDateLabel, formatDateTime } from '../utils/date'

defineOptions({ name: 'Actor' })

const toast = useToast()

const pageSize = 20
const actorsData = ref<Actor[]>([])
const loading = ref(false)

const filterName = ref('')

const selectedActorId = ref<number | null>(null)
const selectedActor = computed(() => actorsData.value.find(a => a.id === selectedActorId.value) ?? null)

const messages = ref<MessageDetail[]>([])
const hasMoreMessages = ref(true)
const nextCursor = ref<string | null>(null)

const showModal = ref(false)
const editMode = ref(false)
const currentEditId = ref<number | null>(null)
const formData = ref({ name: '', description: '' })

const scrollContainer = ref<HTMLElement | null>(null)
const topSentinel = ref<HTMLElement | null>(null)

const previewOpen = ref(false)
const previewItems = ref<MessageMediaItem[]>([])
const previewStartIndex = ref(0)
const currentMessageIndex = ref(-1)

const previewMessageStarred = computed(() => {
  if (currentMessageIndex.value < 0) return false
  return messages.value[currentMessageIndex.value]?.starred ?? false
})

let observer: IntersectionObserver | null = null

// --- Fetch Actors ---

const fetchActors = async (reset = false) => {
  if (loading.value) return

  if (reset) {
    actorsData.value = []
  }

  loading.value = true
  try {
    const data = await api.get<Actor[]>('/actors', {
      name: filterName.value || undefined,
    })

    actorsData.value = data

    if (actorsData.value.length > 0 && !selectedActorId.value) {
      selectActor(actorsData.value[0]!.id)
    }
  } catch (error) {
    toast.error('获取演员数据失败')
  } finally {
    loading.value = false
  }
}

const resetAndFetch = () => {
  fetchActors(true)
}

// --- Select Actor ---

const selectActor = (id: number) => {
  selectedActorId.value = id
  fetchMessages(true)
}

// --- Fetch Messages ---

const fetchMessages = async (reset = false) => {
  if (!selectedActorId.value) return

  if (reset) {
    messages.value = []
    hasMoreMessages.value = true
    nextCursor.value = null
  }

  loading.value = true
  try {
    const data = await api.get<{
      items: MessageDetail[]
      next_cursor: string | null
      has_more: boolean
    }>('/messages/with-detail', {
      actor_id: selectedActorId.value,
      cursor: nextCursor.value,
      limit: pageSize,
    })

    if (reset) {
      // desc order returned, reverse for chat layout (newest at bottom)
      messages.value = data.items.reverse()
      // Scroll to bottom on initial load
      await nextTick()
      scrollToBottom('auto')
    } else {
      // Preserve scroll position when loading older messages
      const container = scrollContainer.value
      const previousScrollY = container?.scrollTop ?? 0
      const previousHeight = container?.scrollHeight ?? 0

      // Append older messages at the beginning
      messages.value = [...data.items.reverse(), ...messages.value]

      // Restore scroll position
      await nextTick()
      if (container) {
        const scrollDelta = container.scrollHeight - previousHeight
        if (scrollDelta > 0) {
          container.scrollTo({ top: previousScrollY + scrollDelta, behavior: 'auto' })
        }
      }
    }
    hasMoreMessages.value = data.has_more
    nextCursor.value = data.next_cursor
  } catch (error) {
    toast.error('获取消息数据失败')
  } finally {
    loading.value = false
  }
}

const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
  const el = scrollContainer.value
  if (el) el.scrollTo({ top: el.scrollHeight, behavior })
}

const onMessageSent = async (message: MessageDetail) => {
  messages.value.push(message)
  await nextTick()
  scrollToBottom()
}

// --- CRUD ---

const editActor = (item: Actor) => {
  editMode.value = true
  currentEditId.value = item.id
  formData.value = { name: item.name, description: item.description || '' }
  showModal.value = true
}

const saveActor = async (data: typeof formData.value) => {
  try {
    if (editMode.value && currentEditId.value) {
      await api.put(`/actors/${currentEditId.value}`, data)
    } else {
      await api.post('/actors', data)
    }
    await fetchActors(true)
    closeModal()
    toast.success('保存成功')
  } catch (error) {
    toast.error('保存演员数据失败')
  }
}

const deleteActor = async (id: number) => {
  if (!confirm('确定要删除这条记录吗?')) return
  try {
    await api.del(`/actors/${id}`)
    actorsData.value = actorsData.value.filter((a: Actor) => a.id !== id)
    if (selectedActorId.value === id) {
      selectedActorId.value = null
      messages.value = []
    }
    toast.success('删除成功')
  } catch (error) {
    toast.error('删除演员数据失败')
  }
}

const closeModal = () => {
  showModal.value = false
  editMode.value = false
  currentEditId.value = null
}

// --- Message Handlers ---

const handleMediaClick = (messageId: number, index: number) => {
  const messageIndex = messages.value.findIndex(m => m.id === messageId)
  if (messageIndex >= 0) {
    currentMessageIndex.value = messageIndex
    previewItems.value = messages.value[messageIndex]!.media_items
    previewStartIndex.value = index
    previewOpen.value = true
  }
}

const handleDeleteMessage = async (messageId: number) => {
  if (!confirm('确定要删除这条消息吗?')) return
  try {
    await api.del(`/messages/${messageId}`)
    messages.value = messages.value.filter(m => m.id !== messageId)
    toast.success('删除成功')
  } catch (error) {
    toast.error('删除消息失败')
  }
}

const handleToggleStar = async (messageId: number) => {
  const message = messages.value.find(m => m.id === messageId)
  if (!message) return

  try {
    const newStarred = !message.starred
    await api.put(`/messages/${messageId}`, { starred: newStarred })
    message.starred = newStarred
  } catch (error) {
    toast.error('更新收藏状态失败')
  }
}

const handleToggleMediaStar = async (mediaId: number) => {
  for (const message of messages.value) {
    const media = message.media_items.find(m => m.id === mediaId)
    if (media) {
      try {
        const newStarred = !media.starred
        await api.put(`/media/${mediaId}`, { starred: newStarred })
        media.starred = newStarred
      } catch (error) {
        toast.error('更新收藏状态失败')
      }
      break
    }
  }
}

const navigateToPrevMessage = () => {
  if (currentMessageIndex.value > 0) {
    currentMessageIndex.value--
    const message = messages.value[currentMessageIndex.value]!
    previewItems.value = message.media_items
    previewStartIndex.value = 0
  }
}

const navigateToNextMessage = () => {
  if (currentMessageIndex.value < messages.value.length - 1) {
    currentMessageIndex.value++
    const message = messages.value[currentMessageIndex.value]!
    previewItems.value = message.media_items
    previewStartIndex.value = 0
  }
}

const handlePreviewToggleStar = async () => {
  if (currentMessageIndex.value >= 0) {
    await handleToggleStar(messages.value[currentMessageIndex.value]!.id)
  }
}

const closePreview = () => {
  previewOpen.value = false
  previewItems.value = []
  currentMessageIndex.value = -1
}

const getDateStr = (dateStr: string) => dateStr.substring(0, 10)

// --- Infinite scroll ---

onMounted(() => {
  fetchActors(true)
  const root = scrollContainer.value
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          if (entry.target === topSentinel.value && !loading.value && hasMoreMessages.value) {
            fetchMessages(false)
          }
        }
      }
    },
    { root, rootMargin: '200px' },
  )
  if (topSentinel.value) observer.observe(topSentinel.value)
})

onUnmounted(() => {
  observer?.disconnect()
})
</script>
