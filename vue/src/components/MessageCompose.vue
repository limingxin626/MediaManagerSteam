<template>
  <div class="shrink-0 border-t border-white/10 shadow-lg">
    <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
      <div class="flex gap-2 items-center max-w-2xl mx-auto">
        <!-- Attachment Button -->
        <button @click="triggerFileInput"
          class="flex-shrink-0 p-2 text-gray-400 hover:text-indigo-400 hover:bg-white/10 rounded-lg transition-colors"
          title="添加附件">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
        </button>

        <!-- File Input (Hidden) -->
        <input ref="fileInput" type="file" multiple class="hidden" @change="handleFileSelect" />

        <!-- Text Input -->
        <div class="flex-1 relative">
          <textarea ref="textareaRef" v-model="text" placeholder="输入消息..." rows="1"
            class="w-full px-4 py-2 border border-white/10 rounded-lg bg-white/10 text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none max-h-32 overflow-hidden"
            @keydown="handleKeydown" @input="handleInput" />
        </div>

        <!-- Send Button -->
        <button @click="send" :disabled="!text.trim() && files.length === 0"
          class="flex-shrink-0 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-600 text-white rounded-lg transition-colors"
          title="发送">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>

      <!-- Selected Files Preview -->
      <div v-if="files.length > 0" class="mt-2 max-w-2xl mx-auto">
        <div class="flex flex-wrap gap-2">
          <div v-for="(filePath, index) in files" :key="index"
            class="inline-flex items-center gap-1 px-2 py-1 bg-white/10 rounded-md text-sm">
            <span class="text-gray-300 truncate max-w-xs">{{ filePath.split('\\').pop() || filePath }}</span>
            <button @click="removeFile(index)" class="text-gray-500 hover:text-red-500 transition-colors">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Tag Suggestions -->
    <div
      v-if="tagSuggestionVisible && tagSuggestions.length > 0"
      class="fixed bg-gray-800 border border-white/10 rounded-lg shadow-xl max-h-48 overflow-y-auto z-[100]"
      :style="{ top: tagSuggestionPosition.top + 'px', left: tagSuggestionPosition.left + 'px', transform: 'translateY(-100%)' }"
    >
      <div
        v-for="(tag, index) in tagSuggestions"
        :key="tag.id"
        @click="selectTagSuggestion(tag)"
        class="px-3 py-2 cursor-pointer text-sm"
        :class="index === tagSuggestionIndex ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-white/10'"
      >
        #{{ tag.name }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { MessageDetail, TagItem } from '../types'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'

const props = defineProps<{
  actorId?: number | null
  tagId?: number | null
  allTags?: TagItem[]
}>()

const emit = defineEmits<{
  sent: [message: MessageDetail]
}>()

const toast = useToast()

const text = ref('')
const files = ref<string[]>([])
const fileInput = ref<HTMLInputElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

// Tag 自动提示相关状态
const tagSuggestions = ref<TagItem[]>([])
const tagSuggestionVisible = ref(false)
const tagSuggestionIndex = ref(0)
const tagSuggestionPosition = ref({ top: 0, left: 0 })
let currentTagStart = -1

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

const updateSuggestionPosition = () => {
  const textarea = textareaRef.value
  if (!textarea) return

  const caretPos = textarea.selectionStart
  const cs = window.getComputedStyle(textarea)
  const textareaRect = textarea.getBoundingClientRect()

  const mirror = document.createElement('div')

  ;[
    'font-family', 'font-size', 'font-weight', 'font-style',
    'letter-spacing', 'word-spacing', 'line-height',
    'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
    'border-top-width', 'border-right-width', 'border-bottom-width', 'border-left-width',
    'box-sizing', 'word-wrap', 'overflow-wrap',
  ].forEach((prop) => mirror.style.setProperty(prop, cs.getPropertyValue(prop)))

  mirror.style.position = 'fixed'
  mirror.style.visibility = 'hidden'
  mirror.style.pointerEvents = 'none'
  mirror.style.top = textareaRect.top + 'px'
  mirror.style.left = textareaRect.left + 'px'
  mirror.style.width = textareaRect.width + 'px'
  mirror.style.height = textareaRect.height + 'px'
  mirror.style.whiteSpace = 'pre-wrap'
  mirror.style.wordBreak = 'break-word'
  mirror.style.overflow = 'hidden'

  mirror.textContent = textarea.value.substring(0, caretPos)

  const caretSpan = document.createElement('span')
  caretSpan.textContent = '\u200b'
  mirror.appendChild(caretSpan)

  document.body.appendChild(mirror)
  const spanRect = caretSpan.getBoundingClientRect()
  document.body.removeChild(mirror)

  tagSuggestionPosition.value = {
    top: spanRect.top - textarea.scrollTop - 4,
    left: spanRect.left - textarea.scrollLeft,
  }
}

const handleInput = () => {
  autoResize()

  const textarea = textareaRef.value
  if (!textarea) return

  const cursorPos = textarea.selectionStart
  let hashPos = -1
  for (let i = cursorPos - 1; i >= 0; i--) {
    if (text.value[i] === '#') {
      hashPos = i
      break
    }
    if (text.value[i] === ' ' || text.value[i] === '\n') {
      break
    }
  }

  if (hashPos === -1) {
    tagSuggestionVisible.value = false
    return
  }

  const afterHash = text.value.substring(hashPos + 1, cursorPos)
  if (afterHash.includes(' ') || afterHash.includes('\n')) {
    tagSuggestionVisible.value = false
    return
  }

  currentTagStart = hashPos
  const query = afterHash.toLowerCase()
  const allTags = props.allTags || []
  tagSuggestions.value = allTags.filter(tag =>
    tag.name.toLowerCase().includes(query)
  ).slice(0, 8)

  if (tagSuggestions.value.length > 0) {
    tagSuggestionVisible.value = true
    tagSuggestionIndex.value = 0
    updateSuggestionPosition()
  } else {
    tagSuggestionVisible.value = false
  }
}

const handleKeydown = (e: KeyboardEvent) => {
  if (tagSuggestionVisible.value) {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      tagSuggestionIndex.value = Math.min(
        tagSuggestionIndex.value + 1,
        tagSuggestions.value.length - 1
      )
      return
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      tagSuggestionIndex.value = Math.max(tagSuggestionIndex.value - 1, 0)
      return
    } else if (e.key === 'Tab') {
      e.preventDefault()
      selectTagSuggestion(tagSuggestions.value[tagSuggestionIndex.value])
      return
    } else if (e.key === 'Enter') {
      e.preventDefault()
      selectTagSuggestion(tagSuggestions.value[tagSuggestionIndex.value])
      return
    } else if (e.key === 'Escape') {
      tagSuggestionVisible.value = false
      return
    }
  }

  // Default Enter behavior: send message
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

const selectTagSuggestion = (tag: TagItem) => {
  if (!tag || currentTagStart === -1) return

  const textarea = textareaRef.value
  if (!textarea) return

  const cursorPos = textarea.selectionStart
  const before = text.value.substring(0, currentTagStart)
  const after = text.value.substring(cursorPos)
  const tagName = tag.name.includes(' ') ? `#${tag.name}#` : `#${tag.name}`

  text.value = before + tagName + (after.startsWith(' ') ? '' : ' ') + after

  tagSuggestionVisible.value = false
  currentTagStart = -1

  setTimeout(() => {
    const newPos = before.length + tagName.length + 1
    textarea.setSelectionRange(newPos, newPos)
    textarea.focus()
  }, 0)
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
