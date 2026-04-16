<template>
  <div class="flex gap-4 min-h-[60vh]">
    <!-- 左侧表列表 -->
    <div class="w-40 shrink-0">
      <div class="space-y-1">
        <button
          v-for="t in tableDefs"
          :key="t.name"
          @click="selectTable(t)"
          :class="[
            'w-full text-left px-3 py-2 rounded-lg text-sm transition-colors',
            activeTable?.name === t.name
              ? 'bg-indigo-600 text-white'
              : 'text-gray-600 dark:text-gray-300 hover:bg-[var(--bg-secondary)]'
          ]"
        >
          {{ t.label }}
        </button>
      </div>
    </div>

    <!-- 右侧内容 -->
    <div class="flex-1 min-w-0">
      <div v-if="activeTable">
        <!-- 搜索栏 -->
        <div class="flex items-center gap-3 mb-4">
          <input
            v-model="searchText"
            @keydown.enter="doSearch"
            type="text"
            placeholder="搜索..."
            class="flex-1 max-w-xs px-3 py-1.5 text-sm rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          />
          <button
            @click="doSearch"
            class="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
          >
            搜索
          </button>
          <button
            v-if="searchText"
            @click="clearSearch"
            class="px-3 py-1.5 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
          >
            清除
          </button>
        </div>

        <!-- 表格 -->
        <div class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] overflow-hidden">
          <DataTable
            :columns="activeTable.columns"
            :rows="rows"
            @select="openDrawer"
          />
        </div>

        <!-- 分页 -->
        <div class="flex items-center justify-between mt-4">
          <span class="text-sm text-gray-400">
            {{ rows.length }} 条记录{{ hasMore ? ' (更多)' : '' }}
          </span>
          <div class="flex gap-2">
            <button
              :disabled="cursorHistory.length === 0"
              @click="prevPage"
              class="px-3 py-1.5 text-sm rounded-lg border border-[var(--border-color)] text-gray-600 dark:text-gray-300 hover:bg-[var(--bg-secondary)] disabled:opacity-30 transition-colors"
            >
              上一页
            </button>
            <button
              :disabled="!hasMore"
              @click="nextPage"
              class="px-3 py-1.5 text-sm rounded-lg border border-[var(--border-color)] text-gray-600 dark:text-gray-300 hover:bg-[var(--bg-secondary)] disabled:opacity-30 transition-colors"
            >
              下一页
            </button>
          </div>
        </div>
      </div>

      <div v-else class="flex items-center justify-center h-60 text-gray-400">
        选择左侧的表开始浏览
      </div>
    </div>

    <!-- 详情抽屉 -->
    <RecordDrawer
      v-if="drawerRecord"
      :record="drawerRecord"
      :table-def="activeTable!"
      @close="drawerRecord = null"
      @saved="onRecordSaved"
      @deleted="onRecordDeleted"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DataTable from './DataTable.vue'
import RecordDrawer from './RecordDrawer.vue'
import { tableDefs, type TableDef } from './tableConfig'

const activeTable = ref<TableDef | null>(null)
const rows = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const hasMore = ref(false)
const nextCursor = ref<string | null>(null)
const cursorHistory = ref<(string | null)[]>([])
const searchText = ref('')
const activeSearch = ref('')
const drawerRecord = ref<Record<string, unknown> | null>(null)

async function fetchData(cursor: string | null = null) {
  if (!activeTable.value) return
  loading.value = true
  try {
    const res = await activeTable.value.apiList({
      cursor,
      limit: 20,
      search: activeSearch.value || undefined,
    })
    rows.value = res.items
    nextCursor.value = res.next_cursor
    hasMore.value = res.has_more
  } finally {
    loading.value = false
  }
}

function selectTable(t: TableDef) {
  activeTable.value = t
  cursorHistory.value = []
  nextCursor.value = null
  searchText.value = ''
  activeSearch.value = ''
  drawerRecord.value = null
  fetchData()
}

function nextPage() {
  if (!hasMore.value || !nextCursor.value) return
  cursorHistory.value.push(nextCursor.value)
  // 记录当前的 cursor 以便返回
  // 我们需要在 fetchData 之前 push 上一页的起始 cursor
  // 实际上我们需要维护的是每一页的起始 cursor
  fetchData(nextCursor.value)
}

function prevPage() {
  if (cursorHistory.value.length === 0) return
  cursorHistory.value.pop()
  const prev = cursorHistory.value.length > 0
    ? cursorHistory.value[cursorHistory.value.length - 1]
    : null
  fetchData(prev)
}

function doSearch() {
  activeSearch.value = searchText.value.trim()
  cursorHistory.value = []
  nextCursor.value = null
  fetchData()
}

function clearSearch() {
  searchText.value = ''
  activeSearch.value = ''
  cursorHistory.value = []
  nextCursor.value = null
  fetchData()
}

function openDrawer(row: Record<string, unknown>) {
  drawerRecord.value = { ...row }
}

function onRecordSaved() {
  drawerRecord.value = null
  fetchData(cursorHistory.value.length > 0 ? cursorHistory.value[cursorHistory.value.length - 1] : null)
}

function onRecordDeleted() {
  drawerRecord.value = null
  fetchData(cursorHistory.value.length > 0 ? cursorHistory.value[cursorHistory.value.length - 1] : null)
}
</script>
