import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { api } from './useApi'
import type {
  RepositoryBrowseResponse,
  RepositoryFile,
  RepositorySummary,
} from '../types'

export function useRepositoryBrowser() {
  const repositories = ref<RepositorySummary[]>([])
  const selectedRepoId = ref('')
  const currentPath = ref('')
  const browse = ref<RepositoryBrowseResponse | null>(null)
  const loading = ref(false)
  const error = ref('')
  const visibleFileCount = ref(60)
  let pollTimer: number | undefined

  const selectedRepository = computed(() =>
    repositories.value.find((repository) => repository.repo_id === selectedRepoId.value) ?? null,
  )

  const visibleFiles = computed<RepositoryFile[]>(() =>
    (browse.value?.files ?? []).slice(0, visibleFileCount.value),
  )
  const hasMoreFiles = computed(() => visibleFileCount.value < (browse.value?.files.length ?? 0))

  async function loadRepositories() {
    repositories.value = await api.get<RepositorySummary[]>('/repositories')
    if (!selectedRepoId.value || !repositories.value.some((repo) => repo.repo_id === selectedRepoId.value)) {
      selectedRepoId.value = repositories.value[0]?.repo_id ?? ''
    }
  }

  async function loadFolder(path = currentPath.value, quiet = false) {
    if (!selectedRepoId.value) {
      browse.value = null
      return
    }
    if (!quiet) loading.value = true
    error.value = ''
    try {
      const data = await api.get<RepositoryBrowseResponse>(
        `/repositories/${encodeURIComponent(selectedRepoId.value)}/browse`,
        { path },
      )
      browse.value = data
      currentPath.value = data.folder.rel_path
      visibleFileCount.value = 60
      const index = repositories.value.findIndex((repo) => repo.repo_id === data.repository.repo_id)
      if (index !== -1) repositories.value[index] = data.repository
    } catch (e: any) {
      error.value = e?.message || '加载文件夹失败'
    } finally {
      if (!quiet) loading.value = false
    }
  }

  function openFolder(path: string) {
    currentPath.value = path
    return loadFolder(path)
  }

  function loadMoreFiles() {
    visibleFileCount.value += 60
  }

  async function pollPending() {
    clearTimeout(pollTimer)
    if (!selectedRepoId.value) return
    try {
      const summary = await api.get<RepositorySummary>(
        `/repositories/${encodeURIComponent(selectedRepoId.value)}`,
      )
      const index = repositories.value.findIndex((repo) => repo.repo_id === summary.repo_id)
      if (index !== -1) repositories.value[index] = summary
      if (browse.value?.repository.repo_id === summary.repo_id) browse.value.repository = summary
      if (summary.pending_count > 0) {
        await loadFolder(currentPath.value, true)
        pollTimer = window.setTimeout(pollPending, 3000)
      }
    } catch {
      pollTimer = window.setTimeout(pollPending, 5000)
    }
  }

  watch(selectedRepoId, async () => {
    currentPath.value = ''
    await loadFolder('')
    pollPending()
  })

  onMounted(async () => {
    try {
      await loadRepositories()
    } catch (e: any) {
      error.value = e?.message || '加载仓库失败'
    }
  })

  onUnmounted(() => clearTimeout(pollTimer))

  return {
    repositories,
    selectedRepoId,
    selectedRepository,
    currentPath,
    browse,
    visibleFiles,
    hasMoreFiles,
    loading,
    error,
    openFolder,
    loadMoreFiles,
  }
}
