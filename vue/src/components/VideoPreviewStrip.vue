<template>
  <div class="space-y-3">
    <!-- Action buttons -->
    <div class="flex flex-col gap-2">
      <button
        @click="pickerOpen = true"
        :disabled="busy"
        class="w-full flex items-center justify-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg disabled:opacity-40 transition-colors text-sm"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        从已有图片添加
      </button>
    </div>

    <!-- Preview list -->
    <div v-if="previews.length" class="space-y-2">
      <div
        v-for="p in previews"
        :key="p.id"
        class="group relative bg-gray-900 rounded-lg overflow-hidden border border-gray-800 hover:border-indigo-500 transition-colors cursor-pointer"
        @click="seekTo(p)"
      >
        <div class="flex gap-3 p-2">
          <img
            :src="resolveUrl(p.thumb_url)"
            :alt="`preview-${p.id}`"
            class="w-24 h-16 object-cover rounded bg-black flex-shrink-0"
            loading="lazy"
          />
          <div class="flex-1 min-w-0">
            <div class="text-xs text-gray-300 font-mono">{{ formatMs(p.frame_ms) }}</div>
            <div v-if="p.start_ms != null || p.end_ms != null" class="text-[10px] text-gray-500 mt-0.5">
              {{ p.start_ms != null ? formatMs(p.start_ms) : '?' }}
              →
              {{ p.end_ms != null ? formatMs(p.end_ms) : '?' }}
            </div>
          </div>
        </div>
        <div class="absolute top-1 right-1 hidden group-hover:flex gap-1">
          <button
            @click.stop="openEdit(p)"
            class="bg-gray-800/80 hover:bg-gray-700 text-white rounded p-1"
            title="编辑"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
          <button
            @click.stop="removePreview(p)"
            class="bg-red-600/80 hover:bg-red-500 text-white rounded p-1"
            title="删除"
          >
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V4a2 2 0 012-2h2a2 2 0 012 2v3" />
            </svg>
          </button>
        </div>
      </div>
    </div>
    <p v-else class="text-sm text-gray-500">暂无片段</p>

    <!-- Screenshot inline confirm card: 显示在信息栏下方 -->

    <!-- Picker modal -->
    <MediaPickerModal
      :visible="pickerOpen"
      @close="pickerOpen = false"
      @select="onPickImage"
    />

    <!-- Edit form modal -->
    <Teleport to="body">
      <div
        v-if="editing"
        class="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4"
        @click.self="editing = null"
      >
        <div class="bg-gray-950 rounded-2xl border border-gray-800 w-full max-w-sm p-6">
          <h2 class="text-lg font-semibold text-white mb-4">编辑预览</h2>
          <div class="space-y-3">
            <label class="block">
              <span class="text-xs text-gray-400">frame_ms（毫秒）</span>
              <input
                v-model.number="editForm.frame_ms"
                type="number"
                min="0"
                class="mt-1 w-full bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 text-sm"
              />
            </label>
            <label class="block">
              <span class="text-xs text-gray-400">start_ms（可选）</span>
              <input
                v-model.number="editForm.start_ms"
                type="number"
                min="0"
                class="mt-1 w-full bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 text-sm"
              />
            </label>
            <label class="block">
              <span class="text-xs text-gray-400">end_ms（可选）</span>
              <input
                v-model.number="editForm.end_ms"
                type="number"
                min="0"
                class="mt-1 w-full bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 text-sm"
              />
            </label>
          </div>
          <div class="mt-5 flex justify-end gap-2">
            <button
              @click="editing = null"
              class="px-3 py-1.5 text-gray-300 hover:bg-gray-800 rounded text-sm"
            >取消</button>
            <button
              @click="saveEdit"
              class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-sm"
            >保存</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Pick form modal (after picker selects image) -->
    <Teleport to="body">
      <div
        v-if="pickedMediaId != null"
        class="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4"
        @click.self="pickedMediaId = null"
      >
        <div class="bg-gray-950 rounded-2xl border border-gray-800 w-full max-w-sm p-6">
          <h2 class="text-lg font-semibold text-white mb-4">设置时间</h2>
          <div class="space-y-3">
            <label class="block">
              <span class="text-xs text-gray-400">frame_ms（毫秒，必填）</span>
              <input
                v-model.number="pickForm.frame_ms"
                type="number"
                min="0"
                class="mt-1 w-full bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 text-sm"
              />
            </label>
            <label class="block">
              <span class="text-xs text-gray-400">start_ms（可选）</span>
              <input
                v-model.number="pickForm.start_ms"
                type="number"
                min="0"
                class="mt-1 w-full bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 text-sm"
              />
            </label>
            <label class="block">
              <span class="text-xs text-gray-400">end_ms（可选）</span>
              <input
                v-model.number="pickForm.end_ms"
                type="number"
                min="0"
                class="mt-1 w-full bg-gray-900 border border-gray-700 text-white rounded px-3 py-2 text-sm"
              />
            </label>
          </div>
          <div class="mt-5 flex justify-end gap-2">
            <button
              @click="pickedMediaId = null"
              class="px-3 py-1.5 text-gray-300 hover:bg-gray-800 rounded text-sm"
            >取消</button>
            <button
              @click="confirmPick"
              class="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-sm"
            >确定</button>
          </div>
        </div>
      </div>
    </Teleport>

    <!-- Screenshot confirm modal: 前端先展示截图，确认后才上传 -->
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { VideoPreviewItem } from '../types'
import { api, ApiError } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { resolveUrl } from '../utils/media'
import MediaPickerModal from './MediaPickerModal.vue'

