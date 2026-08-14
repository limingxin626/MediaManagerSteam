<template>
  <div v-if="visible" class="message-compose-overlay fixed inset-0 z-[95] bg-[var(--bg-primary)] flex flex-col animate-fade-in"
    @keydown.esc="handleEscape"
    @dragenter.prevent="onDragEnter" @dragover.prevent @dragleave="onDragLeave" @drop.prevent="onDropFiles">    <!-- 顶部工具栏 -->
    <div class="shrink-0 flex items-center justify-between gap-3 px-5 py-3 border-b border-[var(--border-color)]">
      <div class="flex items-center gap-3 min-w-0">
        <button @click="handleClose" title="返回"
          class="shrink-0 flex items-center gap-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          <span class="text-sm">返回</span>
        </button>
        <h3 class="text-sm font-semibold text-[var(--text-primary)] pl-2 border-l border-[var(--border-color)]">
          {{ mode === 'create' ? '新消息' : '编辑消息' }}
        </h3>
      </div>
      <button @click="handleSubmit" :disabled="!canSubmit"
        class="shrink-0 px-4 py-1.5 bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-700)] disabled:bg-gray-600 text-white text-sm rounded-[var(--radius-sm)] transition-colors">
        {{ mode === 'create' ? '发送' : '保存' }}
      </button>
    </div>

    <!-- Body: 左写作区 + 右元数据侧栏 -->
    <div class="flex-1 min-h-0 flex flex-col lg:flex-row">
      <!-- 左:写作区 -->
      <div class="flex-1 min-w-0 flex flex-col items-center p-6">
        <MilkdownEditor ref="editorRef" v-model="text" placeholder="输入消息内容..."
          class="flex-1 w-full max-w-5xl min-h-[40vh] border border-[var(--border-color)] rounded-[var(--radius-lg)] bg-[var(--bg-card)] overflow-y-auto"
          @update="tag.onUpdate" @ready="onEditorReady" />
      </div>

      <!-- 右:元数据侧栏 -->
      <aside
        class="shrink-0 w-full lg:w-[40rem] border-t lg:border-t-0 lg:border-l border-[var(--border-color)] overflow-y-auto p-5 space-y-6 bg-[var(--bg-secondary)]/40">
        <!-- 标签 -->
        <section>
          <div class="flex items-center justify-between mb-2">
            <h4 class="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide">标签</h4>
            <TagPickerPopover v-if="allTags && allTags.length" :all-tags="allTags" :message-tags="selectedTags"
              direction="down" @select="addTag" @created="emit('tagCreated')" />
          </div>
          <div class="flex flex-wrap gap-1.5 min-h-[1.75rem]">
            <span v-for="t in selectedTags" :key="t.id"
              class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-indigo-100 text-indigo-700 dark:bg-indigo-500/20 dark:text-indigo-300">
              #{{ t.name }}
              <button @click="removeTag(t.id)" class="hover:text-red-500" title="移除标签">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </span>
            <span v-if="selectedTags.length === 0"
              class="text-xs text-[var(--text-muted)] self-center">点「+」或在正文输入 # 添加</span>
          </div>
        </section>

        <!-- 创建日期 (edit mode only) -->
        <section v-if="mode === 'edit'">
          <h4 class="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">创建日期</h4>
          <input v-model="editDate" type="datetime-local"
            class="w-full px-3 py-2 text-sm border border-[var(--border-color)] rounded-[var(--radius-md)] bg-[var(--bg-card)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent" />
        </section>

        <!-- 媒体 -->
        <section>
          <h4 class="text-xs font-semibold text-[var(--text-secondary)] uppercase tracking-wide mb-2">媒体</h4>
          <div v-if="existingMedia.length > 0 || newFilePreviews.length > 0 || files.length > 0"
            class="grid grid-cols-3 gap-2 mb-3">
            <!-- 已存在媒体 (edit) -->
            <div v-for="media in existingMedia" :key="'existing-' + media.id"
              class="relative aspect-square rounded-lg overflow-hidden group"
              draggable="true"
              @dragstart="onDragStart($event, media.id, 'existing')"
              @dragover.prevent="onDragOver($event)"
              @drop.stop="onDrop($event, media.id, 'existing')">
              <img :src="resolveThumb(media)" class="w-full h-full object-cover" />
              <button @click="removeExistingMedia(media.id)"
                class="absolute top-1 right-1 p-0.5 bg-black/60 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
              <div v-if="media.mime_type && media.mime_type.startsWith('video')"
                class="absolute bottom-1 left-1 bg-black/60 text-white text-xs px-1 rounded">视频</div>
            </div>
            <!-- 新选文件预览 (create/edit) -->
            <div v-for="(file, index) in newFilePreviews" :key="'new-' + index"
              class="relative aspect-square rounded-lg overflow-hidden group border-2 border-dashed border-indigo-400/50">
              <img v-if="file.previewUrl" :src="file.previewUrl" class="w-full h-full object-cover" />
              <div v-else class="w-full h-full flex items-center justify-center bg-[var(--bg-card)]" :title="file.file.name">
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
            <!-- Electron 本地路径 (无缩略图,只显示文件名) -->
            <div v-for="(filePath, index) in files" :key="'path-' + index"
              class="relative aspect-square rounded-lg overflow-hidden group border-2 border-dashed border-gray-400/40 flex items-center justify-center p-1 bg-[var(--bg-card)]">
              <span class="text-[10px] text-[var(--text-muted)] text-center break-all line-clamp-3">{{ filePath.split('\\').pop()?.split('/').pop() || filePath }}</span>
              <button @click="removeElectronFile(index)"
                class="absolute top-1 right-1 p-0.5 bg-black/60 rounded-full text-white opacity-0 group-hover:opacity-100 transition-opacity">
                <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          <button @click="triggerFileInput"
            class="w-full inline-flex items-center justify-center gap-1.5 px-3 py-2 text-sm text-[var(--text-secondary)] hover:text-[var(--color-primary-600)] border border-dashed border-[var(--border-color)] hover:border-[var(--color-primary-500)] rounded-[var(--radius-md)] transition-colors">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            添加媒体
          </button>
          <p class="mt-1.5 text-xs text-[var(--text-muted)]">也可以把文件拖拽到这个页面</p>
          <input ref="fileInput" type="file" multiple accept="image/*,video/*" class="hidden" @change="handleFileSelect" />
        </section>
      </aside>
    </div>

    <!-- Tag Suggestions (# 补全浮层,fixed 定位) -->
    <div v-if="tag.tagSuggestionVisible.value && tag.tagSuggestions.value.length > 0"
      ref="tagSuggestionListEl"
      class="fixed bg-white dark:bg-gray-800 border border-gray-200 dark:border-white/10 rounded-lg shadow-xl max-h-48 overflow-y-auto z-[100]"
      :style="{ top: tag.tagSuggestionPosition.value.top + 'px', left: tag.tagSuggestionPosition.value.left + 'px', transform: tag.tagSuggestionPosition.value.placement === 'above' ? 'translateY(-100%)' : 'none' }">
      <div v-for="(t, index) in tag.tagSuggestions.value" :key="t.id" @click="tag.selectTag(t)"
        class="px-3 py-2 cursor-pointer text-sm"
        :class="index === tag.tagSuggestionIndex.value ? 'bg-indigo-600 text-white' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
        #{{ t.name }}
      </div>
    </div>

    <!-- 拖拽文件高亮遮罩 -->
    <div v-if="dragActive"
      class="absolute inset-0 z-[110] bg-[var(--color-primary-600)]/10 border-4 border-dashed border-[var(--color-primary-500)] rounded-lg flex items-center justify-center pointer-events-none">
      <div class="px-6 py-3 bg-[var(--bg-card)] rounded-full shadow-lg text-sm font-medium text-[var(--color-primary-600)]">
        松开鼠标添加媒体
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onUnmounted } from 'vue'
import type { MessageDetail, MessageMediaItem, TagItem, TagWithCount } from '../types'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { useTagAutocompleteEditor } from '../composables/useTagAutocompleteEditor'
import { resolveThumb } from '../utils/media'
import { API_BASE_URL } from '../utils/constants'
import MilkdownEditor from './MilkdownEditor.vue'
import TagPickerPopover from './TagPickerPopover.vue'

