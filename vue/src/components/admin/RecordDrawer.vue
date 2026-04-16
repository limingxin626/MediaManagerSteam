<template>
  <div class="fixed inset-y-0 right-0 w-96 bg-[var(--bg-card)] border-l border-[var(--border-color)] shadow-xl z-50 flex flex-col">
    <!-- 头部 -->
    <div class="flex items-center justify-between px-4 py-3 border-b border-[var(--border-color)]">
      <h3 class="text-sm font-medium text-gray-900 dark:text-white">
        {{ tableDef.label }} #{{ record[tableDef.idField || 'id'] }}
      </h3>
      <button @click="$emit('close')" class="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>

    <!-- 内容 -->
    <div class="flex-1 overflow-y-auto p-4">
      <div class="space-y-3">
        <div v-for="col in tableDef.columns" :key="col.key">
          <label class="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">{{ col.label }}</label>
          <template v-if="col.editable">
            <textarea
              v-if="col.type === 'text'"
              v-model="editData[col.key]"
              rows="3"
              class="w-full px-2 py-1.5 text-sm rounded border border-[var(--border-color)] bg-[var(--bg-secondary)] text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-indigo-500 resize-y"
            />
            <input
              v-else
              v-model="editData[col.key]"
              :type="col.type === 'number' ? 'number' : 'text'"
              class="w-full px-2 py-1.5 text-sm rounded border border-[var(--border-color)] bg-[var(--bg-secondary)] text-gray-700 dark:text-gray-300 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </template>
          <template v-else>
            <div class="px-2 py-1.5 text-sm text-gray-700 dark:text-gray-300 bg-[var(--bg-secondary)] rounded break-all">
              <template v-if="col.type === 'datetime'">
                {{ formatDatetime(record[col.key]) }}
              </template>
              <template v-else>
                {{ record[col.key] ?? '-' }}
              </template>
            </div>
          </template>
        </div>
      </div>
    </div>

    <!-- 底部操作 -->
    <div class="px-4 py-3 border-t border-[var(--border-color)] flex items-center gap-2">
      <button
        v-if="tableDef.apiUpdate && hasEditableColumns"
        @click="save"
        :disabled="saving"
        class="px-3 py-1.5 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors"
      >
        {{ saving ? '保存中...' : '保存' }}
      </button>
      <button
        v-if="tableDef.apiDelete"
        @click="doDelete"
        class="px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors ml-auto"
      >
        删除
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useToast } from '../../composables/useToast'
import { useConfirm } from '../../composables/useConfirm'
import type { TableDef } from './tableConfig'

const props = defineProps<{
  record: Record<string, unknown>
  tableDef: TableDef
}>()

const emit = defineEmits<{
  close: []
  saved: []
  deleted: []
}>()

const toast = useToast()
const { confirm } = useConfirm()
const saving = ref(false)
const deleting = ref(false)
const editData = ref<Record<string, unknown>>({})

const hasEditableColumns = computed(() =>
  props.tableDef.columns.some(c => c.editable)
)

watch(
  () => props.record,
  (rec) => {
    const data: Record<string, unknown> = {}
    for (const col of props.tableDef.columns) {
      if (col.editable) {
        data[col.key] = rec[col.key]
      }
    }
    editData.value = data
  },
  { immediate: true },
)

function formatDatetime(val: unknown): string {
  if (!val) return '-'
  const d = new Date(val as string)
  return isNaN(d.getTime()) ? String(val) : d.toLocaleString('zh-CN')
}

async function save() {
  if (!props.tableDef.apiUpdate) return
  const id = props.record[props.tableDef.idField || 'id'] as number
  saving.value = true
  try {
    await props.tableDef.apiUpdate(id, editData.value)
    toast.success('保存成功')
    emit('saved')
  } catch (e: unknown) {
    toast.error((e as Error).message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function doDelete() {
  const ok = await confirm({
    title: '确认删除',
    message: `确定要删除 ${props.tableDef.label} #${props.record[props.tableDef.idField || 'id']} 吗？此操作不可恢复。`,
    danger: true,
  })
  if (!ok) return

  if (!props.tableDef.apiDelete) return
  const id = props.record[props.tableDef.idField || 'id'] as number
  deleting.value = true
  try {
    await props.tableDef.apiDelete(id)
    toast.success('删除成功')
    emit('deleted')
  } catch (e: unknown) {
    toast.error((e as Error).message || '删除失败')
  } finally {
    deleting.value = false
  }
}
</script>
