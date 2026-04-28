<template>
  <div v-if="visible" class="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50"
    @keydown.esc="handleEscape" @mousedown.self="handleClose">
    <div
      class="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-white/10 shadow-xl w-full max-w-3xl p-6 h-[90vh] flex flex-col">
      <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        {{ mode === 'create' ? '新消息' : '编辑消息' }}
      </h3>

      <!-- Date picker (edit mode only) -->
      <div v-if="mode === 'edit'" class="mb-4">
        <label class="block text-sm font-medium text-gray-600 dark:text-gray-300 mb-1">创建日期</label>
        <input v-model="editDate" type="datetime-local"
          class="w-full px-4 py-2 border border-gray-300 dark:border-white/10 rounded-lg bg-gray-50 dark:bg-white/10 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
      </div>

      <!-- Selected tags -->
      <div class="flex flex-wrap gap-1.5 mb-2 min-h-[1.75rem]">
        <span v-for="t in selectedTags" :key="t.id"
          class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
          #{{ t.name }}
          <button @click="removeTag(t.id)" class="hover:text-red-500" title="移除标签">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </span>
        <span v-if="selectedTags.length === 0" class="text-xs text-gray-400 dark:text-gray-500 self-center">输入 # 选择标签</span>
      </div>

      <!-- Textarea -->
      <textarea ref="textareaRef" v-model="text" placeholder="输入消息内容..."
        class="flex-1 w-full px-4 py-2 border border-gray-300 dark:border-white/10 rounded-lg bg-gray-50 dark:bg-white/10 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        @input="tag.onInput" @keydown="handleKeydown" @blur="tag.hide" />

      <!-- Tag Suggestions -->
      <div v-if="tag.tagSuggestionVisible.value && tag.tagSuggestions.value.length > 0"
        ref="tagSuggestionListEl"
        class="fixed bg-white dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg shadow-xl max-h-48 overflow-y-auto z-[100]"
        :style="{ top: tag.tagSuggestionPosition.value.top + 'px', left: tag.tagSuggestionPosition.value.left + 'px', transform: 'translateY(-100%)' }">
        <div v-for="(t, index) in tag.tagSuggestions.value" :key="t.id" @click="tag.selectTag(t)"
          class="px-3 py-2 cursor-pointer text-sm"
          :class="index === tag.tagSuggestionIndex.value ? 'bg-indigo-600 text-white' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
          #{{ t.name }}
        </div>
      </div>

      <!-- Media grid (edit mode) -->
      <div v-if="mode === 'edit'" class="mt-3">
        <div v-if="existingMedia.length > 0 || newFiles.length > 0" class="grid grid-cols-6 gap-2 mb-2">
          <!-- Existing media -->
          <div v-for="media in existingMedia" :key="'existing-' + media.id"
            class="relative aspect-square rounded-lg overflow-hidden group"
            draggable="true"
            @dragstart="onDragStart($event, media.id, 'existing')"
            @dragover.prevent="onDragOver($event)"
            @drop="onDrop($event, media.id, 'existing')">
            <img :src="resolveUrl(media.thumb_url)" class="w-full h-full object-cover" />
            <button @click="removeExistingMedia(media.id)"
              class="absolute top-1 right-1 p-0.5 bg-black/60 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div v-if="media.mime_type && media.mime_type.startsWith('video')"
              class="absolute bottom-1 left-1 bg-black/60 text-white text-xs px-1 rounded">
              视频
            </div>
          </div>
          <!-- New files (local preview) -->
          <div v-for="(file, index) in newFilePreviews" :key="'new-' + index"
            class="relative aspect-square rounded-lg overflow-hidden group border-2 border-dashed border-indigo-400/50">
            <img v-if="file.previewUrl" :src="file.previewUrl" class="w-full h-full object-cover" />
            <div v-else class="w-full h-full flex items-center justify-center bg-gray-100 dark:bg-white/10">
              <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
            </div>
            <button @click="removeNewFile(index)"
              class="absolute top-1 right-1 p-0.5 bg-black/60 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <button @click="triggerFileInput"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 4v16m8-8H4" />
          </svg>
          添加媒体
        </button>
        <input ref="fileInput" type="file" multiple accept="image/*,video/*" class="hidden" @change="handleFileSelect" />
      </div>

      <!-- File attachments (create mode only) -->
      <div v-if="mode === 'create'" class="mt-3">
        <div v-if="files.length > 0" class="flex flex-wrap gap-2 mb-2">
          <div v-for="(filePath, index) in files" :key="index"
            class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-white/10 rounded-md text-sm">
            <span class="text-gray-700 dark:text-gray-300 truncate max-w-xs">{{ filePath.split('\\').pop() || filePath
              }}</span>
            <button @click="removeFile(index)" class="text-gray-500 hover:text-red-500 transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <button @click="triggerFileInput"
          class="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
          添加附件
        </button>
        <input ref="fileInput" type="file" multiple class="hidden" @change="handleFileSelect" />
      </div>

      <!-- Footer buttons -->
      <div class="flex justify-end gap-3 mt-4">
        <button @click="handleClose"
          class="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-white rounded-lg transition-colors">
          取消
        </button>
        <button @click="handleSubmit" :disabled="!canSubmit"
          class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 text-white rounded-lg transition-colors">
          {{ mode === 'create' ? '发送' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import type { MessageDetail, MessageMediaItem, TagItem } from '../types'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { useTagAutocomplete } from '../composables/useTagAutocomplete'
import { resolveUrl } from '../utils/media'
import { API_BASE_URL } from '../utils/constants'

interface Props {
  visible: boolean
  mode: 'create' | 'edit'
  messageId?: number
  initialText?: string
  initialDate?: string
  initialMedia?: MessageMediaItem[]
  initialTags?: TagItem[]
  allTags?: TagItem[]
  tagId?: number | null
  actorId?: number | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  created: [message: MessageDetail]
  updated: [messageId: number, text: string, date: string, tagIds: number[]]
  mediaChanged: [messageId: number]
}>()

const toast = useToast()

const text = ref('')
const editDate = ref('')
const files = ref<string[]>([])
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const submitting = ref(false)

// Edit mode media state
const existingMedia = ref<MessageMediaItem[]>([])
const newFiles = ref<File[]>([])
const newFilePreviews = ref<{ file: File; previewUrl: string | null }[]>([])
const mediaChanged = ref(false)

// Drag state
let dragId: number | null = null
let dragType: 'existing' | 'new' = 'existing'

const selectedTags = ref<TagItem[]>([])

const addTag = (tag: TagItem) => {
  if (selectedTags.value.some(t => t.id === tag.id)) return
  selectedTags.value = [...selectedTags.value, tag]
}

const removeTag = (tagId: number) => {
  selectedTags.value = selectedTags.value.filter(t => t.id !== tagId)
}

const tag = useTagAutocomplete(textareaRef, text, computed(() => props.allTags || []), addTag)
const tagSuggestionListEl = ref<HTMLElement | null>(null)
watch(tagSuggestionListEl, (el) => { tag.suggestionListRef.value = el })

const canSubmit = computed(() => {
  if (submitting.value) return false
  if (props.mode === 'create') return text.value.trim().length > 0 || files.value.length > 0
  return true
})

watch(() => props.visible, async (visible) => {
  if (visible) {
    text.value = props.initialText || ''
    editDate.value = props.initialDate || ''
    files.value = []
    submitting.value = false
    existingMedia.value = props.initialMedia ? [...props.initialMedia] : []
    newFiles.value = []
    newFilePreviews.value = []
    mediaChanged.value = false
    if (props.mode === 'edit') {
      selectedTags.value = props.initialTags ? [...props.initialTags] : []
    } else {
      const preselect = props.tagId != null
        ? (props.allTags || []).find(t => t.id === props.tagId)
        : undefined
      selectedTags.value = preselect ? [preselect] : []
    }
    await nextTick()
    textareaRef.value?.focus()
  } else {
    tag.hide()
    cleanupPreviews()
  }
})

const cleanupPreviews = () => {
  for (const p of newFilePreviews.value) {
    if (p.previewUrl) URL.revokeObjectURL(p.previewUrl)
  }
  newFilePreviews.value = []
}

onUnmounted(cleanupPreviews)

const handleKeydown = (e: KeyboardEvent) => {
  if (tag.onKeydown(e)) return
}

const handleEscape = () => {
  if (tag.tagSuggestionVisible.value) {
    tag.hide()
    return
  }
  handleClose()
}

const handleClose = () => {
  tag.hide()
  emit('close')
}

const handleSubmit = async () => {
  if (!canSubmit.value) return
  submitting.value = true

  try {
    if (props.mode === 'create') {
      const result = await api.post<MessageDetail>('/messages', {
        text: text.value || null,
        files: files.value,
        actor_id: props.actorId ?? undefined,
        tag_ids: selectedTags.value.map(t => t.id),
      })
      emit('created', result)
      toast.success('消息已发送')
    } else {
      // Upload new files first
      if (newFiles.value.length > 0) {
        const uploadedPaths: string[] = []
        for (const file of newFiles.value) {
          const formData = new FormData()
          formData.append('file', file)
          const res = await fetch(`${API_BASE_URL}/files/upload-media`, {
            method: 'POST',
            body: formData,
          })
          if (!res.ok) {
            toast.error(`上传失败: ${file.name}`)
            continue
          }
          const data = await res.json()
          uploadedPaths.push(data.path)
        }
        if (uploadedPaths.length > 0) {
          await api.post<MessageDetail>(`/messages/${props.messageId}/media`, uploadedPaths)
          mediaChanged.value = true
        }
      }

      emit('updated', props.messageId!, text.value, editDate.value, selectedTags.value.map(t => t.id))
      if (mediaChanged.value) {
        emit('mediaChanged', props.messageId!)
      }
    }
    handleClose()
  } catch {
    toast.error(props.mode === 'create' ? '发送消息失败' : '更新消息失败')
  } finally {
    submitting.value = false
  }
}

// --- Existing media operations (edit mode) ---

const removeExistingMedia = async (mediaId: number) => {
  try {
    await api.del(`/messages/${props.messageId}/media/${mediaId}`)
    existingMedia.value = existingMedia.value.filter(m => m.id !== mediaId)
    mediaChanged.value = true
  } catch {
    toast.error('删除媒体失败')
  }
}

// --- Drag and drop for reordering ---

const onDragStart = (e: DragEvent, id: number, type: 'existing' | 'new') => {
  dragId = id
  dragType = type
  if (e.dataTransfer) e.dataTransfer.effectAllowed = 'move'
}

const onDragOver = (e: DragEvent) => {
  if (e.dataTransfer) e.dataTransfer.dropEffect = 'move'
}

const onDrop = async (e: DragEvent, targetId: number, _targetType: 'existing' | 'new') => {
  e.preventDefault()
  if (dragId === null || dragType !== 'existing' || dragId === targetId) return

  const items = [...existingMedia.value]
  const fromIdx = items.findIndex(m => m.id === dragId)
  const toIdx = items.findIndex(m => m.id === targetId)
  if (fromIdx < 0 || toIdx < 0) return

  const [moved] = items.splice(fromIdx, 1)
  items.splice(toIdx, 0, moved)
  existingMedia.value = items

  const mediaOrder = items.map(m => m.id)
  try {
    await api.patch(`/messages/${props.messageId}`, { media_order: mediaOrder })
    mediaChanged.value = true
  } catch {
    toast.error('排序失败')
  }

  dragId = null
}

// --- File handling ---

const triggerFileInput = async () => {
  if (props.mode === 'create') {
    const isElectron = navigator.userAgent.indexOf('Electron') > -1
    if (isElectron && window.electronAPI) {
      try {
        const result = await window.electronAPI.openFileDialog({
          properties: ['openFile', 'multiSelections']
        })
        if (!result.canceled && result.filePaths) {
          files.value = [...files.value, ...result.filePaths]
        }
      } catch {
        fileInput.value?.click()
      }
    } else {
      fileInput.value?.click()
    }
  } else {
    fileInput.value?.click()
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files) return

  if (props.mode === 'create') {
    const filePaths = Array.from(target.files).map(file =>
      (file as any).path || (file as any).webkitRelativePath || file.name
    )
    files.value = [...files.value, ...filePaths]
  } else {
    for (const file of Array.from(target.files)) {
      newFiles.value.push(file)
      const isImage = file.type.startsWith('image/')
      newFilePreviews.value.push({
        file,
        previewUrl: isImage ? URL.createObjectURL(file) : null,
      })
    }
  }
  target.value = ''
}

const removeFile = (index: number) => {
  files.value.splice(index, 1)
}

const removeNewFile = (index: number) => {
  const preview = newFilePreviews.value[index]
  if (preview?.previewUrl) URL.revokeObjectURL(preview.previewUrl)
  newFiles.value.splice(index, 1)
  newFilePreviews.value.splice(index, 1)
}
</script>