interface Props {
  visible: boolean
  mode: 'create' | 'edit'
  messageId?: number
  initialText?: string
  initialDate?: string
  initialMedia?: MessageMediaItem[]
  initialTags?: TagItem[]
  allTags?: TagWithCount[]
  tagId?: number | null
  collectionId?: number | null
  issueId?: number | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  created: [message: MessageDetail]
  updated: [messageId: number, text: string, date: string, tagIds: number[]]
  mediaChanged: [messageId: number]
  tagCreated: []
}>()

const toast = useToast()

const text = ref('')
const editDate = ref('')
// Electron 直传的本地绝对路径(web 走 File 上传,见 newFiles)
const files = ref<string[]>([])
const editorRef = ref<InstanceType<typeof MilkdownEditor> | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)
const submitting = ref(false)
const dragActive = ref(false)

// 媒体状态(create/edit 共用):新选的本地文件 + 预览;edit 额外有已存在媒体
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

const tag = useTagAutocompleteEditor(editorRef as any, computed(() => props.allTags || []), addTag)
const tagSuggestionListEl = ref<HTMLElement | null>(null)
watch(tagSuggestionListEl, (el) => { tag.suggestionListRef.value = el })

const onEditorReady = () => {
  tag.attach()
}

const canSubmit = computed(() => {
  if (submitting.value) return false
  if (props.mode === 'create')
    return text.value.trim().length > 0 || newFiles.value.length > 0 || files.value.length > 0
  return true
})

