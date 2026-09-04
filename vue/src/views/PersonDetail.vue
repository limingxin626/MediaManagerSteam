<template>
  <div class="fixed inset-0 z-[95] flex flex-col bg-[var(--bg-primary)]">
    <div v-if="loading && !person" class="grid flex-1 place-items-center">
      <div class="h-8 w-8 animate-spin rounded-full border-2 border-[var(--border-color)] border-t-[var(--color-primary-500)]"></div>
    </div>

    <template v-else-if="person">
      <!-- Top bar -->
      <header class="z-20 shrink-0 border-b border-[var(--border-color)] bg-[var(--bg-card)]/95 backdrop-blur">
        <div class="mx-auto flex h-14 w-full max-w-[1600px] items-center gap-3 px-3 sm:px-6 lg:px-8 xl:px-10">
          <button class="grid h-9 w-9 shrink-0 place-items-center rounded-[var(--radius-md)] text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]" title="返回人物列表 (Esc)" @click="close">
            <svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 19 3 12l7-7M3 12h18" /></svg>
          </button>
          <div class="min-w-0 flex-1">
            <h1 class="truncate text-sm font-semibold text-[var(--text-primary)] sm:text-base">{{ person.name }}</h1>
            <p class="truncate text-xs text-[var(--text-muted)]">{{ folderCount }} 部参演作品 · {{ person.media_count }} 个媒体</p>
          </div>
          <button
            class="grid h-9 shrink-0 place-items-center rounded-[var(--radius-md)] border border-[var(--border-color)] bg-[var(--bg-card)] text-[var(--text-secondary)] transition-colors hover:bg-[var(--bg-secondary)] hover:text-[var(--text-primary)]"
            title="编辑人物"
            @click="openEdit"
          >
            <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
          </button>
        </div>
      </header>

      <div ref="scrollContainer" class="min-h-0 flex-1 overflow-y-auto">
        <main class="mx-auto w-full max-w-[1760px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8 xl:px-10">
          <!-- Person intro -->
          <section class="mx-auto flex max-w-3xl items-start gap-5 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--border-color)] bg-[var(--bg-card)] p-5 shadow-[var(--shadow-md)]">
            <img v-if="coverUrl" :src="coverUrl" :alt="person.name" class="grid h-24 w-24 shrink-0 place-items-center rounded-2xl object-cover" />
            <div v-else class="grid h-24 w-24 shrink-0 place-items-center rounded-2xl bg-[var(--color-primary-500)]/10 text-4xl font-semibold text-[var(--color-primary-500)]/60">
              {{ initial }}
            </div>
            <div class="min-w-0 flex-1">
              <h2 class="truncate text-xl font-bold text-[var(--text-primary)]">{{ person.name }}</h2>
              <p v-if="person.description" class="mt-1.5 whitespace-pre-wrap text-sm leading-6 text-[var(--text-secondary)]">{{ person.description }}</p>
              <div class="mt-3 flex flex-wrap gap-2 text-xs text-[var(--text-secondary)]">
                <span class="inline-flex items-center gap-1 rounded-full bg-[var(--bg-secondary)] px-2.5 py-1"><span class="font-semibold text-[var(--text-primary)]">{{ folderCount }}</span> 部参演作品</span>
                <span class="inline-flex items-center gap-1 rounded-full bg-[var(--bg-secondary)] px-2.5 py-1"><span class="font-semibold text-[var(--text-primary)]">{{ person.media_count }}</span> 个媒体标注</span>
              </div>
            </div>
          </section>

          <!-- Folders of this person -->
          <section class="mt-8">
            <div class="mb-3 flex items-baseline justify-between gap-3">
              <h2 class="text-base font-semibold text-[var(--text-primary)]">参演作品</h2>
              <span class="text-xs tabular-nums text-[var(--text-muted)]">{{ folders.length }} / {{ folderCount }}</span>
            </div>

            <div v-if="loadingFolders && !folders.length" class="mx-auto grid max-w-7xl grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
              <div v-for="index in 8" :key="index" class="animate-pulse overflow-hidden rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)]">
                <div class="aspect-[376/535] bg-[var(--bg-secondary)]"></div>
                <div class="h-10 px-3 py-2.5"><div class="h-4 w-2/3 rounded bg-[var(--bg-secondary)]"></div></div>
              </div>
            </div>

            <div v-else-if="!folders.length" class="flex flex-col items-center py-16 text-center">
              <span class="grid h-14 w-14 place-items-center rounded-lg bg-[var(--bg-secondary)] text-[var(--text-muted)]">
                <svg class="h-7 w-7" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3.5 6.5h6l2 2h9v10h-17z" /></svg>
              </span>
              <h3 class="mt-4 text-sm font-medium text-[var(--text-primary)]">暂无参演作品目录</h3>
              <p class="mt-1 text-xs text-[var(--text-muted)]">当影片目录的 .nfo 标出该人物后会自动出现</p>
            </div>

            <div v-else class="mx-auto grid max-w-7xl grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
              <article
                v-for="folder in folders"
                :key="folder.id"
                :data-folder-id="folder.id"
                class="group flex min-w-0 cursor-pointer flex-col overflow-hidden rounded-lg border border-[var(--border-color)] bg-[var(--bg-card)] shadow-[var(--shadow-sm)] transition-shadow hover:shadow-[var(--shadow-md)]"
                @click="openFolder(folder.id)"
              >
                <div class="relative aspect-[376/535] shrink-0 overflow-hidden bg-[var(--bg-secondary)]">
                  <img v-if="resolveFolderCover(folder)" :src="resolveFolderCover(folder)" :alt="folder.name" class="h-full w-full object-cover transition-transform duration-200 group-hover:scale-[1.03]" loading="lazy" />
                  <div v-else class="grid h-full place-items-center text-[var(--text-muted)]">
                    <svg class="h-12 w-12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3"><path d="M4 5h16v14H4zM7 15l3-3 2 2 2-2 3 3" /></svg>
                  </div>
                  <span class="absolute right-2 top-2 rounded-full bg-black/55 px-2 py-0.5 text-[10px] font-medium text-white/90 backdrop-blur">{{ folderKindLabel(folder.kind) }}</span>
                </div>
                <div class="flex h-11 shrink-0 items-center gap-2 px-3 py-2.5">
                  <h3 class="min-w-0 truncate text-sm font-semibold leading-5">{{ folder.name }}</h3>
                  <span v-if="releasedYear(folder)" class="ml-auto shrink-0 text-[11px] tabular-nums text-[var(--text-muted)]">{{ releasedYear(folder) }}</span>
                </div>
              </article>
            </div>

            <!-- Sentinel for infinite scroll -->
            <div v-if="hasMore && folders.length" ref="sentinel" class="py-6 text-center">
              <div class="inline-block h-6 w-6 animate-spin rounded-full border-2 border-[var(--border-color)] border-t-[var(--color-primary-500)]"></div>
            </div>
            <div v-else-if="folders.length" class="py-8 text-center">
              <p class="text-xs text-[var(--text-muted)]">已经到底了</p>
            </div>
          </section>
        </main>
      </div>
    </template>

    <template v-else>
      <div class="grid flex-1 place-items-center">
        <p v-if="error" class="text-sm text-red-500">{{ error }}</p>
        <button v-else class="text-sm text-[var(--color-primary-600)]" @click="() => load(true)">重试</button>
      </div>
    </template>

    <!-- Edit modal reuses people page's form -->
    <PersonEditModal
      :is-open="showModal"
      title="编辑人物"
      :form-data="editForm"
      :edit-mode="true"
      @close="closeModal"
      @save="savePerson"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { Folder, FolderKind, Person, RepositoryFile } from '../types'
