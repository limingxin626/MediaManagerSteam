<template>
  <div
    class="bg-[var(--color-card-bg)] rounded-xl shadow-sm border border-gray-700 overflow-hidden hover:shadow-lg transition-all hover:scale-[1.02] duration-200 cursor-pointer flex flex-col"
    @click="$emit('click', person.id)"
  >
    <!-- Cover -->
    <div class="bg-gray-100 dark:bg-gray-700 overflow-hidden aspect-square">
      <img
        v-if="resolveCover(person)"
        :src="resolveCover(person)"
        :alt="person.name"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-3xl font-semibold text-[var(--color-primary-500)]/50">
        {{ person.name.charAt(0).toUpperCase() }}
      </div>
    </div>

    <div class="p-4 mt-auto">
      <div class="flex justify-between items-start mb-2">
        <h3 class="text-base font-bold text-gray-900 dark:text-white truncate">{{ person.name }}</h3>
        <button
          @click.stop="$emit('edit', person)"
          class="shrink-0 p-1 text-gray-400 hover:text-[var(--color-primary-500)] transition-colors"
          title="编辑"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
          </svg>
        </button>
      </div>
      <div class="text-sm text-gray-400">
        <template v-if="(person.folder_count ?? 0) > 0">{{ person.folder_count }} 部作品</template>
        <template v-else>{{ person.media_count }} 个媒体</template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Person } from '../types'
import { resolveCover } from '../utils/media'

interface Props {
  person: Person
}

defineProps<Props>()

defineEmits<{
  click: [id: number]
  edit: [person: Person]
  delete: [id: number]
}>()
</script>
