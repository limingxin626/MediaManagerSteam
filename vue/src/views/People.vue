<template>
  <div class="h-full flex flex-col transition-colors">
    <!-- Header -->
    <div class="shrink-0 border-b border-[var(--border-color)] shadow-sm">
      <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div class="flex items-center gap-4 max-w-5xl mx-auto">
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
    <div ref="scrollContainer" class="flex-1 overflow-y-auto min-h-0">
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
            @click="openPerson"
            @edit="openEdit"
          />
        </div>
      </div>
    </div>

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
import { ref, computed, nextTick, onMounted, onActivated, onDeactivated } from 'vue'
import { useRouter } from 'vue-router'
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
const router = useRouter()

const people = ref<Person[]>([])
const loading = ref(false)
const filterName = ref('')

const scrollContainer = ref<HTMLElement | null>(null)
let savedScrollTop = 0

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

const openPerson = (personId: number) => {
  router.push({ name: 'PersonDetail', params: { id: personId } })
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

// 切到 PersonDetail 等其它路由时组件被 keep-alive 缓存，DOM 被摘除，
// 内部的滚动容器位置会重置。这里在失活时保存、重新激活时恢复，回到列表不再跳到顶部。
onDeactivated(() => {
  savedScrollTop = scrollContainer.value?.scrollTop ?? savedScrollTop
})

onActivated(() => {
  nextTick(() => {
    scrollContainer.value?.scrollTo({ top: savedScrollTop })
  })
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
