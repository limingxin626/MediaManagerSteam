<template>
  <div class="h-full flex flex-col transition-colors">
    <!-- Header -->
    <div class="shrink-0 border-b border-[var(--border-color)] shadow-sm">
      <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div class="flex items-center gap-4 max-w-5xl mx-auto">
          <h2 class="text-lg font-bold text-gray-900 dark:text-white shrink-0">人物</h2>
          <SearchInput v-model="filterName" placeholder="搜索人物..." @search="() => {}" />
          <button
            @click="openCreate"
            class="shrink-0 inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium rounded-full bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)] transition-colors"
          >
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
            </svg>
            新建人物
          </button>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 overflow-y-auto min-h-0">
      <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 max-w-5xl">
        <!-- Loading -->
        <div v-if="loading" class="text-center py-20 text-[var(--text-muted)]">加载中...</div>

        <!-- Empty -->
        <div v-else-if="filteredPeople.length === 0" class="flex flex-col items-center justify-center py-20">
          <div class="relative w-24 h-24 mb-4">
            <div class="absolute inset-0 rounded-2xl bg-[var(--color-primary-500)]/10 rotate-6"></div>
            <div class="absolute inset-0 rounded-2xl bg-[var(--color-primary-500)]/5 -rotate-3"></div>
            <div class="absolute inset-0 flex items-center justify-center">
              <svg class="w-10 h-10 text-[var(--color-primary-500)]/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
          </div>
          <h3 class="text-sm font-medium text-[var(--text-primary)]">暂无人物</h3>
          <p class="mt-1 text-sm text-[var(--text-muted)]">点击「新建人物」添加</p>
        </div>

        <!-- Grid -->
        <div v-else class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          <PersonCard
            v-for="person in filteredPeople"
            :key="person.id"
            :person="person"
            @click="selectPerson(person)"
            @edit="openEdit"
          />
        </div>
      </div>
    </div>

    <!-- Person media placeholder panel (right slide-in) -->
    <!--
      TODO(person-media browsing):后端目前没有「按人物筛选 media」的接口。
      GET /media 只按 message 层的东西过滤(tag / collection / starred / type),
      没有 person_id 参数;客户端全量拉取再本地过滤在规模上不可行。
      待后端补 GET /media?person_id=<id>(复用现有 cursor 分页 + MediaResponse.people)后,
      这里可仿照 Media.vue 的 useVirtualGrid / 网格 + 无限滚动做人物媒体浏览。
    -->
    <Transition name="fade">
      <div v-if="selectedPerson" class="fixed inset-0 z-40 flex justify-end">
        <div class="absolute inset-0 bg-black/40" @click="selectedPerson = null"></div>
        <div class="relative w-full max-w-md h-full bg-[var(--bg-card)] border-l border-[var(--border-color)] shadow-2xl flex flex-col">
          <div class="shrink-0 flex items-center justify-between px-5 py-4 border-b border-[var(--border-color)]">
            <h3 class="text-base font-semibold text-[var(--text-primary)] truncate">{{ selectedPerson.name }}</h3>
            <button @click="selectedPerson = null" class="p-1.5 text-[var(--text-muted)] hover:text-[var(--text-primary)] rounded-lg transition-colors">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <div class="flex-1 flex flex-col items-center justify-center p-6 text-center">
            <svg class="w-12 h-12 text-[var(--color-primary-500)]/40 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <p class="text-sm font-medium text-[var(--text-primary)]">该人物有 {{ selectedPerson.media_count }} 个媒体</p>
            <p class="mt-2 text-xs text-[var(--text-muted)] max-w-xs">
              按人物浏览媒体的功能即将上线（需要后端提供 <code class="px-1 rounded bg-[var(--bg-secondary)]">GET /media?person_id=</code> 接口）。
              目前可在媒体预览中通过「标注人物」为媒体打上人物标签。
            </p>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Edit / Create Modal -->
    <PersonEditModal
      :is-open="showModal"
      :title="editMode ? '编辑人物' : '新建人物'"
      :form-data="formData"
      :edit-mode="editMode"
      @close="closeModal"
      @save="savePerson"
      @delete="deletePerson"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { Person } from '../types'
import PersonCard from '../components/PersonCard.vue'
import PersonEditModal from '../components/PersonEditModal.vue'
import SearchInput from '../components/SearchInput.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'

defineOptions({ name: 'People' })

const toast = useToast()
const { confirm } = useConfirm()

const people = ref<Person[]>([])
const loading = ref(false)
const filterName = ref('')

const selectedPerson = ref<Person | null>(null)

const showModal = ref(false)
const editMode = ref(false)
const currentEditId = ref<number | null>(null)
const formData = ref({ name: '', description: '' })

const filteredPeople = computed(() => {
  const q = filterName.value.trim().toLowerCase()
  if (!q) return people.value
  return people.value.filter(p => p.name.toLowerCase().includes(q))
})

const fetchPeople = async () => {
  loading.value = true
  try {
    people.value = await api.get<Person[]>('/people')
  } catch {
    toast.error('获取人物数据失败')
  } finally {
    loading.value = false
  }
}

const selectPerson = (person: Person) => {
  selectedPerson.value = person
}

const openCreate = () => {
  editMode.value = false
  currentEditId.value = null
  formData.value = { name: '', description: '' }
  showModal.value = true
}

const openEdit = (person: Person) => {
  editMode.value = true
  currentEditId.value = person.id
  formData.value = { name: person.name, description: person.description ?? '' }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editMode.value = false
  currentEditId.value = null
}

const savePerson = async (data: typeof formData.value) => {
  try {
    if (editMode.value && currentEditId.value) {
      await api.put(`/people/${currentEditId.value}`, data)
    } else {
      await api.post('/people', data)
    }
    await fetchPeople()
    closeModal()
    toast.success('保存成功')
  } catch {
    toast.error('保存人物数据失败')
  }
}

const deletePerson = async () => {
  if (!currentEditId.value) return
  const ok = await confirm({ title: '确认删除', message: '确定要删除这个人物吗？其媒体标注将被移除。', danger: true })
  if (!ok) return
  try {
    await api.del(`/people/${currentEditId.value}`)
    await fetchPeople()
    closeModal()
    toast.success('删除成功')
  } catch {
    toast.error('删除人物失败')
  }
}

onMounted(() => {
  fetchPeople()
})
</script>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
