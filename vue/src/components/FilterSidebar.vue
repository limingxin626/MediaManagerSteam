<template>
  <div class="flex flex-col w-48 shrink-0 border-r border-[var(--border-color)] min-h-0">
    <!-- Tab bar -->
    <div class="shrink-0 flex border-b border-[var(--border-color)]">
      <button
        v-for="tab in visibleTabs"
        :key="tab.key"
        @click="activeTab = tab.key"
        class="flex-1 px-2 py-2.5 text-xs font-semibold transition-colors relative"
        :class="activeTab === tab.key
          ? 'text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
          : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'"
      >
        {{ tab.label }}
        <span
          v-if="activeTab === tab.key"
          class="absolute left-2 right-2 -bottom-px h-0.5 rounded-full bg-[var(--color-primary-600)] dark:bg-[var(--color-primary-500)]"
        ></span>
      </button>
    </div>

    <!-- Tag panel -->
    <div v-show="activeTab === 'tag'" class="flex-1 min-h-0 overflow-y-auto flex flex-col gap-0.5 px-2 py-3">
      <button @click="onSelectTag(null)"
        class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left" :class="selectedTagId === null
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

    <!-- Actor panel -->
    <div v-show="activeTab === 'actor'" class="flex-1 min-h-0 overflow-y-auto flex flex-col gap-0.5 px-2 py-3">
      <button @click="onSelectActor(null)"
        class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left" :class="selectedActorId === null
          ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
        <span>全部</span>
      </button>
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

    <!-- Issue panel -->
    <div v-if="issueEnabled" v-show="activeTab === 'issue'" class="flex-1 min-h-0 overflow-y-auto flex flex-col gap-0.5 px-2 py-3">
      <div v-if="onCreateIssue" class="flex justify-end px-1 pb-1">
        <button
          @click="onCreateIssue"
          class="text-gray-400 hover:text-[var(--color-primary-500)] text-sm leading-none"
          title="新增 issue"
        >＋ 新增</button>
      </div>
      <button @click="onSelectIssue(null)"
        class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left" :class="selectedIssueId === null
          ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
        <span>全部</span>
      </button>
      <button
        v-if="noIssueCount > 0 || selectedIssueId === 0"
        @click="onSelectIssue(0)"
        class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left"
        :class="selectedIssueId === 0
          ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'"
      >
        <span class="truncate">无</span>
        <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ noIssueCount }}</span>
      </button>
      <button
        v-for="issue in issues"
        :key="issue.id"
        @click="onSelectIssue(issue.id)"
        class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left"
        :class="selectedIssueId === issue.id
          ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
          : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'"
      >
        <span class="truncate">{{ issue.title }}</span>
        <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ issue.message_count }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Actor, Issue, TagWithCount } from '../types'

type TabKey = 'tag' | 'actor' | 'issue'

const props = withDefaults(defineProps<{
  tags: TagWithCount[]
  actors: Actor[]
  noActorCount: number
  selectedTagId: number | null
  selectedActorId: number | null
  issues?: Issue[]
  noIssueCount?: number
  selectedIssueId?: number | null
  onCreateIssue?: () => void
}>(), {
  issues: () => [],
  noIssueCount: 0,
  selectedIssueId: null,
})

const emit = defineEmits<{
  (e: 'select-tag', tagId: number | null): void
  (e: 'select-actor', actorId: number | null): void
  (e: 'select-issue', issueId: number | null): void
}>()

// Issue 功能仅在消费方接入(传 issues / onCreateIssue / 已选 issue)时启用;
// Media 页不传这些,自然退化为「标签 / 演员」两个 tab。
const issueEnabled = computed(() =>
  props.issues.length > 0 || !!props.onCreateIssue || (props.selectedIssueId ?? null) !== null,
)

const visibleTabs = computed<{ key: TabKey; label: string }[]>(() => {
  const tabs: { key: TabKey; label: string }[] = [
    { key: 'tag', label: '标签' },
    { key: 'actor', label: '演员' },
  ]
  if (issueEnabled.value) tabs.push({ key: 'issue', label: 'Issue' })
  return tabs
})

const activeTab = ref<TabKey>('tag')

// 当前有选中项时,自动切到对应 tab,使 keep-alive 返回 / 外部改选时 UI 一致。
watch(
  () => [props.selectedActorId, props.selectedIssueId, props.selectedTagId] as const,
  ([actorId, issueId]) => {
    if (actorId !== null) activeTab.value = 'actor'
    else if (issueEnabled.value && (issueId ?? null) !== null) activeTab.value = 'issue'
  },
  { immediate: true },
)

const onSelectTag = (tagId: number | null) => {
  if (tagId !== null && tagId < 0) return
  emit('select-tag', tagId)
}

const onSelectActor = (actorId: number | null) => {
  emit('select-actor', actorId)
}

const onSelectIssue = (issueId: number | null) => {
  emit('select-issue', issueId)
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
