<template>
  <div class="flex items-center bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
    <button
      v-for="option in viewOptions"
      :key="option.value"
      @click="$emit('update:modelValue', option.value)"
      class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-all"
      :class="modelValue === option.value
        ? 'bg-white dark:bg-gray-600 text-indigo-600 dark:text-indigo-400 shadow-sm'
        : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
      "
      :title="option.label"
    >
      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="option.icon" />
      </svg>
      <span class="hidden sm:inline">{{ option.label }}</span>
    </button>
  </div>
</template>

<script setup lang="ts">
export type ViewMode = 'grid' | 'poster' | 'doujin'

interface ViewOption {
  value: ViewMode
  label: string
  icon: string
}

const props = defineProps<{
  modelValue: ViewMode
}>()

defineEmits<{
  'update:modelValue': [value: ViewMode]
}>()

const viewOptions: ViewOption[] = [
  {
    value: 'grid',
    label: '网格',
    icon: 'M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z'
  },
  {
    value: 'poster',
    label: '海报',
    icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z'
  },
  {
    value: 'doujin',
    label: '同人',
    icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10'
  }
]
</script>
