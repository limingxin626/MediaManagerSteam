<template>
  <div class="fixed inset-0 z-[95] bg-[var(--bg-primary)] flex flex-col animate-fade-in">
    <!-- 顶部工具栏 -->
    <div class="shrink-0 flex items-center justify-between gap-3 px-5 py-3 border-b border-[var(--border-color)]">
      <div class="flex items-center gap-3 min-w-0">
        <button @click="close" title="关闭 (Esc)"
          class="shrink-0 flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span class="text-sm">返回</span>
        </button>
        <div v-if="message?.collection_name" class="flex items-center gap-2 min-w-0 pl-2 border-l border-[var(--border-color)]">
          <div class="w-8 h-8 rounded-full bg-[var(--color-accent-soft)] text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)] flex items-center justify-center font-semibold shrink-0">
            {{ collectionInitial }}
          </div>
          <span class="text-sm font-semibold text-[var(--text-primary)] truncate">{{ message.collection_name }}</span>
        </div>
      </div>
      <p class="shrink-0 text-xs text-[var(--text-muted)]">{{ message ? formatDate(message.created_at) : '' }}</p>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
    </div>

    <template v-else-if="message">
      <!-- Body: 左媒体 + 右信息,居中容器 -->
      <div class="flex-1 overflow-y-auto">
        <div class="max-w-6xl mx-auto px-6 py-8 flex flex-col lg:flex-row gap-10">
          <!-- 左:正文 + 媒体 -->
          <div class="flex-1 min-w-0 space-y-6">
            <div v-if="message.text"
              class="markdown-body text-[15px] text-[var(--text-primary)] leading-relaxed"
              v-html="renderMarkdown(message.text)"></div>

            <!-- 单媒体:大图铺满,保留原始比例 -->
            <div v-if="mediaItems.length === 1"
              class="relative overflow-hidden rounded-[var(--radius-lg)] bg-[var(--bg-secondary)] cursor-pointer group flex items-center justify-center"
              @click="emit('media-click', mediaItems, 0)">
              <img :src="resolveThumb(mediaItems[0])" alt="Media"
                class="max-w-full max-h-[70vh] object-contain transition-transform duration-200 group-hover:scale-[1.01]" />
              <div v-if="isVideo(mediaItems[0].mime_type)"
                class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div class="w-14 h-14 bg-black/50 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/25">
                  <svg class="w-7 h-7 text-white ml-1" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                </div>
              </div>
              <div v-if="mediaItems[0].duration_ms"
                class="absolute bottom-2 left-2 bg-black/70 text-white text-xs px-2 py-0.5 rounded backdrop-blur-sm font-medium">
                {{ formatDuration(mediaItems[0].duration_ms) }}
              </div>
            </div>

            <!-- 多媒体:自适应网格 -->
            <div v-else-if="mediaItems.length > 1"
              class="grid gap-3"
              :class="mediaItems.length === 2 ? 'grid-cols-2' : 'grid-cols-2 sm:grid-cols-3'">
              <div v-for="(media, index) in mediaItems" :key="media.id"
                class="relative overflow-hidden rounded-[var(--radius-md)] bg-[var(--bg-secondary)] cursor-pointer group aspect-square"
                @click="emit('media-click', mediaItems, index)">
                <img :src="resolveThumb(media)" :alt="`Media ${index + 1}`"
                  class="w-full h-full object-cover transition-transform duration-200 group-hover:scale-105" />
                <div v-if="isVideo(media.mime_type)"
                  class="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div class="w-10 h-10 bg-black/50 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/20">
                    <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                  </div>
                </div>
                <div v-if="media.duration_ms"
                  class="absolute bottom-1 left-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded backdrop-blur-sm font-medium">
                  {{ formatDuration(media.duration_ms) }}
                </div>
              </div>
            </div>
          </div>

          <!-- 右:标签 + 基本信息 -->
          <div class="w-full lg:w-72 shrink-0 lg:sticky lg:top-0 lg:self-start space-y-6">
            <!-- 标签 -->
            <div class="rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-secondary)]/40 p-4">
              <div class="flex items-center justify-between mb-3">
                <h4 class="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider">标签</h4>
                <TagPickerPopover v-if="allTags.length" :all-tags="allTags" :message-tags="message.tags || []"
                  @select="addTag" />
              </div>
              <div class="flex flex-wrap gap-2">
                <span v-for="tag in (message.tags || [])" :key="tag.id" @click="removeTag(tag.id)"
                  class="tag-chip hover:!bg-red-500/20 hover:!text-red-500 hover:line-through cursor-pointer transition-colors"
                  title="点击移除">
                  #{{ tag.name }}
                </span>
                <p v-if="!message.tags?.length" class="text-sm text-[var(--text-muted)]">暂无标签</p>
              </div>
            </div>

            <!-- 基本信息 -->
            <div class="rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-secondary)]/40 p-4">
              <h4 class="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">基本信息</h4>
              <div class="space-y-2.5 text-sm">
                <div class="flex justify-between gap-3">
                  <span class="text-[var(--text-muted)] shrink-0">ID</span>
                  <span class="text-[var(--text-primary)]">{{ message.id }}</span>
                </div>
                <div class="flex justify-between gap-3">
                  <span class="text-[var(--text-muted)] shrink-0">媒体数量</span>
                  <span class="text-[var(--text-primary)]">{{ mediaItems.length }}</span>
                </div>
                <div class="flex justify-between gap-3">
                  <span class="text-[var(--text-muted)] shrink-0">收藏</span>
                  <span class="text-[var(--text-primary)]">{{ message.starred ? '是' : '否' }}</span>
                </div>
                <div v-if="message.issue_title" class="flex justify-between gap-3">
                  <span class="text-[var(--text-muted)] shrink-0">Issue</span>
                  <span class="text-[var(--text-primary)] truncate">{{ message.issue_title }}</span>
                </div>
                <div class="flex justify-between gap-3">
                  <span class="text-[var(--text-muted)] shrink-0">创建时间</span>
                  <span class="text-[var(--text-primary)] text-right">{{ formatDate(message.created_at) }}</span>
                </div>
              </div>
            </div>

            <!-- 操作 -->
            <div class="flex items-center gap-2">
              <button @click="emit('edit', message.id)"
                class="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-700)] text-white rounded-[var(--radius-md)] transition-colors text-sm font-medium">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
                编辑
              </button>
              <button @click="emit('toggle-star', message.id)"
                class="px-4 py-2 rounded-[var(--radius-md)] border border-[var(--border-color)] transition-colors text-sm flex items-center gap-2"
                :class="message.starred ? 'text-amber-400 bg-amber-400/10' : 'text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'">
                <svg class="w-4 h-4" :fill="message.starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
                收藏
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-else class="flex-1 flex items-center justify-center text-[var(--text-muted)]">
      消息不存在
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import type { MessageDetail, MessageMediaItem, TagWithCount } from '../types'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { renderMarkdown } from '../utils/markdown'
import { isVideo, formatDuration, resolveThumb } from '../utils/media'
import TagPickerPopover from './TagPickerPopover.vue'

