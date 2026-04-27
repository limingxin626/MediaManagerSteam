<template>
  <div class="h-screen flex flex-col">
    <div class="max-w-5xl w-full mx-auto px-4 pt-6 flex flex-col flex-1 min-h-0">
      <!-- 顶部栏（固定不滚动） -->
      <div class="flex items-center justify-between mb-4 shrink-0">
        <h1 class="text-xl font-bold text-gray-900 dark:text-white">主页</h1>
        <div class="flex items-center gap-2">
          <template v-if="mode === 'edit'">
            <button
              @click="cancelEdit"
              class="px-3 py-1.5 text-sm rounded-lg border border-[var(--border-color)] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              :disabled="saving"
            >
              取消
            </button>
            <button
              @click="save"
              class="px-3 py-1.5 text-sm rounded-lg bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)] disabled:opacity-50 transition-colors"
              :disabled="saving"
            >
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </template>
          <button
            v-else-if="!loading"
            @click="enterEdit"
            class="px-3 py-1.5 text-sm rounded-lg border border-[var(--border-color)] text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          >
            编辑
          </button>
        </div>
      </div>

      <!-- 加载态 -->
      <div v-if="loading" class="text-center py-12 text-gray-500 dark:text-gray-400">
        加载中…
      </div>

      <!-- 编辑模式 -->
      <textarea
        v-else-if="mode === 'edit'"
        v-model="draft"
        ref="textareaRef"
        class="w-full flex-1 min-h-0 mb-24 md:mb-8 p-4 rounded-lg bg-white dark:bg-gray-900 border border-[var(--border-color)] text-gray-900 dark:text-gray-100 font-mono text-sm leading-relaxed focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)] resize-none"
        spellcheck="false"
      ></textarea>

      <!-- 阅读模式 -->
      <div
        v-else
        class="prose dark:prose-invert max-w-none p-4 rounded-lg bg-white/60 dark:bg-black/20 border border-[var(--border-color)] flex-1 min-h-0 overflow-y-auto mb-24 md:mb-8"
      >
        <div v-if="content.trim()" v-html="renderedContent"></div>
        <p v-else class="text-gray-400 dark:text-gray-500 italic">（空白，点击右上角「编辑」开始）</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, onMounted, computed } from 'vue'
import { api, ApiError } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { renderMarkdown } from '../utils/markdown'

interface DashboardPayload {
  content: string
  mtime: number
}

const toast = useToast()

const mode = ref<'view' | 'edit'>('view')
const loading = ref(true)
const saving = ref(false)
const content = ref('')
const mtime = ref(0)
const draft = ref('')
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const renderedContent = computed(() => renderMarkdown(content.value))

async function load() {
  loading.value = true
  try {
    const data = await api.get<DashboardPayload>('/api/dashboard')
    content.value = data.content
    mtime.value = data.mtime
  } catch (e) {
    toast.error(`加载主页失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
}

function enterEdit() {
  draft.value = content.value
  mode.value = 'edit'
  nextTick(() => textareaRef.value?.focus())
}

function cancelEdit() {
  draft.value = ''
  mode.value = 'view'
}

async function save() {
  saving.value = true
  try {
    const data = await api.put<DashboardPayload>('/api/dashboard', {
      content: draft.value,
      if_match: mtime.value,
    })
    content.value = data.content
    mtime.value = data.mtime
    mode.value = 'view'
    toast.success('已保存')
  } catch (e) {
    if (e instanceof ApiError && e.status === 409) {
      // 后端在 detail 里塞了 {message, current_mtime, current_content}
      // useApi 会把 detail 当作 message string 抛上来；这里直接重新 load
      toast.error('文件已被外部修改，已重新加载')
      await load()
      mode.value = 'view'
      draft.value = ''
    } else {
      toast.error(`保存失败：${(e as Error).message}`)
    }
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>