import PersonEditModal from '../components/PersonEditModal.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { resolveCover, resolveThumb } from '../utils/media'

interface FolderCursorResponse {
  items: Folder[]
  next_cursor: string | null
  has_more: boolean
}

const props = defineProps<{ personId: number }>()

const router = useRouter()
const toast = useToast()

const person = ref<Person | null>(null)
const loading = ref(false)
const error = ref('')

const folders = ref<Folder[]>([])
const loadingFolders = ref(false)
const nextCursor = ref<string | null>(null)
const hasMore = ref(false)

const scrollContainer = ref<HTMLElement | null>(null)
const sentinel = ref<HTMLElement | null>(null)
let infiniteObserver: IntersectionObserver | null = null
let loadRequest = 0

const folderCount = computed(() => person.value?.folder_count ?? 0)
const initial = computed(() => (person.value?.name ?? '?').charAt(0).toUpperCase())
const coverUrl = computed(() => (person.value ? resolveCover(person.value) : ''))

const editForm = ref({ name: '', description: '' })
const showModal = ref(false)

const KIND_LABELS: Record<string, string> = {
  movie: '影片', multi_part: '多部', series: '剧集',
  gallery: '图集', video: '单视频', mixed: '混合', unknown: '未分类',
}

function folderKindLabel(kind: FolderKind): string {
  return KIND_LABELS[kind] ?? kind
}

