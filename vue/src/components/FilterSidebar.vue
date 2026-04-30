<template>
  <div class="flex flex-col w-48 shrink-0 border-r border-[var(--border-color)] min-h-0">
    <!-- Tags (top half) -->
    <div class="flex-1 min-h-0 flex flex-col overflow-hidden">
      <div class="px-3 pt-4 pb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider shrink-0">标签</div>
      <div class="flex-1 min-h-0 overflow-y-auto flex flex-col gap-0.5 px-2 pb-4">
        <button @click="onSelectTag(null)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left" :class="selectedTagId === null && selectedActorId === null
            ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
          <span>全部</span>
        </button>
        <div v-for="(parentTag, index) in tagTree" :key="index" class="flex flex-col gap-0.5">
          <button @click="onSelectTag(parentTag.id)"
            class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left" :class="selectedTagId === parentTag.id
              ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
            <span class="truncate">{{ parentTag.name }}</span>
            <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ parentTag.message_count }}</span>
          </button>
          <div v-if="parentTag.children && parentTag.children.length > 0" class="pl-6 flex flex-col gap-0.5">
            <button v-for="childTag in parentTag.children" :key="childTag.id" @click="onSelectTag(childTag.id)"
              class="flex items-center justify-between px-3 py-1.5 rounded-lg text-sm transition-colors text-left" :class="selectedTagId === childTag.id
                ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/10'">
              <span class="truncate">{{ childTag.name }}</span>
              <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ childTag.message_count }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Actor List (bottom half) -->
    <div class="flex-1 min-h-0 flex flex-col overflow-hidden border-t border-[var(--border-color)]">
      <div class="px-3 pt-4 pb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider shrink-0">演员</div>
      <div class="flex-1 min-h-0 overflow-y-auto flex flex-col gap-0.5 px-2 pb-4">
        <button
          v-if="noActorCount > 0 || selectedActorId === 0"
          @click="onSelectActor(0)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left"
          :class="selectedActorId === 0
            ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'"
        >
          <span class="truncate">无</span>
          <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ noActorCount }}</span>
        </button>
        <button
          v-for="actor in actors"
          :key="actor.id"
          @click="onSelectActor(actor.id)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left"
          :class="selectedActorId === actor.id
            ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'"
        >
          <span class="truncate">{{ actor.name }}</span>
          <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ actor.message_count }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Actor, TagWithCount } from '../types'

const props = defineProps<{
  tags: TagWithCount[]
  actors: Actor[]
  noActorCount: number
  selectedTagId: number | null
  selectedActorId: number | null
}>()

const emit = defineEmits<{
  (e: 'select-tag', tagId: number | null): void
  (e: 'select-actor', actorId: number | null): void
}>()

const onSelectTag = (tagId: number | null) => {
  if (tagId !== null && tagId < 0) return
  emit('select-tag', tagId)
}

const onSelectActor = (actorId: number | null) => {
  emit('select-actor', actorId)
}

const tagTree = computed(() => {
  const tagMap = new Map<number, TagWithCount & { children?: TagWithCount[] }>()
  const rootTags: (TagWithCount & { children?: TagWithCount[] })[] = []
  const virtualParentTags = new Map<string, TagWithCount & { children?: TagWithCount[] }>()

  props.tags.forEach(tag => {
    tagMap.set(tag.id, { ...tag, children: [] })
  })

  props.tags.forEach(tag => {
    const parts = tag.name.split('/')
    if (parts.length === 1) {
      rootTags.push(tagMap.get(tag.id)!)
    } else if (parts.length === 2) {
      const parentName = parts[0]
      const parentTag = props.tags.find(t => t.name === parentName)
      if (parentTag && tagMap.has(parentTag.id)) {
        tagMap.get(parentTag.id)!.children!.push(tag)
      } else {
        if (!virtualParentTags.has(parentName)) {
          const virtualTag: TagWithCount & { children?: TagWithCount[] } = {
            id: -1,
            name: parentName,
            message_count: 0,
            children: []
          }
          virtualParentTags.set(parentName, virtualTag)
          rootTags.push(virtualTag)
        }
        virtualParentTags.get(parentName)!.children!.push(tag)
      }
    } else {
      rootTags.push(tagMap.get(tag.id)!)
    }
  })

  rootTags.sort((a, b) => {
    if (b.message_count !== a.message_count) return b.message_count - a.message_count
    return a.name.localeCompare(b.name)
  })
  rootTags.forEach(tag => {
    if (tag.children) {
      tag.children.sort((a, b) => {
        if (b.message_count !== a.message_count) return b.message_count - a.message_count
        return a.name.localeCompare(b.name)
      })
    }
  })

  return rootTags
})
</script>
