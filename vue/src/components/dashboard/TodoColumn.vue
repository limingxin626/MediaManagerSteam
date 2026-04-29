<template>
  <div class="flex flex-col bg-white/40 dark:bg-black/20 border border-[var(--border-color)] rounded-xl p-3 min-h-[200px]">
    <div class="flex items-center justify-between mb-2 px-1">
      <h3 class="text-sm font-semibold text-gray-700 dark:text-gray-200">
        {{ title }}
        <span class="ml-1 text-xs text-gray-400">{{ todos.length }}</span>
      </h3>
    </div>

    <draggable
      :list="todos"
      group="todos"
      :animation="150"
      item-key="id"
      ghost-class="opacity-40"
      class="flex-1 flex flex-col gap-2 min-h-[40px]"
      @change="onChange"
    >
      <template #item="{ element }">
        <TodoCard
          :todo="element"
          @rename="(t, title) => $emit('rename', t, title)"
          @delete="(t) => $emit('delete', t)"
        />
      </template>
    </draggable>

    <form
      v-if="status === 'pending'"
      @submit.prevent="addNew"
      class="mt-2"
    >
      <input
        v-model="newTitle"
        placeholder="+ 新增待办，回车提交"
        class="w-full text-sm bg-transparent border border-dashed border-[var(--border-color)] rounded-md px-2 py-1.5 text-gray-700 dark:text-gray-200 placeholder:text-gray-400 focus:outline-none focus:border-[var(--color-primary-500)]"
      />
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
// @ts-expect-error - vuedraggable v4 lacks bundled TS types
import draggable from 'vuedraggable'
import TodoCard from './TodoCard.vue'
import type { Todo, TodoStatus } from '../../types'

defineProps<{
  status: TodoStatus
  title: string
  todos: Todo[]
}>()

const emit = defineEmits<{
  add: [title: string]
  rename: [todo: Todo, title: string]
  delete: [todo: Todo]
  changed: [event: any]
}>()

const newTitle = ref('')

function addNew() {
  const t = newTitle.value.trim()
  if (!t) return
  newTitle.value = ''
  emit('add', t)
}

function onChange(event: any) {
  emit('changed', event)
}
</script>
