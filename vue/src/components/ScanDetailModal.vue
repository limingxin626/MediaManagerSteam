<template>
  <TransitionRoot appear :show="!!item" as="template">
    <Dialog as="div" @close="emit('close')" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out" enter-from="opacity-0" enter-to="opacity-100"
        leave="duration-200 ease-in" leave-from="opacity-100" leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/50" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out" enter-from="opacity-0 scale-95" enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in" leave-from="opacity-100 scale-100" leave-to="opacity-0 scale-95"
          >
            <DialogPanel
              v-if="display"
              class="w-full max-w-3xl transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 text-left align-middle shadow-xl transition-all flex flex-col md:flex-row"
            >
              <!-- 预览 -->
              <div class="md:w-1/2 bg-black flex items-center justify-center min-h-[240px]">
                <img v-if="thumb" :src="thumb" :alt="display.rel_path" class="max-h-[60vh] w-full object-contain" />
                <div v-else class="text-gray-500 text-sm p-8">无预览</div>
              </div>

              <!-- metadata -->
              <div class="md:w-1/2 p-5 space-y-3 max-h-[70vh] overflow-y-auto">
                <DialogTitle as="h3" class="text-base font-semibold text-gray-900 dark:text-white break-all">
                  {{ basename(display.rel_path) }}
                </DialogTitle>

                <dl class="text-sm space-y-1.5">
                  <Row label="仓库" :value="display.repo_id" />
                  <Row label="路径" :value="display.rel_path" mono />
                  <Row label="类型" :value="display.media_type" />
                  <Row label="大小" :value="formatSize(display.file_size)" />
                  <Row label="修改时间" :value="formatMtime(display.mtime)" />
                  <Row v-if="display.taken_at" label="拍摄时间" :value="formatDate(display.taken_at)" />
                  <Row v-if="display.width" label="分辨率" :value="`${display.width} × ${display.height}`" />
                  <Row v-if="display.duration_ms" label="时长" :value="formatDuration(display.duration_ms)" />
                  <Row v-if="display.fps" label="帧率" :value="`${display.fps} fps`" />
                  <Row v-if="display.bitrate" label="码率" :value="`${Math.round(display.bitrate / 1000)} kbps`" />
                  <Row v-if="display.video_codec" label="视频编码" :value="display.video_codec" />
                  <Row v-if="display.audio_codec" label="音频编码" :value="display.audio_codec" />
                  <Row v-if="display.is_hdr !== null" label="HDR" :value="display.is_hdr === 1 ? `是${display.color_transfer ? ' (' + display.color_transfer + ')' : ''}` : '否'" />
                  <Row v-if="display.camera_make || display.camera_model" label="相机" :value="[display.camera_make, display.camera_model].filter(Boolean).join(' ')" />
                  <Row v-if="display.lens" label="镜头" :value="display.lens" />
                  <div v-if="display.gps_lat != null && display.gps_lng != null" class="flex gap-2">
                    <dt class="text-gray-500 dark:text-gray-400 w-20 shrink-0">位置</dt>
                    <dd>
                      <a
                        :href="`https://www.google.com/maps?q=${display.gps_lat},${display.gps_lng}`"
                        target="_blank" rel="noopener"
                        class="text-[var(--color-primary-600)] underline break-all"
                      >{{ display.gps_lat }}, {{ display.gps_lng }}</a>
                    </dd>
                  </div>
                  <Row label="状态" :value="`meta=${display.meta_status} / thumb=${display.thumb_status}`" />
                  <Row v-if="display.media_id" label="Media ID" :value="String(display.media_id)" />
                </dl>

                <div class="flex gap-2 pt-2">
                  <a
                    :href="fileUrl" target="_blank" rel="noopener"
                    class="flex-1 text-center bg-[var(--color-primary-600)] text-white px-3 py-2 rounded-lg text-sm hover:opacity-90 transition"
                  >打开文件</a>
                  <button
                    @click="emit('close')"
                    class="px-4 py-2 rounded-lg text-sm bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-600 transition"
                  >关闭</button>
                </div>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { computed, h, ref, watch } from 'vue'
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild } from '@headlessui/vue'
import type { FsEntry } from '../types'
import { resolveThumb, resolveMediaUrl, formatSize, formatMtime, formatDuration, basename } from '../utils/media'

const props = defineProps<{ item: FsEntry | null }>()
const emit = defineEmits<{ close: [] }>()

// 关闭时父级会把 item 置 null,但 TransitionRoot 的 leave 动画还在播 —— 此时若用
// v-if="item" 直接销毁 DialogPanel,会和 HeadlessUI 的过渡 DOM 管理打架,
// 报 "Cannot read properties of null (reading 'type')"。
// 因此缓存最后一次非空 item,leave 期间继续渲染旧内容,由 :show 控制真正的挂载/卸载。
const display = ref<FsEntry | null>(null)
watch(
  () => props.item,
  (v) => { if (v) display.value = v },
  { immediate: true },
)

const thumb = computed(() => resolveThumb(display.value))
const fileUrl = computed(() => resolveMediaUrl(display.value))

function formatDate(iso: string): string {
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

// 简单的 label/value 行组件(避免重复模板)
const Row = (p: { label: string; value: string; mono?: boolean }) =>
  h('div', { class: 'flex gap-2' }, [
    h('dt', { class: 'text-gray-500 dark:text-gray-400 w-20 shrink-0' }, p.label),
    h('dd', { class: ['break-all text-gray-800 dark:text-gray-200', p.mono ? 'font-mono text-xs' : ''] }, p.value),
  ])
</script>
