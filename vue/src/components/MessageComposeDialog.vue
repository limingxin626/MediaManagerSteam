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

      <!-- Textarea -->
      <textarea ref="textareaRef" v-model="text" placeholder="输入消息内容..."
        class="flex-1 w-full px-4 py-2 border border-gray-300 dark:border-white/10 rounded-lg bg-gray-50 dark:bg-white/10 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        @input="tag.onInput" @keydown="handleKeydown" @blur="tag.hide" />

      <!-- Tag Suggestions -->
      <div v-if="tag.tagSuggestionVisible.value && tag.tagSuggestions.value.length > 0"
        class="fixed bg-white dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg shadow-xl max-h-48 overflow-y-auto z-[100]"
        :style="{ top: tag.tagSuggestionPosition.value.top + 'px', left: tag.tagSuggestionPosition.value.left + 'px', transform: 'translateY(-100%)' }">
        <div v-for="(t, index) in tag.tagSuggestions.value" :key="t.id" @click="tag.selectTag(t)"
          class="px-3 py-2 cursor-pointer text-sm"
          :class="index === tag.tagSuggestionIndex.value ? 'bg-indigo-600 text-white' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
          #{{ t.name }}
        </div>
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
import { ref, computed, watch, nextTick } from 'vue'
import type { MessageDetail, TagItem } from '../types'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { useTagAutocomplete } from '../composables/useTagAutocomplete'

interface Props {
  visible: boolean
  mode: 'create' | 'edit'
  messageId?: number
  initialText?: string
  initialDate?: string
  allTags?: TagItem[]
  tagId?: number | null
  actorId?: number | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  created: [message: MessageDetail]
  updated: [messageId: number, text: string, date: string]
}>()

const toast = useToast()

const text = ref('')
const editDate = ref('')
const files = ref<string[]>([])
const textareaRef = ref<HTMLTextAreaElement | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const submitting = ref(false)

const tag = useTagAutocomplete(textareaRef, text, computed(() => props.allTags || []))

const canSubmit = computed(() => {
  if (submitting.value) return false
  if (props.mode === 'create') return text.value.trim().length > 0 || files.value.length > 0
  return text.value.trim().length > 0 || text.value === '' // edit mode: allow empty to clear text
})

// Reset state when dialog opens
watch(() => props.visible, async (visible) => {
  if (visible) {
    text.value = props.initialText || ''
    editDate.value = props.initialDate || ''
    files.value = []
    submitting.value = false
    await nextTick()
    textareaRef.value?.focus()
  } else {
    tag.hide()
  }
})

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
        tag_ids: props.tagId != null ? [props.tagId] : undefined,
      })
      emit('created', result)
      toast.success('消息已发送')
    } else {
      emit('updated', props.messageId!, text.value, editDate.value)
    }
    handleClose()
  } catch {
    toast.error(props.mode === 'create' ? '发送消息失败' : '更新消息失败')
  } finally {
    submitting.value = false
  }
}

// --- File handling (create mode) ---

const triggerFileInput = async () => {
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
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    const filePaths = Array.from(target.files).map(file =>
      (file as any).path || (file as any).webkitRelativePath || file.name
    )
    files.value = [...files.value, ...filePaths]
  }
  target.value = ''
}

const removeFile = (index: number) => {
  files.value.splice(index, 1)
}
</script>
