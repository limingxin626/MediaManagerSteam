<template>
  <div class="relative inline-block">
    <button @click.stop="open = !open"
      :class="variant === 'preview-toolbar'
        ? 'p-2 text-white hover:bg-white/10 rounded-full transition-colors'
        : 'p-1 text-gray-500 hover:text-green-500 rounded transition-colors'"
      title="添加标签">
      <svg :class="variant === 'preview-toolbar' ? 'w-6 h-6' : 'w-3.5 h-3.5'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A2 2 0 013 12V7a4 4 0 014-4z" />
      </svg>
    </button>
    <div v-if="open" ref="popoverRef"
      class="absolute right-0 w-56 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-lg shadow-xl z-50 overflow-hidden"
      :class="direction === 'down' ? 'top-full mt-1' : 'bottom-full mb-1'">
      <div class="p-2 border-b border-[var(--border-color)]">
        <input ref="searchRef" v-model="search" type="text" placeholder="搜索标签..."
          class="w-full px-2 py-1 text-sm bg-transparent border border-[var(--border-color)] rounded focus:outline-none focus:border-[var(--color-primary-500)] text-[var(--text-primary)]"
          @click.stop @keydown="onKeydown" />
      </div>
      <div ref="listRef" class="max-h-48 overflow-y-auto py-1">
        <button v-for="(tag, index) in filteredTags" :key="tag.id" @click.stop="selectTag(tag)"
          class="w-full px-3 py-1.5 text-left text-sm transition-colors flex items-center justify-between"
          :class="[
            existingTagNames.has(tag.name)
              ? 'text-gray-400 dark:text-gray-500'
              : index === activeIndex
                ? 'bg-indigo-600 text-white'
                : 'text-[var(--text-primary)] hover:bg-gray-100 dark:hover:bg-white/10'
          ]">
          <span class="truncate">#{{ tag.name }}</span>
          <span v-if="existingTagNames.has(tag.name)" class="text-xs shrink-0 ml-1"
            :class="index === activeIndex ? 'text-indigo-200' : 'text-gray-400'">已添加</span>
          <span v-else class="text-xs shrink-0 ml-1"
            :class="index === activeIndex ? 'text-indigo-200' : 'text-gray-400 dark:text-gray-500'">{{ tag.message_count }}</span>
        </button>
        <div v-if="filteredTags.length === 0 && !canCreate" class="px-3 py-2 text-sm text-gray-400">无匹配标签</div>
        <button v-if="canCreate" @click.stop="createTag"
          class="w-full px-3 py-1.5 text-left text-sm transition-colors flex items-center gap-1.5"
          :class="activeIndex === filteredTags.length
            ? 'bg-indigo-600 text-white'
            : 'text-[var(--text-primary)] hover:bg-gray-100 dark:hover:bg-white/10'"
          :disabled="creating">
          <svg class="w-3.5 h-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
          </svg>
          <span class="truncate">添加 <span class="font-medium">#{{ search.trim() }}</span></span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import type { TagWithCount, TagItem } from '../types'
import { getPinyinInitials } from '../utils/pinyinInitial'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'

const props = defineProps<{
  allTags: TagWithCount[]
  messageTags: TagItem[]
  direction?: 'up' | 'down'
  variant?: 'default' | 'preview-toolbar'
}>()

const emit = defineEmits<{
  select: [tag: TagWithCount]
  created: [tag: TagWithCount]
}>()

const toast = useToast()

const open = ref(false)
const search = ref('')
const activeIndex = ref(0)
const creating = ref(false)
const popoverRef = ref<HTMLElement | null>(null)
const searchRef = ref<HTMLInputElement | null>(null)
const listRef = ref<HTMLElement | null>(null)

const existingTagNames = computed(() => new Set(props.messageTags.map(t => t.name)))

// 搜索词非空、且没有同名已存在标签时,允许新建
const canCreate = computed(() => {
  const name = search.value.trim()
  if (!name) return false
  return !props.allTags.some(t => t.name.toLowerCase() === name.toLowerCase())
})

const filteredTags = computed(() => {
  const sorted = [...props.allTags].sort((a, b) => b.message_count - a.message_count)
  if (!search.value) return sorted
  const q = search.value.toLowerCase()
  const textMatched = sorted.filter(t => t.name.toLowerCase().includes(q))
  if (!(/^[a-z]+$/.test(q))) return textMatched
  const textIds = new Set(textMatched.map(t => t.id))
  const pinyinMatched = sorted.filter(t => !textIds.has(t.id) && getPinyinInitials(t.name).includes(q))
  return [...textMatched, ...pinyinMatched]
})

watch(filteredTags, (newList) => {
  if (activeIndex.value >= newList.length) activeIndex.value = Math.max(newList.length - 1, 0)
})

const scrollToActive = () => {
  nextTick(() => {
    const list = listRef.value
    if (!list) return
    const item = list.children[activeIndex.value] as HTMLElement | undefined
    item?.scrollIntoView({ block: 'nearest' })
  })
}

const onKeydown = (e: KeyboardEvent) => {
  // 列表项数 + (可新建时的额外一行)
  const maxIndex = filteredTags.value.length - (canCreate.value ? 0 : 1)
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    activeIndex.value = Math.min(activeIndex.value + 1, Math.max(maxIndex, 0))
    scrollToActive()
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    activeIndex.value = Math.max(activeIndex.value - 1, 0)
    scrollToActive()
  } else if (e.key === 'Enter') {
    e.preventDefault()
    if (canCreate.value && activeIndex.value === filteredTags.value.length) {
      createTag()
      return
    }
    const tag = filteredTags.value[activeIndex.value]
    if (tag) selectTag(tag)
  } else if (e.key === 'Escape') {
    open.value = false
  }
}

const selectTag = (tag: TagWithCount) => {
  if (existingTagNames.value.has(tag.name)) return
  emit('select', tag)
}

const createTag = async () => {
  const name = search.value.trim()
  if (!name || creating.value) return
  creating.value = true
  try {
    const tag = await api.post<TagWithCount>('/tags', { name })
    emit('created', tag)
    emit('select', tag)
    toast.success(`已创建标签 #${tag.name}`)
    open.value = false
  } catch {
    toast.error('创建标签失败')
  } finally {
    creating.value = false
  }
}

watch(open, (val) => {
  if (val) {
    nextTick(() => searchRef.value?.focus())
  } else {
    search.value = ''
    activeIndex.value = 0
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
