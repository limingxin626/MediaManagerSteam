<template>
  <Teleport to="body">
    <div
      v-if="visible"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4"
      @click.self="close"
    >
      <div class="bg-gray-950 rounded-2xl border border-gray-800 w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-800">
          <h2 class="text-lg font-semibold text-white">选择图片作为预览</h2>
          <button @click="close" class="text-gray-400 hover:text-white">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Grid -->
        <div class="flex-1 overflow-y-auto p-4">
          <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
            <button
              v-for="item in items"
              :key="item.id"
              type="button"
              @click="selectedId = item.id"
              :class="[
                'relative aspect-square rounded-lg overflow-hidden border-2 transition-colors',
                selectedId === item.id ? 'border-indigo-500' : 'border-transparent hover:border-gray-700'
              ]"
            >
              <img
                :src="resolveUrl(item.thumb_url)"
                :alt="`media-${item.id}`"
                class="w-full h-full object-cover"
                loading="lazy"
              />
              <span
                v-if="selectedId === item.id"
                class="absolute top-1 right-1 bg-indigo-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs"
              >
                ✓
              </span>
            </button>
          </div>
          <div ref="sentinel" class="h-8 flex items-center justify-center text-gray-500 text-xs">
            <span v-if="loading">加载中...</span>
            <span v-else-if="!hasMore && items.length">没有更多了</span>
            <span v-else-if="!items.length && !loading">暂无图片</span>
          </div>
        </div>

        <!-- Footer -->
        <div class="px-6 py-4 border-t border-gray-800 flex items-center justify-end gap-3">
          <button
            @click="close"
            class="px-4 py-2 rounded-lg text-gray-300 hover:bg-gray-800 transition-colors"
          >
            取消
          </button>
          <button
            :disabled="selectedId == null"
            @click="confirm"
            class="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            确定
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import type { Media } from '../types'
import { api, useInfiniteScroll } from '../composables/useApi'
import { resolveUrl } from '../utils/media'

const props = defineProps<{ visible: boolean }>()
const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', mediaId: number): void
}>()

const sentinel = ref<HTMLElement | null>(null)
const selectedId = ref<number | null>(null)

const { items, loading, hasMore, reset, setupObserver } = useInfiniteScroll<Media>({
  fetchFn: ({ cursor, limit }) =>
    api.get('/media', { cursor: cursor ?? undefined, limit, type: 'image' }),
  sentinel,
  limit: 30,
})

watch(
  () => props.visible,
  async (v) => {
    if (v) {
      selectedId.value = null
      await reset()
      await nextTick()
      setupObserver()
    }
  },
)

const close = () => emit('close')
const confirm = () => {
  if (selectedId.value != null) emit('select', selectedId.value)
}
</script>
