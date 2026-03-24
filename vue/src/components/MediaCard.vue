<template>
  <div 
    class="hover:scale-[1.02] transition-all duration-200 cursor-pointer flex flex-col relative rounded-lg overflow-hidden"
    @click="$emit('click', media.id)"
    @contextmenu="$emit('contextmenu', $event, media)"
  >
    <!-- Thumbnail -->
    <div class="aspect-[1/1] overflow-hidden relative rounded-lg">
      <img 
        :src="`file:///E:/AskTao/data/thumbs/${media.id}.webp`" 
        :alt="media.name" 
        class="w-full h-full object-cover rounded-lg"
      />
      
      <!-- Video Play Icon -->
      <div v-if="media.type === 'VIDEO'" class="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div class="w-10 h-10 bg-black/40 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/30">
          <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
            <path d="M8 5v14l11-7z"/>
          </svg>
        </div>
      </div>
      
      <!-- Duration Badge -->
      <div v-if="media.duration" class="absolute top-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded backdrop-blur-sm">
        {{ formatDuration(media.duration) }}
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { API_BASE_URL } from '../utils/constants'

interface Media {
  id: number
  name: string
  type: string | null
  thumbnail_path: string | null
  duration: number | null
  rating: number | null
}

interface Props {
  media: Media
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [id: number]
  contextmenu: [event: MouseEvent, media: Media]
}>()

// 格式化时长显示
const formatDuration = (duration: number | null): string => {
  if (!duration) return ''
  
  const totalSeconds = Math.round(duration)
  const hours = Math.floor(totalSeconds / 3600)
  const mins = Math.floor((totalSeconds % 3600) / 60)
  const secs = totalSeconds % 60
  
  if (hours > 0) {
    return `${hours}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  } else {
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }
}
</script>
