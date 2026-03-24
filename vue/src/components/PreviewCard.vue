<template>
  <div 
    class="cursor-pointer group"
    @click="$emit('click', preview)"
  >
    <!-- Thumbnail -->
    <div class="relative overflow-hidden rounded-lg bg-gray-200 dark:bg-gray-800">
      <img 
        :src="`file:///E:/AskTao/data/thumbs/${preview.id}.webp`" 
        :alt="preview.name" 
        class="w-full h-auto object-contain transition-transform duration-200 group-hover:scale-105"
      />
      
      
      <!-- Time Range Badge -->
      <div v-if="hasTimeRange" class="absolute top-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded backdrop-blur-sm">
        {{ formatTimeRange }}
      </div>
    </div>

    <!-- Timestamp Display -->
    <p v-if="preview.timestamp !== null && preview.timestamp !== undefined" class="text-xs text-gray-500 dark:text-gray-400">
      时间点: {{ formatTimestamp(preview.timestamp) }}
    </p>
  </div>
</template>

<script setup lang="ts">
interface Preview {
  id: number
  name: string
  start_time: number | null
  end_time: number | null
  timestamp: number | null
}

interface Props {
  preview: Preview
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [preview: Preview]
}>()

// 判断是否有时长范围
const hasTimeRange = computed(() => {
  return props.preview.start_time !== null && props.preview.end_time !== null
})

// 格式化时间范围显示
const formatTimeRange = computed(() => {
  if (!hasTimeRange.value) return ''
  const start = formatTime(props.preview.start_time!)
  const end = formatTime(props.preview.end_time!)
  return `${start} - ${end}`
})

// 格式化单个时间（秒数转为 mm:ss 格式）
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 格式化时间点
const formatTimestamp = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

import { computed } from 'vue'
</script>
