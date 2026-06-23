<template>
  <div
    class="group w-full aspect-square relative cursor-pointer rounded overflow-hidden bg-gray-200 dark:bg-gray-900"
    @click="emit('open')"
  >
    <img
      v-if="item.thumb_status !== 'pending' && thumb"
      :src="thumb"
      :alt="item.rel_path"
      class="w-full h-full object-cover"
      loading="lazy"
    />
    <div v-else class="absolute inset-0 flex items-center justify-center">
      <svg class="w-5 h-5 animate-spin text-gray-400" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
      </svg>
    </div>

    <!-- 视频播放图标 -->
    <div v-if="item.media_type === 'VIDEO'" class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div class="w-8 h-8 bg-black/40 rounded-full flex items-center justify-center border border-white/30">
        <svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
      </div>
    </div>

    <!-- HDR 角标 -->
    <span v-if="item.is_hdr === 1" class="absolute top-1 left-1 text-[10px] font-bold px-1 rounded bg-amber-500/90 text-white">HDR</span>
    <!-- 分辨率 -->
    <span v-if="item.height" class="absolute top-1 right-1 text-[10px] px-1 rounded bg-black/60 text-white">{{ item.height }}p</span>
    <!-- 时长 -->
    <span v-if="item.duration_ms" class="absolute bottom-1 right-1 text-xs px-1.5 py-0.5 rounded bg-black/70 text-white">{{ formatDuration(item.duration_ms) }}</span>
    <!-- 失败标记 -->
    <span v-if="item.thumb_status === 'failed'" class="absolute bottom-1 left-1 text-[10px] px-1 rounded bg-red-600/80 text-white">无缩略图</span>

    <!-- hover 底部:文件名 + 大小 + mtime -->
    <div class="absolute bottom-0 inset-x-0 px-1 py-0.5 bg-gradient-to-t from-black/70 to-transparent opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
      <div class="text-[10px] text-white truncate">{{ basename(item.rel_path) }}</div>
      <div class="text-[10px] text-white/70 truncate">{{ formatSize(item.file_size) }} · {{ formatMtime(item.mtime) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { FsEntry } from '../types'
import { formatDuration, resolveThumb, formatSize, formatMtime, basename } from '../utils/media'

const props = defineProps<{ item: FsEntry }>()
const emit = defineEmits<{ open: [] }>()

const thumb = computed(() => resolveThumb(props.item))
</script>