const props = defineProps<{
  messageId: number
  allTags: TagWithCount[]
  previewOpen?: boolean
}>()

const emit = defineEmits<{
  close: []
  'media-click': [items: MessageMediaItem[], index: number]
  edit: [id: number]
  'toggle-star': [id: number]
  'tags-changed': [messageId: number, tags: { id: number; name: string; category?: string | null }[]]
}>()

const toast = useToast()
const message = ref<MessageDetail | null>(null)
const isLoading = ref(true)

const mediaItems = computed<MessageMediaItem[]>(() => message.value?.media_items ?? [])

const collectionInitial = computed(() => {
  const name = message.value?.collection_name || ''
  return name ? name.charAt(0).toUpperCase() : ''
})

const formatDate = (iso: string): string => {
  try {
    return new Date(iso).toLocaleString('zh-CN')
  } catch {
    return iso
  }
}

const load = async () => {
  isLoading.value = true
  try {
    message.value = await api.get<MessageDetail>(`/messages/${props.messageId}`)
  } catch {
    message.value = null
    toast.error('加载消息失败')
  } finally {
    isLoading.value = false
  }
}

const persistTags = async (tags: { id: number; name: string; category?: string | null }[]) => {
  if (!message.value) return
  try {
    await api.patch(`/messages/${message.value.id}`, { tag_ids: tags.map(t => t.id) })
    message.value.tags = tags
    emit('tags-changed', message.value.id, tags)
  } catch {
    toast.error('更新标签失败')
  }
}

const addTag = (tag: TagWithCount) => {
  if (!message.value) return
  const existing = message.value.tags || []
  if (existing.some(t => t.id === tag.id)) return
  persistTags([...existing, { id: tag.id, name: tag.name, category: tag.category }])
}

const removeTag = (tagId: number) => {
  if (!message.value) return
  persistTags((message.value.tags || []).filter(t => t.id !== tagId))
}

const close = () => emit('close')

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Escape') {
    // preview 打开时,Esc 交给 MediaPreview 处理,不要连详情一起关掉
    if (props.previewOpen) return
    e.preventDefault()
    close()
  }
}

watch(() => props.messageId, load)

onMounted(() => {
  load()
  window.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeydown)
})
</script>

<style scoped>
@keyframes fade-in {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fade-in {
  animation: fade-in 0.18s ease-out;
}
</style>
