<template>
  <div class="overflow-x-auto">
    <table class="w-full text-sm text-left">
      <thead class="text-xs text-gray-500 dark:text-gray-400 border-b border-[var(--border-color)]">
        <tr>
          <th v-for="col in columns" :key="col.key" class="px-3 py-2 font-medium whitespace-nowrap">
            {{ col.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(row, i) in rows"
          :key="i"
          @click="$emit('select', row)"
          class="border-b border-[var(--border-color)] hover:bg-[var(--bg-secondary)] cursor-pointer transition-colors"
        >
          <td v-for="col in columns" :key="col.key" class="px-3 py-2 whitespace-nowrap text-gray-700 dark:text-gray-300">
            <template v-if="col.type === 'datetime'">
              {{ formatDatetime(row[col.key]) }}
            </template>
            <template v-else-if="col.truncate && typeof row[col.key] === 'string' && (row[col.key] as string).length > col.truncate">
              {{ (row[col.key] as string).slice(0, col.truncate) }}...
            </template>
            <template v-else>
              {{ row[col.key] ?? '-' }}
            </template>
          </td>
        </tr>
        <tr v-if="rows.length === 0">
          <td :colspan="columns.length" class="px-3 py-8 text-center text-gray-400">暂无数据</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import type { ColumnDef } from './tableConfig'

defineProps<{
  columns: ColumnDef[]
  rows: Record<string, unknown>[]
}>()

defineEmits<{
  select: [row: Record<string, unknown>]
}>()

function formatDatetime(val: unknown): string {
  if (!val) return '-'
  const d = new Date(val as string)
  return isNaN(d.getTime()) ? String(val) : d.toLocaleString('zh-CN')
}
</script>