watch(() => props.visible, async (visible) => {
  if (visible) {
    text.value = props.initialText || ''
    editDate.value = props.initialDate || ''
    files.value = []
    submitting.value = false
    dragActive.value = false
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
    editorRef.value?.focus()
  } else {
    tag.hide()
    tag.detach()
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

const handleEscape = () => {
  if (tag.tagSuggestionVisible.value) {
    tag.hide()
    return
  }
  // Esc 不关闭整个页面,只能手动点左上角返回
}

const handleClose = () => {
  tag.hide()
  emit('close')
}

// 把 newFiles 逐个上传,返回 repo 内相对路径列表
const uploadNewFiles = async (): Promise<string[]> => {
  const uploaded: string[] = []
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
    uploaded.push(data.path)
  }
  return uploaded
}

const handleSubmit = async () => {
  if (!canSubmit.value) return
  submitting.value = true

  // 兜底：从编辑器拉一次最新 markdown，避免 listener 未触发
  const md = editorRef.value?.getMarkdown()
  if (typeof md === 'string') text.value = md

  try {
    if (props.mode === 'create') {
      // web: File 上传拿路径;electron: files 已是本地绝对路径,合并一起传
      const uploadedPaths = newFiles.value.length > 0 ? await uploadNewFiles() : []
      const allFiles = [...files.value, ...uploadedPaths]
      const result = await api.post<MessageDetail>('/messages', {
        text: text.value || null,
        files: allFiles,
        collection_id: props.collectionId ?? undefined,
        issue_id: props.issueId ?? undefined,
        tag_ids: selectedTags.value.map(t => t.id),
      })
      emit('created', result)
      toast.success('消息已发送')
    } else {
      // Upload new files first
      if (newFiles.value.length > 0) {
        const uploadedPaths = await uploadNewFiles()
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

// --- File handling (create/edit 共用) ---

const triggerFileInput = async () => {
  const isElectron = navigator.userAgent.indexOf('Electron') > -1
  if (isElectron && window.electronAPI) {
    try {
      const result = await window.electronAPI.openFileDialog({
        properties: ['openFile', 'multiSelections'],
      })
      if (!result.canceled && result.filePaths) {
        files.value = [...files.value, ...result.filePaths]
      }
      return
    } catch {
      /* fall through to file input */
    }
  }
  fileInput.value?.click()
}

// 收下一批本地 File,生成预览
const addLocalFiles = (fileList: FileList | File[]) => {
  for (const file of Array.from(fileList)) {
    newFiles.value.push(file)
    const isImage = file.type.startsWith('image/')
    newFilePreviews.value.push({
      file,
      previewUrl: isImage ? URL.createObjectURL(file) : null,
    })
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (!target.files) return
  addLocalFiles(target.files)
  target.value = ''
}

// --- Drag & drop 文件到整个页面 ---

const onDragEnter = (e: DragEvent) => {
  if (e.dataTransfer?.types.includes('Files')) dragActive.value = true
}

const onDragLeave = (e: DragEvent) => {
  // 只在真正离开窗口时关闭(relatedTarget 为空)
  if (!e.relatedTarget) dragActive.value = false
}

const onDropFiles = (e: DragEvent) => {
  dragActive.value = false
  const dropped = e.dataTransfer?.files
  if (dropped && dropped.length > 0) addLocalFiles(dropped)
}

const removeNewFile = (index: number) => {
  const preview = newFilePreviews.value[index]
  if (preview?.previewUrl) URL.revokeObjectURL(preview.previewUrl)
  newFiles.value.splice(index, 1)
  newFilePreviews.value.splice(index, 1)
}

// 移除 Electron 直传的本地路径
const removeElectronFile = (index: number) => {
  files.value.splice(index, 1)
}
</script>
