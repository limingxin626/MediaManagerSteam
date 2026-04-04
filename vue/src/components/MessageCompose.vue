<template>
  <div class="shrink-0 border-t border-white/10 shadow-lg">
    <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
      <div class="flex gap-2 items-center max-w-2xl mx-auto">
        <!-- Attachment Button -->
        <button
          @click="triggerFileInput"
          class="flex-shrink-0 p-2 text-gray-400 hover:text-indigo-400 hover:bg-white/10 rounded-lg transition-colors"
          title="添加附件"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
        </button>

        <!-- File Input (Hidden) -->
        <input
          ref="fileInput"
          type="file"
          multiple
          class="hidden"
          @change="handleFileSelect"
        />

        <!-- Text Input -->
        <div class="flex-1 relative">
          <textarea
            ref="textareaRef"
            v-model="text"
            placeholder="输入消息..."
            rows="1"
            class="w-full px-4 py-2 border border-white/10 rounded-lg bg-white/10 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none max-h-32 overflow-y-auto"
            @keydown.enter="handleEnterKey"
            @input="autoResize"
          />
        </div>

        <!-- Send Button -->
        <button
          @click="send"
          :disabled="!text.trim() && files.length === 0"
          class="flex-shrink-0 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
          title="发送"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>

      <!-- Selected Files Preview -->
      <div v-if="files.length > 0" class="mt-2 max-w-2xl mx-auto">
        <div class="flex flex-wrap gap-2">
          <div
            v-for="(filePath, index) in files"
            :key="index"
            class="inline-flex items-center gap-1 px-2 py-1 bg-white/10 rounded-md text-sm"
          >
            <span class="text-gray-300 truncate max-w-xs">{{ filePath.split('\\').pop() || filePath }}</span>
            <button
              @click="removeFile(index)"
              class="text-gray-500 hover:text-red-500 transition-colors"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { MessageDetail } from '../types'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'

const props = defineProps<{
  actorId?: number | null
  tagId?: number | null
}>()

const emit = defineEmits<{
  sent: [message: MessageDetail]
}>()

const toast = useToast()

const text = ref('')
const files = ref<string[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

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
    } catch (err) {
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

const autoResize = () => {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = el.scrollHeight + 'px'
}

const handleEnterKey = (event: KeyboardEvent) => {
  if (event.shiftKey) return
  event.preventDefault()
  send()
}

const send = async () => {
  if (!text.value.trim() && files.value.length === 0) return

  try {
    const result = await api.post<MessageDetail>('/messages', {
      text: text.value || null,
      files: files.value,
      actor_id: props.actorId ?? undefined,
      tag_ids: props.tagId != null ? [props.tagId] : undefined,
    })

    emit('sent', result)
    text.value = ''
    files.value = []
    if (textareaRef.value) textareaRef.value.style.height = 'auto'
    toast.success('消息已发送')
  } catch (error) {
    toast.error('发送消息失败')
  }
}
</script>
