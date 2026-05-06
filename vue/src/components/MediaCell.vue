<template>
  <div
    class="group w-full h-full relative cursor-pointer transition-transform duration-200 hover:scale-[1.03]"
    @click="emit('open')"
  >
    <img
      :src="resolveUrl(item.thumb_url)"
      :alt="String(item.id)"
      class="w-full h-full object-cover"
      loading="lazy"
    />
    <div class="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors duration-200 pointer-events-none"></div>
    <div v-if="isVideo(item.mime_type)" class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div class="w-8 h-8 bg-black/40 rounded-full flex items-center justify-center border border-white/30">
        <svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M8 5v14l11-7z"/>
        </svg>
      </div>
    </div>
    <div v-if="item.duration_ms" class="absolute bottom-1 right-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
      {{ formatDuration(item.duration_ms) }}
    </div>
    <button
      @click.stop="emit('star')"
      class="absolute top-1 right-1 p-1 rounded-full transition-all"
      :class="item.starred
        ? 'text-yellow-400'
        : 'text-white/70 hover:text-yellow-400 opacity-0 group-hover:opacity-100'
      "
    >
      <svg class="w-4 h-4" :class="{ 'star-bounce': bouncing }" :fill="item.starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
      </svg>
    </button>
  </div>
</template>

<script setup lang="ts">
import type { Media } from '../types'
import { isVideo, formatDuration, resolveUrl } from '../utils/media'

defineProps<{ item: Media; bouncing: boolean }>()
const emit = defineEmits<{ open: []; star: [] }>()
</script>
