<template>
  <section class="bg-white/30 dark:bg-black/20 backdrop-blur rounded-2xl p-4 border border-[var(--border-color)]">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-base font-bold text-gray-900 dark:text-white">🖼️ 最近媒体</h2>
      <router-link to="/media" class="text-xs text-gray-500 hover:text-[var(--color-primary-500)]">查看全部 →</router-link>
    </div>
    <div v-if="loading" class="text-center py-6 text-gray-500 text-sm">加载中…</div>
    <div v-else-if="!items.length" class="text-center py-6 text-gray-400 text-sm italic">暂无媒体</div>
    <div v-else class="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-6 gap-2">
      <div
        v-for="(m, idx) in items"
        :key="m.id"
        class="aspect-square overflow-hidden rounded-lg bg-gray-200 dark:bg-gray-700 hover:ring-2 hover:ring-[var(--color-primary-500)] transition cursor-pointer"
        @click="openPreview(idx)"
      >
        <img
          :src="resolveThumb(m)"
          :alt="`media-${m.id}`"
          class="w-full h-full object-cover"
          loading="lazy"
        />
      </div>
    </div>

    <Teleport to="body">
      <MediaPreview
        :is-open="previewOpen"
        :items="previewItems"
        :start-index="previewStartIndex"
        @close="previewOpen = false"
        @media-deleted="handleDeleted"
      />
    </Teleport>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../../composables/useApi'
import { useToast } from '../../composables/useToast'
import { resolveThumb } from '../../utils/media'
import MediaPreview from '../MediaPreview.vue'
import type { Media, CursorResponse } from '../../types'

const toast = useToast()
const loading = ref(true)
const items = ref<Media[]>([])

const previewOpen = ref(false)
const previewItems = ref<any[]>([])
const previewStartIndex = ref(0)

onMounted(async () => {
  try {
    const data = await api.get<CursorResponse<Media>>('/media', { limit: 12 })
    items.value = data.items
  } catch (e) {
    toast.error(`加载最近媒体失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
})

function openPreview(idx: number) {
  previewItems.value = items.value.map(m => ({
    id: m.id,
    file_path: m.file_path,
    mime_type: m.mime_type,
    duration_ms: m.duration_ms,
    thumb_url: m.thumb_url,
    thumb_path: m.thumb_path,
    starred: m.starred,
  }))
  previewStartIndex.value = idx
  previewOpen.value = true
}

function handleDeleted(mediaId: number) {
  items.value = items.value.filter(m => m.id !== mediaId)
}
</script>
