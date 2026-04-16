<template>
  <div class="min-h-screen pl-0 md:pl-16 pb-24 md:pb-0">
    <div class="max-w-7xl mx-auto px-4 py-6">
      <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-6">数据库管理</h1>

      <!-- Tab 切换 -->
      <div class="flex gap-1 mb-6 border-b border-[var(--border-color)]">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          @click="activeTab = tab.key"
          :class="[
            'px-4 py-2 text-sm font-medium border-b-2 transition-colors -mb-px',
            activeTab === tab.key
              ? 'border-indigo-500 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          ]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab 内容 -->
      <AdminDashboard v-if="activeTab === 'overview'" />
      <TableBrowser v-else-if="activeTab === 'tables'" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AdminDashboard from '../components/admin/AdminDashboard.vue'
import TableBrowser from '../components/admin/TableBrowser.vue'

const tabs = [
  { key: 'overview', label: '概览' },
  { key: 'tables', label: '表浏览' },
]

const activeTab = ref('overview')
</script>
