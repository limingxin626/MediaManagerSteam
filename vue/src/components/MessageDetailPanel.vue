<template>
  <div class="message-detail fixed inset-0 z-[95] bg-[var(--bg-primary)] flex flex-col animate-fade-in">
    <!-- 顶部工具栏 -->
    <header class="message-detail__header shrink-0 flex items-center justify-between gap-4 px-4 sm:px-6 py-3 border-b border-[var(--border-color)] bg-[var(--bg-card)]/90 backdrop-blur-xl">
      <div class="flex items-center gap-3 min-w-0">
        <button @click="close" title="关闭 (Esc)"
          class="shrink-0 flex items-center gap-2 px-3 py-2 -ml-2 rounded-[var(--radius-md)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-white/5 transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span class="text-sm font-medium">返回消息</span>
        </button>
        <div v-if="message?.collection_name" class="flex items-center gap-2.5 min-w-0 pl-3 border-l border-[var(--border-color)]">
          <div class="w-8 h-8 rounded-full bg-[var(--color-accent-soft)] text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)] flex items-center justify-center font-semibold shrink-0">
            {{ collectionInitial }}
          </div>
          <span class="text-sm font-semibold text-[var(--text-primary)] truncate">{{ message.collection_name }}</span>
        </div>
      </div>
      <div class="flex items-center gap-3">
        <span v-if="message?.starred" class="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-amber-400/10 text-amber-400 text-xs font-medium">
          <span>★</span> 已收藏
        </span>
        <p class="shrink-0 text-xs text-[var(--text-muted)]">{{ message ? formatDate(message.created_at) : '' }}</p>
      </div>
    </header>

    <!-- Loading -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
    </div>

    <template v-else-if="message">
      <!-- Body: 左媒体 + 右信息,居中容器 -->
      <div class="flex-1 overflow-y-auto">
        <main class="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 xl:px-10 py-6 lg:py-10 flex flex-col lg:flex-row gap-6 lg:gap-8">
          <!-- 左:正文 + 媒体 -->
          <article class="flex-1 min-w-0 space-y-5">
            <div v-if="message.text"
              class="message-detail__content markdown-body text-[15px] text-[var(--text-primary)] leading-7 rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] px-5 sm:px-7 py-5 sm:py-6 shadow-[var(--shadow-sm)]"
              v-html="renderMarkdown(message.text)"></div>

            <!-- 单媒体:大图铺满,保留原始比例 -->
            <div v-if="mediaItems.length === 1"
              class="message-detail__media relative overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[#181818] cursor-pointer group flex items-center justify-center shadow-[var(--shadow-md)]"
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
                class="grid gap-2.5 p-2.5 rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] shadow-[var(--shadow-sm)]"
              :class="mediaItems.length === 2 ? 'grid-cols-2' : 'grid-cols-2 sm:grid-cols-3'">
              <div v-for="(media, index) in mediaItems" :key="media.id"
                class="relative overflow-hidden rounded-[var(--radius-md)] bg-[#181818] cursor-pointer group aspect-square"
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
          </article>

          <!-- 右:标签 + 基本信息 -->
          <aside class="w-full lg:w-72 xl:w-80 shrink-0 lg:sticky lg:top-6 lg:self-start rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] shadow-[var(--shadow-sm)] overflow-hidden">
            <!-- 物理文件夹 -->
            <div v-if="message.folders?.length"
              class="p-5 border-b border-[var(--border-color)]">
              <h4 class="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wider mb-3">文件夹</h4>
              <div class="space-y-3">
                <div v-for="folder in message.folders" :key="folder.id" class="min-w-0">
                  <div class="flex items-center justify-between gap-2 mb-1">
                    <span class="text-xs font-medium text-[var(--text-secondary)] truncate">{{ folder.repo_id }}</span>
                    <span v-if="folder.role === 'PRIMARY'"
                      class="shrink-0 text-[10px] text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]">主目录</span>
                  </div>
                  <p class="text-sm text-[var(--text-primary)] break-all leading-5" :title="folder.rel_path">
                    {{ folder.rel_path }}
                  </p>
                </div>
              </div>
            </div>

            <!-- 标签 -->
            <div class="p-5 border-b border-[var(--border-color)]">
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
            <div class="p-5 border-b border-[var(--border-color)]">
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
            <div class="flex items-center gap-2 p-4 bg-[var(--bg-secondary)]/45">
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
          </aside>
        </main>
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

.message-detail {
  background:
    radial-gradient(circle at 30% -15%, color-mix(in srgb, var(--color-primary-500) 9%, transparent), transparent 34rem),
    var(--bg-primary);
}

.message-detail__header {
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.025);
}

.message-detail__content {
  min-height: 5rem;
}

.message-detail__media::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.035);
  pointer-events: none;
}

@media (max-width: 1023px) {
  .message-detail__media img {
    max-height: 60vh;
  }
}
</style>
