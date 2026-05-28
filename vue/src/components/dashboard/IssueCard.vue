<template>
  <div
    class="group bg-white dark:bg-[#3d3d3d] border border-[var(--border-color)] rounded-lg px-3 py-2 shadow-sm hover:shadow transition-shadow cursor-grab active:cursor-grabbing"
  >
    <div v-if="!editing" class="flex items-start gap-2">
      <div class="flex-1 min-w-0">
        <div
          @dblclick="startEdit"
          class="text-sm text-gray-900 dark:text-gray-100 break-words select-none"
          :class="{ 'line-through text-gray-400 dark:text-gray-500': issue.status === 'done' || issue.status === 'abandoned' }"
        >
          {{ issue.title }}
        </div>
        <div v-if="issue.message_count > 0" class="mt-1 text-xs text-gray-400 dark:text-gray-500">
          {{ issue.message_count }} 条消息
        </div>
      </div>
      <button
        @click="$emit('delete', issue)"
        class="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 text-sm leading-none transition-opacity"
        title="删除"
      >
        ✕
      </button>
    </div>
    <input
      v-else
      ref="inputRef"
      v-model="draft"
      @keydown.enter.prevent="commit"
      @keydown.esc.prevent="cancel"
      @blur="commit"
      class="w-full text-sm bg-transparent border-b border-[var(--color-primary-500)] text-gray-900 dark:text-gray-100 focus:outline-none"
    />
  </div>
</template>

<script setup lang="ts">
import { nextTick, ref } from 'vue'
import type { Issue } from '../../types'

const props = defineProps<{ issue: Issue }>()
const emit = defineEmits<{
  rename: [issue: Issue, title: string]
  delete: [issue: Issue]
}>()

const editing = ref(false)
const draft = ref('')
const inputRef = ref<HTMLInputElement | null>(null)

function startEdit() {
  draft.value = props.issue.title
  editing.value = true
  nextTick(() => inputRef.value?.focus())
}

function commit() {
  if (!editing.value) return
  const title = draft.value.trim()
  editing.value = false
  if (title && title !== props.issue.title) {
    emit('rename', props.issue, title)
  }
}

function cancel() {
  editing.value = false
}
</script>
