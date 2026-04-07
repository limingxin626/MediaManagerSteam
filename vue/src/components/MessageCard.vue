<template>
  <div
    class="group bg-[var(--bg-card)] rounded-xl shadow-sm border border-[var(--border-color)] overflow-hidden hover:shadow-lg transition-all duration-200 cursor-pointer"
    :class="{ 'ring-2 ring-indigo-500 border-indigo-500': props.selected }" @click="handleClick">
    <div class="px-4">
      <!-- Actor Info -->
      <div class="flex items-center justify-between gap-3">
        <!-- Selection checkbox -->
        <div v-if="props.selectable" @click.stop="emit('toggle-select', props.message.id)"
          class="shrink-0 w-6 h-6 rounded-md border-2 flex items-center justify-center transition-colors" :class="props.selected
            ? 'bg-indigo-600 border-indigo-600 text-white'
            : 'border-gray-600 hover:border-indigo-400'">
          <svg v-if="props.selected" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div v-if="message.actor_name"
          class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold">
          {{ actorInitial }}
        </div>
        <div class="flex-1 min-w-0">
          <h3 v-if="message.actor_name" class="text-sm font-semibold text-white truncate">
            {{ message.actor_name }}
          </h3>
        </div>
      </div>

      <!-- Unified Media Preview -->
      <div v-if="mediaPreviewItems.length > 0" class="relative rounded-xl overflow-hidden mb-2">
        <div class="grid gap-0.5" :class="mediaGridClass">
          <div v-for="(item, index) in mediaPreviewItems" :key="item.id"
            class="relative overflow-hidden bg-gray-100 dark:bg-gray-800 cursor-pointer" :class="mediaItemClass(index)"
            @click.stop="handleMediaClick(index)">
            <img :src="resolveUrl(item.thumb_url)" :alt="`Media ${index + 1}`"
              class="w-full h-full object-cover transition-transform duration-200 hover:scale-105" />

            <!-- Video overlay -->
            <div v-if="isVideo(item.mime_type)"
              class="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div
                class="w-10 h-10 bg-black/50 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/20">
                <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
            </div>

            <!-- Duration badge -->
            <div v-if="item.duration_ms"
              class="absolute bottom-1.5 left-1.5 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded backdrop-blur-sm font-medium">
              {{ formatDuration(item.duration_ms) }}
            </div>

            <!-- Star and Menu Buttons -->
            <div class="absolute top-1.5 right-1.5 flex gap-1.5">
              <!-- Star Button -->
              <button @click.stop="handleMediaToggleStar(item)"
                class="w-6 h-6 rounded-full flex items-center justify-center backdrop-blur-sm transition-colors" :class="item.starred
                  ? 'text-yellow-400 bg-yellow-900/30 hover:bg-yellow-900/50'
                  : 'text-white/70 hover:text-yellow-400 hover:bg-white/10'
                  " :title="item.starred ? '取消收藏' : '收藏'">
                <svg class="w-3.5 h-3.5" :fill="item.starred ? 'currentColor' : 'none'" stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>

              <!-- Menu Button -->
              <button @click.stop="toggleMenu(index)"
                class="w-6 h-6 bg-black/50 hover:bg-black/80 text-white rounded-full flex items-center justify-center backdrop-blur-sm transition-colors opacity-0 hover:opacity-100"
                :class="{ 'opacity-100!': activeMenuIndex === index }">
                <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path
                    d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
                </svg>
              </button>

              <div v-if="activeMenuIndex === index"
                class="absolute top-8 right-0 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-white/10 py-1 min-w-[140px] z-10">
                <button @click.stop="findMessagesByMedia(item.id)"
                  class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                  查找所有message
                </button>
              </div>
            </div>

            <!-- "More" overlay on last item -->
            <div v-if="index === mediaPreviewItems.length - 1 && remainingCount > 0"
              class="absolute inset-0 bg-black/50 flex items-center justify-center pointer-events-none">
              <span class="text-white text-2xl font-semibold">+{{ remainingCount }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Message Text -->
      <div v-if="message.text" class="mb-2 prose dark:prose-invert prose-sm max-w-none text-gray-700 dark:text-gray-300">
        <div class="line-clamp-40" v-html="renderedText"></div>
      </div>

      <!-- Tags & Media count row -->
      <div v-if="messageTags.length > 0 || message.media_count > 0" class="flex items-center gap-2 mt-2 flex-wrap">
        <span v-for="tag in messageTags" :key="tag.id"
          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-indigo-900/30 text-indigo-300">
          {{ tag.name }}
        </span>
        <span v-if="message.media_count > 0" class="inline-flex items-center gap-1 text-xs text-gray-500 ml-auto">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          {{ message.media_count }}
        </span>
      </div>

      <!-- Timestamp Info & Actions -->
      <div class="flex items-center justify-between mt-3 pt-2 border-t border-[var(--border-color)] text-xs text-gray-500">
          <div class="flex items-center gap-3">
            <span class="flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              创建: {{ formatDate(message.created_at) }}
            </span>
            <span v-if="message.updated_at && message.updated_at !== message.created_at" class="flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              修改: {{ formatDate(message.updated_at) }}
            </span>
          </div>
          <div class="flex items-center gap-1">
            <button @click.stop="handleToggleStar" class="p-1 rounded transition-colors" :class="props.message.starred
              ? 'text-yellow-400 hover:text-yellow-500'
              : 'text-gray-500 hover:text-yellow-400'"
              :title="props.message.starred ? '取消收藏' : '收藏'">
              <svg class="w-3.5 h-3.5" :fill="props.message.starred ? 'currentColor' : 'none'" stroke="currentColor"
                viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            </button>
            <button @click.stop="handleEdit"
              class="p-1 text-gray-500 hover:text-blue-500 rounded transition-colors"
              title="编辑消息">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button @click.stop="handleDelete"
              class="p-1 text-gray-500 hover:text-red-500 rounded transition-colors"
              title="删除消息">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
    </div>
  </div>

  <!-- Edit Dialog -->
  <div v-if="editDialogVisible" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50">
    <div class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-white/10 shadow-xl w-full max-w-3xl p-6 h-[90vh] flex flex-col">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">编辑消息</h3>
      <div class="mb-4">
        <label class="block text-sm font-medium text-gray-600 dark:text-gray-300 mb-1">创建日期</label>
        <input
          v-model="editDate"
          type="datetime-local"
          class="w-full px-4 py-2 border border-gray-300 dark:border-white/10 rounded-lg bg-gray-50 dark:bg-white/10 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        />
      </div>
      <textarea
        ref="editTextareaRef"
        v-model="editText"
        placeholder="输入消息内容..."
        class="flex-1 w-full px-4 py-2 border border-gray-300 dark:border-white/10 rounded-lg bg-gray-50 dark:bg-white/10 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        @input="tag.onInput"
        @keydown="tag.onKeydown"
        @blur="tag.hide"
      />
      <!-- Tag Suggestions -->
      <div
        v-if="tag.tagSuggestionVisible.value && tag.tagSuggestions.value.length > 0"
        class="fixed bg-white dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg shadow-xl max-h-48 overflow-y-auto z-[100]"
        :style="{ top: tag.tagSuggestionPosition.value.top + 'px', left: tag.tagSuggestionPosition.value.left + 'px', transform: 'translateY(-100%)' }"
      >
        <div
          v-for="(t, index) in tag.tagSuggestions.value"
          :key="t.id"
          @click="tag.selectTag(t)"
          class="px-3 py-2 cursor-pointer text-sm"
          :class="index === tag.tagSuggestionIndex.value ? 'bg-indigo-600 text-white' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'"
        >
          #{{ t.name }}
        </div>
      </div>
      <div class="flex justify-end gap-3 mt-4">
        <button @click="cancelEdit" class="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-white rounded-lg transition-colors">
          取消
        </button>
        <button @click="saveEdit" class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors">
          保存
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { marked } from 'marked'
import type { Message, MessageMediaItem, TagItem } from '../types'
import { isVideo, formatDuration, resolveUrl } from '../utils/media'
import { useTagAutocomplete } from '../composables/useTagAutocomplete'
import { formatRelativeTime } from '../utils/date'

interface Props {
  message: Message
  mediaItems?: MessageMediaItem[]
  tags?: TagItem[]
  selectable?: boolean
  selected?: boolean
  allTags?: TagItem[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [id: number]
  'media-click': [mediaIndex: number]
  delete: [id: number]
  'find-messages-by-media': [mediaId: number]
  'toggle-select': [id: number]
  'toggle-star': [id: number]
  'toggle-media-star': [mediaId: number]
  'edit': [id: number, text: string, date: string]
}>()

const maxPreviewItems = 9
const activeMenuIndex = ref<number | null>(null)

// 编辑相关状态
const editDialogVisible = ref(false)
const editText = ref('')
const editDate = ref('')
const editTextareaRef = ref<HTMLTextAreaElement | null>(null)

const tag = useTagAutocomplete(editTextareaRef, editText, computed(() => props.allTags || []))

const handleEdit = () => {
  editText.value = props.message.text || ''
  const dateStr = props.message.created_at
  if (dateStr) {
    const date = new Date(dateStr)
    // 确保日期是有效的
    if (!isNaN(date.getTime())) {
      // 格式化为 YYYY-MM-DDTHH:MM
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      editDate.value = `${year}-${month}-${day}T${hours}:${minutes}`
    }
  }
  editDialogVisible.value = true
}

const saveEdit = () => {
  emit('edit', props.message.id, editText.value, editDate.value)
  editDialogVisible.value = false
}

const cancelEdit = () => {
  editDialogVisible.value = false
  editText.value = ''
  editDate.value = ''
  tag.hide()
}

const actorInitial = computed(() => {
  if (!props.message.actor_name) return '?'
  return props.message.actor_name.charAt(0).toUpperCase()
})

const messageTags = computed(() => {
  return props.tags || []
})

const mediaPreviewItems = computed(() => {
  if (!props.mediaItems) return []
  return props.mediaItems.slice(0, maxPreviewItems)
})

const remainingCount = computed(() => {
  if (!props.mediaItems) return 0
  return Math.max(0, props.mediaItems.length - maxPreviewItems)
})

const renderedText = computed(() => {
  if (!props.message.text) return ''
  // 配置 marked 保留原始换行行为
  marked.setOptions({
    breaks: true
  })
  return marked.parse(props.message.text) as string
})

// Telegram-style grid: 1→full, 2→2col, 3→left big + right 2 small, 4→2x2, 5+→3col
const mediaGridClass = computed(() => {
  const count = mediaPreviewItems.value.length
  if (count === 1) return 'grid-cols-1'
  if (count === 2) return 'grid-cols-2'
  if (count === 3) return 'grid-cols-3 grid-rows-2'
  if (count === 4) return 'grid-cols-2'
  return 'grid-cols-3'
})

const mediaItemClass = (index: number) => {
  const count = mediaPreviewItems.value.length
  if (count === 1) return 'aspect-video'
  if (count === 3 && index === 0) return 'col-span-2 row-span-2'
  if (count === 3) return 'aspect-square'
  return 'aspect-square'
}

const formatDate = formatRelativeTime

const handleClick = () => {
  emit('click', props.message.id)
}

const handleMediaClick = (index: number) => {
  emit('media-click', index)
}

const handleDelete = () => {
  emit('delete', props.message.id)
}

const handleToggleStar = () => {
  emit('toggle-star', props.message.id)
}

const toggleMenu = (index: number) => {
  if (activeMenuIndex.value === index) {
    activeMenuIndex.value = null
  } else {
    activeMenuIndex.value = index
  }
}

const findMessagesByMedia = (mediaId: number) => {
  activeMenuIndex.value = null
  emit('find-messages-by-media', mediaId)
}

const handleMediaToggleStar = (mediaItem: MessageMediaItem) => {
  emit('toggle-media-star', mediaItem.id)
}
</script>
