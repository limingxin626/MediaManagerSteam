<template>
  <section class="bg-white/30 dark:bg-black/20 backdrop-blur rounded-2xl p-4 border border-[var(--border-color)]">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-base font-bold text-gray-900 dark:text-white">🖼️ 最近媒体</h2>
      <router-link to="/media" class="text-xs text-gray-500 hover:text-[var(--color-primary-500)]">查看全部 →</router-link>
    </div>
    <div v-if="loading" class="text-center py-6 text-gray-500 text-sm">加载中…</div>
    <div v-else-if="!items.length" class="text-center py-6 text-gray-400 text-sm italic">暂无媒体</div>
    <div v-else class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2">
      <router-link
        v-for="m in items"
        :key="m.id"
        :to="`/media/${m.id}`"
        class="aspect-square overflow-hidden rounded-lg bg-gray-200 dark:bg-gray-700 hover:ring-2 hover:ring-[var(--color-primary-500)] transition"
      >
        <img
          :src="m.thumb_url"
          :alt="`media-${m.id}`"
          class="w-full h-full object-cover"
          loading="lazy"
        />
      </router-link>
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../../composables/useApi'
import { useToast } from '../../composables/useToast'

interface MediaThumb {
  id: number
  thumb_url: string
}

interface CursorResponse<T> {
  items: T[]
  next_cursor: string | null
  has_more: boolean
}

const toast = useToast()
const loading = ref(true)
const items = ref<MediaThumb[]>([])

onMounted(async () => {
  try {
    const data = await api.get<CursorResponse<MediaThumb>>('/media', { limit: 12 })
    items.value = data.items
  } catch (e) {
    toast.error(`加载最近媒体失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
})
</script>
