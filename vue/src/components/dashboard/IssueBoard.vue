<template>
  <section class="bg-white/30 dark:bg-[var(--bg-card)] backdrop-blur rounded-2xl p-4 border border-[var(--border-color)]">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-base font-bold text-gray-900 dark:text-white">🎯 Issue 看板</h2>
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

    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-3">
      <IssueColumn
        status="doing"
        title="进行中"
        :issues="board.doing"
        @add="handleAdd"
        @rename="handleRename"
        @delete="handleDelete"
        @changed="(e) => onChange('doing', e)"
      />
      <IssueColumn
        status="done"
        title="已完成"
        :issues="board.done"
        @add="handleAdd"
        @rename="handleRename"
        @delete="handleDelete"
        @changed="(e) => onChange('done', e)"
      />
      <IssueColumn
        status="archived"
        title="已归档"
        :issues="board.archived"
        @add="handleAdd"
        @rename="handleRename"
        @delete="handleDelete"
        @changed="(e) => onChange('archived', e)"
      />
      <IssueColumn
        status="abandoned"
        title="已放弃"
        :issues="board.abandoned"
        @add="handleAdd"
        @rename="handleRename"
        @delete="handleDelete"
        @changed="(e) => onChange('abandoned', e)"
      />
    </div>
  </section>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { api } from '../../composables/useApi'
import { useToast } from '../../composables/useToast'
import { useConfirm } from '../../composables/useConfirm'
import IssueColumn from './IssueColumn.vue'
import type { Issue, IssueBoard as IssueBoardData, IssueStatus } from '../../types'

const toast = useToast()
const { confirm } = useConfirm()

const loading = ref(true)
const board = reactive<IssueBoardData>({ doing: [], done: [], archived: [], abandoned: [] })

async function reload() {
  loading.value = true
  try {
    const data = await api.get<IssueBoardData>('/issues')
    board.doing = data.doing
    board.done = data.done
    board.archived = data.archived
    board.abandoned = data.abandoned
  } catch (e) {
    toast.error(`加载 Issue 失败：${(e as Error).message}`)
  } finally {
    loading.value = false
  }
}

async function handleAdd(title: string) {
  try {
    const created = await api.post<Issue>('/issues', { title })
    board.doing.push(created)
  } catch (e) {
    toast.error(`新增失败：${(e as Error).message}`)
  }
}

async function handleRename(issue: Issue, title: string) {
  const original = issue.title
  issue.title = title
  try {
    await api.patch<Issue>(`/issues/${issue.id}`, { title })
  } catch (e) {
    issue.title = original
    toast.error(`修改失败：${(e as Error).message}`)
  }
}

async function handleDelete(issue: Issue) {
  const ok = await confirm({ title: '删除', message: `确定删除「${issue.title}」？`, danger: true })
  if (!ok) return
  try {
    await api.del(`/issues/${issue.id}`)
    await reload()
  } catch (e) {
    toast.error(`删除失败：${(e as Error).message}`)
  }
}

async function onChange(status: IssueStatus, event: any) {
  const item: Issue | undefined = event.added?.element ?? event.moved?.element
  const newIndex: number | undefined = event.added?.newIndex ?? event.moved?.newIndex
  if (!item || newIndex === undefined) return
  try {
    await api.patch<Issue>(`/issues/${item.id}/move`, { status, position: newIndex })
  } catch (e) {
    toast.error(`移动失败：${(e as Error).message}`)
    await reload()
  }
}

onMounted(reload)
</script>
