<template>
  <div class="max-w-3xl mx-auto">
    <!-- Selected tags -->
    <div v-if="selectedTags.length > 0" class="flex flex-wrap gap-1.5 mb-2 px-10">
      <span v-for="t in selectedTags" :key="t.id"
        class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
        #{{ t.name }}
        <button @click="removeTag(t.id)" class="hover:text-red-500" title="移除标签">
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </span>
    </div>

    <!-- File chips -->
    <div v-if="files.length > 0" class="flex flex-wrap gap-2 mb-2 px-10">
      <div v-for="(filePath, index) in files" :key="index"
        class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-white/10 rounded-md text-xs">
        <span class="text-gray-700 dark:text-gray-300 truncate max-w-[12rem]">{{ filePath.split('\\').pop()?.split('/').pop() || filePath }}</span>
        <button @click="removeFile(index)" class="text-gray-500 hover:text-red-500 transition-colors">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Input row -->
    <div class="flex items-center gap-2">
      <div class="flex-1 min-w-0 flex items-center gap-1 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-2xl pl-1 pr-3 py-1 focus-within:border-[var(--color-primary-500)] transition-colors">
        <button @click="triggerFileInput" type="button"
          class="shrink-0 p-1.5 text-gray-500 hover:text-indigo-500 hover:bg-gray-100 dark:hover:bg-white/10 rounded-full transition-colors"
          title="添加附件">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
        </button>
        <VditorEditor ref="editorRef" v-model="text" placeholder="写点什么... (输入 # 选择标签)"
          class="flex-1 min-w-0 max-h-[40vh] overflow-y-auto text-sm"
          @update="tag.onUpdate" @ready="onEditorReady" />
      </div>

      <button @click="handleSubmit" :disabled="!canSubmit" type="button"
        class="shrink-0 w-8 h-8 rounded-full bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-500)] disabled:bg-gray-400 dark:disabled:bg-gray-600 text-white flex items-center justify-center shadow-md hover:shadow-lg transition-all active:scale-95"
        title="发送">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M5 12l14-7-7 14-2-5-5-2z" />
        </svg>
      </button>

      <input ref="fileInput" type="file" multiple class="hidden" @change="handleFileSelect" />
    </div>

    <!-- Tag suggestions -->
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
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import type { MessageDetail, TagItem } from '../types'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { useTagAutocompleteEditor } from '../composables/useTagAutocompleteEditor'
import VditorEditor from './VditorEditor.vue'

interface Props {
  allTags?: TagItem[]
  tagId?: number | null
  actorId?: number | null
  issueId?: number | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  created: [message: MessageDetail]
}>()

const toast = useToast()

const text = ref('')
const files = ref<string[]>([])
const submitting = ref(false)
const selectedTags = ref<TagItem[]>([])

const editorRef = ref<InstanceType<typeof VditorEditor> | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const tagSuggestionListEl = ref<HTMLElement | null>(null)

const addTag = (t: TagItem) => {
  if (selectedTags.value.some(x => x.id === t.id)) return
  selectedTags.value = [...selectedTags.value, t]
}

const removeTag = (tagId: number) => {
  selectedTags.value = selectedTags.value.filter(t => t.id !== tagId)
}

const tag = useTagAutocompleteEditor(editorRef as any, computed(() => props.allTags || []), addTag)
watch(tagSuggestionListEl, (el) => { tag.suggestionListRef.value = el })

const onEditorReady = () => {
  tag.attach()
  applyPreselectedTag()
}

const applyPreselectedTag = () => {
  if (props.tagId == null) return
  const preselect = (props.allTags || []).find(t => t.id === props.tagId)
  if (preselect && !selectedTags.value.some(t => t.id === preselect.id)) {
    selectedTags.value = [preselect]
  }
}

watch(() => props.tagId, () => {
  selectedTags.value = []
  applyPreselectedTag()
})

const canSubmit = computed(() => {
  if (submitting.value) return false
  return text.value.trim().length > 0 || files.value.length > 0
})

const handleSubmit = async () => {
  if (!canSubmit.value) return
  submitting.value = true

  const md = editorRef.value?.getMarkdown()
  if (typeof md === 'string') text.value = md

  try {
    const result = await api.post<MessageDetail>('/messages', {
      text: text.value || null,
      files: files.value,
      actor_id: props.actorId ?? undefined,
      issue_id: props.issueId ?? undefined,
      tag_ids: selectedTags.value.map(t => t.id),
    })
    emit('created', result)
    toast.success('消息已发送')

    text.value = ''
    files.value = []
    selectedTags.value = []
    applyPreselectedTag()
    await nextTick()
    editorRef.value?.focus()
  } catch {
    toast.error('发送消息失败')
  } finally {
    submitting.value = false
  }
}

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
      return
    } catch {
      /* fall through */
    }
  }
  fileInput.value?.click()
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files) return
  const filePaths = Array.from(target.files).map(file =>
    (file as any).path || (file as any).webkitRelativePath || file.name
  )
  files.value = [...files.value, ...filePaths]
  target.value = ''
}

const removeFile = (index: number) => {
  files.value.splice(index, 1)
}
</script>
