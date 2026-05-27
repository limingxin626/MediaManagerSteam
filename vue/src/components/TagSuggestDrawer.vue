<template>
  <Transition name="fade">
    <div v-if="isOpen" class="fixed inset-0 z-[150]">
      <div class="absolute inset-0 bg-black/60 backdrop-blur-sm" @click="close"></div>
      <div class="absolute right-0 top-0 bottom-0 w-full sm:max-w-md bg-[var(--bg-primary)] dark:bg-gray-900 shadow-2xl flex flex-col">
        <div class="flex items-center justify-between p-4 border-b border-[var(--border-color)]">
          <h3 class="text-base font-semibold text-[var(--text-primary)]">智能 tag 建议</h3>
          <button @click="close" class="p-1.5 rounded-full hover:bg-white/10 text-[var(--text-muted)]">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div class="flex-1 overflow-y-auto px-4 py-3">
          <div v-if="loading" class="flex items-center justify-center py-12 text-sm text-[var(--text-muted)]">
            正在分析图像...
          </div>
          <div v-else-if="error" class="py-8 px-2 text-sm text-red-500">
            {{ error }}
          </div>
          <div v-else-if="!suggestions.length" class="py-12 text-center text-sm text-[var(--text-muted)]">
            未生成建议
          </div>
          <ul v-else class="flex flex-col gap-1.5">
            <li
              v-for="sug in suggestions"
              :key="sug.tag_id"
              @click="toggle(sug.tag_id)"
              class="flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors"
              :class="selected.has(sug.tag_id)
                ? 'bg-[var(--color-primary-600)]/25 ring-1 ring-[var(--color-primary-500)]'
                : 'hover:bg-white/5'"
            >
              <input
                type="checkbox"
                :checked="selected.has(sug.tag_id)"
                @click.stop="toggle(sug.tag_id)"
                class="h-4 w-4 rounded border-gray-500 text-[var(--color-primary-500)]"
              />
              <div class="flex-1 min-w-0">
                <div class="text-sm text-[var(--text-primary)] truncate">#{{ sug.name }}</div>
                <div class="mt-1 h-1 bg-gray-700/40 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-[var(--color-primary-500)]"
                    :style="{ width: scoreToWidth(sug.score) + '%' }"
                  ></div>
                </div>
              </div>
              <span class="text-xs text-[var(--text-muted)] shrink-0 tabular-nums">{{ sug.score.toFixed(3) }}</span>
            </li>
          </ul>
        </div>

        <div class="p-4 border-t border-[var(--border-color)] flex items-center justify-between">
          <div class="text-xs text-[var(--text-muted)]">已选 {{ selected.size }} 个</div>
          <div class="flex gap-2">
            <button
              @click="close"
              class="px-3 py-1.5 rounded-md text-sm bg-gray-700/30 text-[var(--text-primary)] hover:bg-gray-700/50"
            >取消</button>
            <button
              @click="confirm"
              :disabled="applying || selected.size === 0"
              class="px-3 py-1.5 rounded-md text-sm bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)] disabled:opacity-40"
            >{{ applying ? '应用中...' : '应用' }}</button>
          </div>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import type { TagSuggestion, TagItem } from '../types'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'

const toast = useToast()

interface Props {
  isOpen: boolean
  mediaId: number | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  close: []
  'tags-applied': [mediaId: number, tags: TagItem[]]
}>()

const suggestions = ref<TagSuggestion[]>([])
const selected = ref<Set<number>>(new Set())
const loading = ref(false)
const applying = ref(false)
const error = ref<string | null>(null)

function scoreToWidth(score: number): number {
  // CLIP cosine 一般落在 0.15~0.35，做个简单线性映射
  const v = Math.max(0, Math.min(1, (score - 0.1) / 0.3))
  return Math.round(v * 100)
}

function toggle(id: number) {
  const next = new Set(selected.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selected.value = next
}

async function load() {
  if (props.mediaId == null) return
  loading.value = true
  error.value = null
  suggestions.value = []
  selected.value = new Set()
  try {
    const data = await api.post<TagSuggestion[]>('/smart/tags/suggest', {
      media_id: props.mediaId,
      top_k: 12,
    })
    suggestions.value = data
  } catch (e: any) {
    error.value = e?.message || '加载建议失败'
  } finally {
    loading.value = false
  }
}

async function confirm() {
  if (props.mediaId == null || selected.value.size === 0) return
  applying.value = true
  try {
    const tags = await api.post<TagItem[]>('/smart/tags/apply', {
      media_id: props.mediaId,
      tag_ids: Array.from(selected.value),
    })
    toast.success(`已添加 ${selected.value.size} 个 tag`)
    emit('tags-applied', props.mediaId, tags)
    emit('close')
  } catch (e: any) {
    toast.error(e?.message || '应用 tag 失败')
  } finally {
    applying.value = false
  }
}

function close() {
  emit('close')
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) load()
  },
)
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