function releasedYear(folder: Folder): string {
  return (folder.released_at || folder.created_at || '').slice(0, 4)
}

function folderCoverFile(folder: Folder): RepositoryFile | null {
  if (folder.poster_file) return folder.poster_file
  if (folder.fanart_file) return folder.fanart_file
  return folder.preview_files?.[0] ?? null
}

function resolveFolderCover(folder: Folder): string {
  return resolveThumb(folderCoverFile(folder))
}

async function load(showSpinner = true) {
  const request = ++loadRequest
  if (showSpinner) loading.value = true
  error.value = ''
  try {
    const result = await api.get<Person>(`/people/${props.personId}`)
    if (request === loadRequest) {
      person.value = result
      editForm.value = { name: result.name, description: result.description ?? '' }
    }
  } catch (caught: any) {
    if (request === loadRequest) {
      person.value = null
      error.value = caught?.message || '加载人物失败'
    }
  } finally {
    if (request === loadRequest && showSpinner) loading.value = false
  }
}

async function loadFolders(reset = false) {
  if (loadingFolders.value) return
  loadingFolders.value = true
  try {
    const data = await api.get<FolderCursorResponse>('/folders', {
      person_id: props.personId,
      cursor: reset ? undefined : nextCursor.value,
      limit: 40,
      sort: 'released',
    })
    folders.value = reset ? data.items : [...folders.value, ...data.items]
    nextCursor.value = data.next_cursor
    hasMore.value = data.has_more
  } catch (caught: any) {
    toast.error(caught?.message || '加载参演作品失败')
  } finally {
    loadingFolders.value = false
    await nextTick()
    bindSentinel()
  }
}

// 人物与作品目录先后加载:先取 person(带 folder_count),再拉目录列表。
async function loadAll(showSpinner = true) {
  await load(showSpinner)
  if (person.value) await loadFolders(true)
}

function setupInfiniteScroll() {
  infiniteObserver?.disconnect()
  const root = scrollContainer.value
  if (!root) return
  infiniteObserver = new IntersectionObserver(entries => {
    if (entries[0]?.isIntersecting && !loadingFolders.value && hasMore.value) loadFolders()
  }, { root })
  bindSentinel()
}

function bindSentinel() {
  infiniteObserver?.disconnect()
  if (!sentinel.value || !hasMore.value) return
  infiniteObserver?.observe(sentinel.value)
}

function openFolder(folderId: number) {
  router.push({ name: 'FolderDetail', params: { id: folderId } })
}

function openEdit() {
  showModal.value = true
}

function closeModal() {
  showModal.value = false
}

async function savePerson(data: { name: string; description: string }) {
  try {
    await api.put(`/people/${props.personId}`, data)
    await load(false)
    closeModal()
    toast.success('保存成功')
  } catch {
    toast.error('保存人物数据失败')
  }
}

function close() {
  if (window.history.length > 1) router.back()
  else router.replace('/people')
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key !== 'Escape' || showModal.value) return
  event.preventDefault()
  close()
}

watch(() => props.personId, async () => {
  folders.value = []
  nextCursor.value = null
  hasMore.value = false
  await loadAll(true)
})

onMounted(() => {
  window.addEventListener('keydown', handleKeydown)
  loadAll(true)
  setupInfiniteScroll()
})

onBeforeUnmount(() => {
  loadRequest++
  infiniteObserver?.disconnect()
  window.removeEventListener('keydown', handleKeydown)
})
</script>
