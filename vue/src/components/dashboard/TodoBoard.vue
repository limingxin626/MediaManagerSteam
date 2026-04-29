<template>
  <section class="bg-white/30 dark:bg-black/20 backdrop-blur rounded-2xl p-4 border border-[var(--border-color)]">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-base font-bold text-gray-900 dark:text-white">📋 Todo 看板</h2>
      <button
        v-if="!loading"
        @click="reload"
        class="text-xs text-gray-500 dark:text-gray-400 hover:text-[var(--color-primary-500)]"
        title="刷新"
      >
        ↻
      </button>
    </div>

    <div v-if="loading" class="text-center py-8 text-gray-500 dark:text-gray-400 text-sm">加载中…</div>

    <div v-else class="grid grid-cols-1 md:grid-cols-3 gap-3">
      <TodoColumn
        status="pending"
        title="待办"
        :todos="board.pending"
        @add="handleAdd"
        @rename="handleRename"
        @delete="handleDelete"
        @changed="(e) => onChange('pending', e)"
      />
      <TodoColumn
        status="doing"
        title="进行中"
        :todos="board.doing"
        @add="handleAdd"
        @rename="handleRename"
        @delete="handleDelete"
        @changed="(e) => onChange('doing', e)"
      />
      <TodoColumn
        status="done"
        title="已完成"
        :todos="board.done"
        @add="handleAdd"
        @rename="handleRename"
        @delete="handleDelete"
        @changed="(e) => onChange('done', e)"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api } from '../../composables/useApi'
import { useToast } from '../../composables/useToast'
import { useConfirm } from '../../composables/useConfirm'
import TodoColumn from './TodoColumn.vue'
import type { Todo, TodoBoard as TodoBoardData, TodoStatus } from '../../types'

const toast = useToast()
const { confirm } = useConfirm()

const loading = ref(true)
const board = reactive<TodoBoardData>({ pending: [], doing: [], done: [] })

async function reload() {
  loading.value = true
  try {
    const data = await api.get<TodoBoardData>('/todos')
    board.pending = data.pending
    board.doing = data.doing
    board.done = data.done
  } catch (e) {
    toast.error(`加载 Todo 失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
}

async function handleAdd(title: string) {
  try {
    const created = await api.post<Todo>('/todos', { title })
    board.pending.push(created)
  } catch (e) {
    toast.error(`新增失败：${(e as Error).message}`)
  }
}

async function handleRename(todo: Todo, title: string) {
  const original = todo.title
  todo.title = title
  try {
    await api.patch<Todo>(`/todos/${todo.id}`, { title })
  } catch (e) {
    todo.title = original
    toast.error(`修改失败：${(e as Error).message}`)
  }
}

async function handleDelete(todo: Todo) {
  const ok = await confirm({ title: '删除', message: `确定删除「${todo.title}」？`, danger: true })
  if (!ok) return
  try {
    await api.del(`/todos/${todo.id}`)
    await reload()
  } catch (e) {
    toast.error(`删除失败：${(e as Error).message}`)
  }
}

async function onChange(status: TodoStatus, event: any) {
  const item: Todo | undefined = event.added?.element ?? event.moved?.element
  const newIndex: number | undefined = event.added?.newIndex ?? event.moved?.newIndex
  if (!item || newIndex === undefined) return
  try {
    await api.patch<Todo>(`/todos/${item.id}/move`, { status, position: newIndex })
  } catch (e) {
    toast.error(`移动失败：${(e as Error).message}`)
    await reload()
  }
}

onMounted(reload)
</script>
