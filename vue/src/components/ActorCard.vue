<template>
  <div 
    class="bg-[var(--color-card-bg)] rounded-xl shadow-sm border border-gray-700 overflow-hidden hover:shadow-lg transition-all hover:scale-[1.02] duration-200 cursor-pointer flex flex-col"
    @click="$emit('click', actor.id)"
  >

    <!-- Thumbnail -->
    <div class="bg-gray-100 dark:bg-gray-700 overflow-hidden aspect-[3/4]">
      <img 
        :src="resolveAvatar(actor)"
        :alt="actor.name" 
        class="w-full h-full object-cover"
      />
    </div>

    <div class="p-4 mt-auto">
      <!-- Card Header -->
      <div class="flex justify-between items-start mb-4">
        <div>
          <h3 class="text-lg font-bold text-gray-900 dark:text-white mb-1 truncate">{{ actor.name }}</h3>
        </div>
      </div>

      <!-- Card Content -->
      <div class="text-sm text-gray-400">
        {{ actor.message_count }} 条消息
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Actor } from '../types'
import { resolveAvatar } from '../utils/media'

interface Props {
  actor: Actor
}

defineProps<Props>()

defineEmits<{
  click: [id: number]
  edit: [actor: Actor]
  delete: [id: number]
}>()


</script>
