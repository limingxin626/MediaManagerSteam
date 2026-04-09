<template>
  <div class="shrink-0 border-t border-[var(--border-color)] shadow-lg">
    <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
      <div class="flex gap-2 items-center max-w-4xl mx-auto cursor-pointer" @click="emit('open')">
        <!-- Attachment Button -->
        <button
          class="flex-shrink-0 p-2 text-gray-400 hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-white/10 rounded-lg transition-colors"
          title="添加附件">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
        </button>

        <!-- Placeholder (readonly trigger) -->
        <div
          class="flex-1 px-4 py-2 border border-gray-300 dark:border-white/10 rounded-lg bg-gray-50 dark:bg-white/10 text-sm text-gray-400 select-none">
          输入消息...
        </div>

        <!-- Send Button (visual only) -->
        <button
          class="flex-shrink-0 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
          title="发送">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const emit = defineEmits<{
  open: []
}>()
</script>
