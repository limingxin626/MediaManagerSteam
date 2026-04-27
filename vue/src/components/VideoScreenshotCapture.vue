<template>
  <div class="bg-gray-900 border border-gray-800 rounded-lg p-3 space-y-3">
    <h3 class="text-xs font-semibold text-gray-400 uppercase tracking-wider">截图预览</h3>

    <div
      v-if="pendingShot"
      class="rounded border border-indigo-700/60 overflow-hidden bg-black"
    >
      <img :src="pendingShot.dataUrl" alt="screenshot" class="w-full block" />
    </div>
    <div
      v-else
      class="rounded border border-dashed border-gray-700 bg-black/40 aspect-video flex items-center justify-center text-xs text-gray-500"
    >
      尚未截图
    </div>

    <div class="space-y-1.5 text-xs">
      <div class="flex justify-between items-center">
        <span class="text-gray-400">时间戳</span>
        <span class="font-mono" :class="pendingShot ? 'text-white' : 'text-gray-600'">
          {{ pendingShot ? formatMs(shotForm.frame_ms) : '未截图' }}
        </span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-400">开始</span>
        <span class="font-mono" :class="shotForm.start_ms != null ? 'text-white' : 'text-gray-600'">
          {{ shotForm.start_ms != null ? formatMs(shotForm.start_ms) : '未设置' }}
        </span>
      </div>
      <div class="flex justify-between items-center">
        <span class="text-gray-400">结束</span>
        <span class="font-mono" :class="shotForm.end_ms != null ? 'text-white' : 'text-gray-600'">
          {{ shotForm.end_ms != null ? formatMs(shotForm.end_ms) : '未设置' }}
        </span>
      </div>
    </div>

    <div class="flex gap-1.5">
      <button
        @click="setShotStart"
        :disabled="busy || !videoEl"
        class="flex-1 px-2 py-1.5 bg-gray-800 hover:bg-gray-700 text-white text-xs rounded disabled:opacity-40"
        title="把当前播放位置设为开始时间"
      >设为开始</button>
      <button
        @click="setShotEnd"
        :disabled="busy || !videoEl"
        class="flex-1 px-2 py-1.5 bg-gray-800 hover:bg-gray-700 text-white text-xs rounded disabled:opacity-40"
        title="把当前播放位置设为结束时间"
      >设为结束</button>
    </div>

    <button
      @click="captureScreenshot"
      :disabled="busy || !videoEl"
      class="w-full flex items-center justify-center gap-2 px-3 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg disabled:opacity-40 disabled:cursor-not-allowed transition-colors text-sm"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
      {{ pendingShot ? '重新截图' : '截图' }}
    </button>

    <div class="flex gap-1.5">
      <button
        @click="cancelShot"
        :disabled="busy || !pendingShot"
        class="flex-1 px-2 py-1.5 text-gray-300 hover:bg-gray-800 rounded text-xs disabled:opacity-40"
      >取消</button>
      <button
        @click="confirmShot"
        :disabled="busy || !pendingShot"
        class="flex-1 px-2 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs disabled:opacity-40"
      >{{ busy ? '上传中...' : '确认上传' }}</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import type { VideoPreviewItem } from '../types'
import { useToast } from '../composables/useToast'
import { API_BASE_URL } from '../utils/constants'

const props = defineProps<{
  videoMediaId: number
  videoEl: HTMLVideoElement | null
}>()

const emit = defineEmits<{
  (e: 'preview-added', item: VideoPreviewItem): void
}>()

const toast = useToast()
const busy = ref(false)
const pendingShot = ref<{ blob: Blob; dataUrl: string } | null>(null)
const shotForm = reactive({ frame_ms: 0, start_ms: null as number | null, end_ms: null as number | null })

const formatMs = (ms: number): string => {
  const s = Math.floor(ms / 1000)
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const milli = ms % 1000
  const head = h > 0 ? `${h}:${String(m).padStart(2, '0')}` : `${m}`
  return `${head}:${String(sec).padStart(2, '0')}.${String(milli).padStart(3, '0')}`
}

const currentMs = (): number => {
  return props.videoEl ? Math.max(0, Math.round(props.videoEl.currentTime * 1000)) : 0
}

const captureScreenshot = async () => {
  if (!props.videoEl || busy.value) return
  try {
    const v = props.videoEl
    const canvas = document.createElement('canvas')
    canvas.width = v.videoWidth || 1280
    canvas.height = v.videoHeight || 720
    const ctx = canvas.getContext('2d')
    if (!ctx) throw new Error('canvas 不可用')
    ctx.drawImage(v, 0, 0, canvas.width, canvas.height)
    const blob: Blob = await new Promise((resolve, reject) => {
      canvas.toBlob(b => b ? resolve(b) : reject(new Error('截图失败')), 'image/jpeg', 0.92)
    })
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92)
    shotForm.frame_ms = currentMs()
    pendingShot.value = { blob, dataUrl }
  } catch (e) {
    const msg = e instanceof Error ? e.message : '截图失败'
    toast.error(msg)
  }
}

const setShotStart = () => {
  if (!props.videoEl) return
  shotForm.start_ms = currentMs()
}

const setShotEnd = () => {
  if (!props.videoEl) return
  shotForm.end_ms = currentMs()
}

const cancelShot = () => {
  if (busy.value) return
  pendingShot.value = null
  shotForm.start_ms = null
  shotForm.end_ms = null
}

const confirmShot = async () => {
  if (!pendingShot.value || busy.value) return
  const { frame_ms, start_ms, end_ms } = shotForm
  if (start_ms != null && start_ms > frame_ms) {
    toast.error('开始时间必须 ≤ 时间戳')
    return
  }
  if (end_ms != null && end_ms < frame_ms) {
    toast.error('结束时间必须 ≥ 时间戳')
    return
  }
  if (start_ms != null && end_ms != null && start_ms > end_ms) {
    toast.error('开始时间必须 ≤ 结束时间')
    return
  }
  busy.value = true
  try {
    const fd = new FormData()
    fd.append('file', pendingShot.value.blob, `screenshot_${Date.now()}.jpg`)
    fd.append('frame_ms', String(frame_ms))
    if (start_ms != null) fd.append('start_ms', String(start_ms))
    if (end_ms != null) fd.append('end_ms', String(end_ms))
    const res = await fetch(`${API_BASE_URL}/media/${props.videoMediaId}/previews/screenshot`, {
      method: 'POST',
      body: fd,
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({}))
      throw new Error(err.detail ?? `${res.status}`)
    }
    const item = await res.json() as VideoPreviewItem
    emit('preview-added', item)
    pendingShot.value = null
    shotForm.start_ms = end_ms
    shotForm.end_ms = null
    toast.success('已添加预览')
  } catch (e) {
    const msg = e instanceof Error ? e.message : '上传失败'
    toast.error(msg)
  } finally {
    busy.value = false
  }
}
</script>
