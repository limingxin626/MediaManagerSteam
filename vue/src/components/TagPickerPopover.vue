<template>
  <div class="relative inline-block">
    <button @click.stop="open = !open" class="p-1 text-gray-500 hover:text-green-500 rounded transition-colors"
      title="添加标签">
      <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z" />
      </svg>
    </button>
    <div v-if="open" ref="popoverRef"
      class="absolute bottom-full right-0 mb-1 w-56 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg shadow-xl z-50 overflow-hidden">
      <div class="p-2 border-b border-[var(--border-color)]">
        <input ref="searchRef" v-model="search" type="text" placeholder="搜索标签..."
          class="w-full px-2 py-1 text-sm bg-transparent border border-[var(--border-color)] rounded focus:outline-none focus:border-[var(--color-primary-500)] text-[var(--text-primary)]"
          @click.stop />
      </div>
      <div class="max-h-48 overflow-y-auto py-1">
        <button v-for="tag in filteredTags" :key="tag.id" @click.stop="selectTag(tag)"
          class="w-full px-3 py-1.5 text-left text-sm transition-colors flex items-center justify-between"
          :class="existingTagNames.has(tag.name)
            ? 'text-gray-400 dark:text-gray-500'
            : 'text-[var(--text-primary)] hover:bg-gray-100 dark:hover:bg-white/10'">
          <span class="truncate">#{{ tag.name }}</span>
          <span v-if="existingTagNames.has(tag.name)" class="text-xs text-gray-400 shrink-0 ml-1">已添加</span>
          <span v-else class="text-xs text-gray-400 dark:text-gray-500 shrink-0 ml-1">{{ tag.message_count }}</span>
        </button>
        <div v-if="filteredTags.length === 0" class="px-3 py-2 text-sm text-gray-400">无匹配标签</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import type { TagWithCount, TagItem } from '../types'
import { getPinyinInitials } from '../utils/pinyinInitial'

const props = defineProps<{
  allTags: TagWithCount[]
  messageTags: TagItem[]
}>()

const emit = defineEmits<{
  select: [tag: TagWithCount]
}>()

const open = ref(false)
const search = ref('')
const popoverRef = ref<HTMLElement | null>(null)
const searchRef = ref<HTMLInputElement | null>(null)

const existingTagNames = computed(() => new Set(props.messageTags.map(t => t.name)))

const filteredTags = computed(() => {
  const sorted = [...props.allTags].sort((a, b) => b.message_count - a.message_count)
  if (!search.value) return sorted
  const q = search.value.toLowerCase()
  const textMatched = sorted.filter(t => t.name.toLowerCase().includes(q))
  if (!(/^[a-z]+$/.test(q))) return textMatched
  const textIds = new Set(textMatched.map(t => t.id))
  const pinyinMatched = sorted.filter(t => !textIds.has(t.id) && getPinyinInitials(t.name).startsWith(q))
  return [...textMatched, ...pinyinMatched]
})

const selectTag = (tag: TagWithCount) => {
  emit('select', tag)
  open.value = false
  search.value = ''
}

watch(open, (val) => {
  if (val) {
    nextTick(() => searchRef.value?.focus())
  } else {
    search.value = ''
  }
})

const onClickOutside = (e: MouseEvent) => {
  if (popoverRef.value && !popoverRef.value.contains(e.target as Node)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>
