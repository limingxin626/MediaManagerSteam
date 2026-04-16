<template>
  <div class="relative flex-1 max-w-md flex gap-1">
    <div class="relative flex-1">
      <input
        :value="modelValue"
        type="text"
        :placeholder="placeholder"
        class="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-300 dark:border-white/10 rounded-md bg-gray-50 dark:bg-white/10 text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[var(--color-primary-500)] focus:border-transparent"
        @input="onInput"
        @keydown.enter="onSearch"
      />
      <svg class="absolute left-2.5 top-2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    </div>
    <button
      @click="onSearch"
      class="px-3 py-1.5 text-sm bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)] text-white rounded-md transition-colors"
    >搜索</button>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: string
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'search': [value: string]
}>()

function onInput(e: Event) {
  const value = (e.target as HTMLInputElement).value
  emit('update:modelValue', value)
}

function onSearch() {
  emit('search', props.modelValue)
}
</script>
