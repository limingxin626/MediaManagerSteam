<template>
  <div class="shrink-0 border-b border-[var(--border-color)] bg-[var(--color-primary-500)]/5">
    <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-2">
      <div class="max-w-3xl mx-auto">
        <!-- View mode -->
        <div v-if="!editing" class="flex items-start gap-2">
          <svg class="w-4 h-4 mt-1 shrink-0 text-[var(--color-primary-500)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="text-sm font-semibold text-gray-900 dark:text-white truncate">{{ issue.title }}</span>
              <span class="text-xs text-[var(--text-muted)] shrink-0">{{ issue.message_count }} 条</span>
            </div>
            <div
              v-if="issue.description"
              ref="descEl"
              class="mt-1 text-xs text-[var(--text-secondary)] markdown-body"
              :class="{ 'line-clamp-2': !expanded }"
              v-html="renderedDescription"
            />
            <div v-else class="mt-1 text-xs text-[var(--text-muted)] italic">无描述</div>
            <button
              v-if="issue.description && canExpand"
              @click="expanded = !expanded"
              class="mt-0.5 text-xs text-[var(--color-primary-500)] hover:underline"
            >
              {{ expanded ? '收起' : '展开' }}
            </button>
          </div>
          <div class="flex items-center gap-1 shrink-0">
            <button @click="startEdit" class="p-1 rounded text-gray-400 hover:text-[var(--color-primary-500)] hover:bg-gray-100 dark:hover:bg-white/10" title="编辑">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button @click="$emit('clear')" class="p-1 rounded text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-white/10" title="取消筛选">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <!-- Edit mode -->
        <div v-else class="flex flex-col gap-2">
          <input
            v-model="draftTitle"
            placeholder="Issue 标题"
            class="w-full text-sm font-semibold bg-transparent border-b border-[var(--color-primary-500)] text-gray-900 dark:text-white focus:outline-none py-1"
          />
          <VditorEditor ref="editorRef" v-model="draftDescription" placeholder="描述 (Markdown)" />
          <div class="flex items-center justify-end gap-2">
            <button @click="cancelEdit" class="px-3 py-1 text-xs rounded text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10">
              取消
            </button>
            <button @click="commitEdit" :disabled="saving" class="px-3 py-1 text-xs rounded bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)] disabled:opacity-50">
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from 'vue'
import type { Issue } from '../types'
import { renderMarkdown } from '../utils/markdown'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import VditorEditor from './VditorEditor.vue'

const props = defineProps<{ issue: Issue }>()
const emit = defineEmits<{
  clear: []
  updated: [issue: Issue]
}>()

const toast = useToast()

const expanded = ref(false)
const descEl = ref<HTMLElement | null>(null)
const canExpand = ref(false)

const renderedDescription = computed(() =>
  props.issue.description ? renderMarkdown(props.issue.description) : ''
)

watch(
  () => [props.issue.id, props.issue.description] as const,
  async () => {
    expanded.value = false
    await nextTick()
    const el = descEl.value
    canExpand.value = !!el && el.scrollHeight > el.clientHeight + 1
  },
  { immediate: true }
)

// --- Edit mode ---
const editing = ref(false)
const draftTitle = ref('')
const draftDescription = ref('')
const saving = ref(false)
const editorRef = ref<InstanceType<typeof VditorEditor> | null>(null)

function startEdit() {
  draftTitle.value = props.issue.title
  draftDescription.value = props.issue.description ?? ''
  editing.value = true
  nextTick(() => editorRef.value?.focus())
}

function cancelEdit() {
  editing.value = false
}

async function commitEdit() {
  const title = draftTitle.value.trim()
  if (!title) {
    toast.error('标题不能为空')
    return
  }
  saving.value = true
  try {
    const updated = await api.patch<Issue>(`/issues/${props.issue.id}`, {
      title,
      description: draftDescription.value || null,
    })
    emit('updated', updated)
    editing.value = false
    toast.success('已更新')
  } catch {
    toast.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>