const props = defineProps<{
  videoMediaId: number
  previews: VideoPreviewItem[]
  videoEl: HTMLVideoElement | null
}>()

const emit = defineEmits<{
  (e: 'update:previews', value: VideoPreviewItem[]): void
}>()

const toast = useToast()
const busy = ref(false)
const pickerOpen = ref(false)
const pickedMediaId = ref<number | null>(null)
const editing = ref<VideoPreviewItem | null>(null)

const editForm = reactive({ frame_ms: 0, start_ms: null as number | null, end_ms: null as number | null })
const pickForm = reactive({ frame_ms: 0, start_ms: null as number | null, end_ms: null as number | null })

const formatMs = (ms: number): string => {
  const s = Math.floor(ms / 1000)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const milli = ms % 1000
  const head = h > 0 ? `${h}:${String(m).padStart(2, '0')}` : `${m}`
  return `${head}:${String(sec).padStart(2, '0')}.${String(milli).padStart(3, '0')}`
}

const sortPreviews = (arr: VideoPreviewItem[]) => [...arr].sort((a, b) => a.frame_ms - b.frame_ms)

const seekTo = (p: VideoPreviewItem) => {
  if (!props.videoEl) return
  const ms = p.start_ms ?? p.frame_ms
  props.videoEl.currentTime = ms / 1000
  props.videoEl.play().catch(() => { /* ignore */ })
}

const currentMs = (): number => {
  return props.videoEl ? Math.max(0, Math.round(props.videoEl.currentTime * 1000)) : 0
}

const onPickImage = (mediaId: number) => {
  pickerOpen.value = false
  pickedMediaId.value = mediaId
  pickForm.frame_ms = currentMs()
  pickForm.start_ms = null
  pickForm.end_ms = null
}

const confirmPick = async () => {
  if (pickedMediaId.value == null) return
  try {
    const item = await api.post<VideoPreviewItem>(`/media/${props.videoMediaId}/previews`, {
      preview_media_id: pickedMediaId.value,
      frame_ms: pickForm.frame_ms,
      start_ms: pickForm.start_ms,
      end_ms: pickForm.end_ms,
    })
    emit('update:previews', sortPreviews([...props.previews, item]))
    toast.success('已添加预览')
    pickedMediaId.value = null
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      toast.error('该图已被其他视频占用')
    } else {
      toast.error('添加失败')
    }
  }
}

const openEdit = (p: VideoPreviewItem) => {
  editing.value = p
  editForm.frame_ms = p.frame_ms
  editForm.start_ms = p.start_ms
  editForm.end_ms = p.end_ms
}

const saveEdit = async () => {
  if (!editing.value) return
  const target = editing.value
  try {
    const updated = await api.patch<VideoPreviewItem>(`/media/previews/${target.id}`, {
      frame_ms: editForm.frame_ms,
      start_ms: editForm.start_ms,
      end_ms: editForm.end_ms,
    })
    const next = props.previews.map(p => p.id === updated.id ? updated : p)
    emit('update:previews', sortPreviews(next))
    editing.value = null
    toast.success('已保存')
  } catch {
    toast.error('保存失败')
  }
}

const removePreview = async (p: VideoPreviewItem) => {
  if (!confirm(`删除该预览片段？`)) return
  try {
    await api.del(`/media/previews/${p.id}`)
    emit('update:previews', props.previews.filter(x => x.id !== p.id))
    toast.success('已删除')
  } catch {
    toast.error('删除失败')
  }
}
</script>
