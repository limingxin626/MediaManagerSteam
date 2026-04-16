<template>
  <div>
    <!-- 刷新按钮 -->
    <div class="flex justify-end mb-4">
      <button
        @click="fetchStats"
        :disabled="loading"
        class="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
      >
        {{ loading ? '加载中...' : '刷新' }}
      </button>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6" v-if="stats">
      <div
        v-for="(count, table) in stats.table_counts"
        :key="table"
        class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-4"
      >
        <div class="text-sm text-gray-500 dark:text-gray-400">{{ tableNames[table] || table }}</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ count.toLocaleString() }}</div>
      </div>
    </div>

    <!-- 存储统计 -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6" v-if="stats">
      <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-4">
        <div class="text-sm text-gray-500 dark:text-gray-400">媒体文件数</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ stats.storage.total_files.toLocaleString() }}</div>
      </div>
      <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-4">
        <div class="text-sm text-gray-500 dark:text-gray-400">媒体总大小</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ formatSize(stats.storage.total_size) }}</div>
      </div>
      <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-4">
        <div class="text-sm text-gray-500 dark:text-gray-400">数据库文件</div>
        <div class="text-2xl font-bold text-gray-900 dark:text-white mt-1">{{ formatSize(stats.db_size) }}</div>
      </div>
    </div>

    <!-- 最近消息 -->
    <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-4" v-if="stats">
      <h3 class="text-sm font-medium text-gray-500 dark:text-gray-400 mb-3">最近消息</h3>
      <div class="space-y-2">
        <div
          v-for="msg in stats.recent_messages"
          :key="msg.id"
          class="flex items-start gap-3 py-2 border-b border-[var(--border-color)] last:border-0"
        >
          <span class="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap mt-0.5">
            {{ msg.created_at ? new Date(msg.created_at).toLocaleString('zh-CN') : '-' }}
          </span>
          <span class="text-sm text-gray-700 dark:text-gray-300 line-clamp-1">
            {{ msg.text || '(无文本)' }}
          </span>
          <span class="text-xs text-gray-400 ml-auto">#{{ msg.id }}</span>
        </div>
        <div v-if="stats.recent_messages.length === 0" class="text-sm text-gray-400">暂无消息</div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading && !stats" class="text-center py-12 text-gray-400">加载中...</div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../../composables/useApi'
import type { AdminStats } from '../../types'

const stats = ref<AdminStats | null>(null)
const loading = ref(false)

const tableNames: Record<string, string> = {
  message: 'Message',
  media: 'Media',
  actor: 'Actor',
  tag: 'Tag',
  message_media: 'MessageMedia',
  message_tag: 'MessageTag',
  sync_log: 'SyncLog',
}

function formatSize(bytes: number): string {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return (bytes / Math.pow(1024, i)).toFixed(1) + ' ' + units[i]
}

async function fetchStats() {
  loading.value = true
  try {
    stats.value = await api.get<AdminStats>('/admin/stats')
  } finally {
    loading.value = false
  }
}

onMounted(fetchStats)
</script>
