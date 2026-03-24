<template>
  <!-- Add Tag Modal -->
  <TransitionRoot appear :show="isOpen" as="template">
    <Dialog as="div" @close="handleClose" class="relative z-50">
      <TransitionChild
        as="template"
        enter="duration-300 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-200 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/30" />
      </TransitionChild>

      <div class="fixed inset-0 overflow-y-auto">
        <div class="flex min-h-full items-center justify-center p-4 text-center">
          <TransitionChild
            as="template"
            enter="duration-300 ease-out"
            enter-from="opacity-0 scale-95"
            enter-to="opacity-100 scale-100"
            leave="duration-200 ease-in"
            leave-from="opacity-100 scale-100"
            leave-to="opacity-0 scale-95"
          >
            <DialogPanel class="w-full max-w-4xl transform overflow-hidden rounded-2xl bg-white dark:bg-gray-800 p-6 text-left align-middle shadow-xl transition-all">
              <DialogTitle as="h3" class="text-lg font-medium leading-6 text-gray-900 dark:text-white mb-4">
                添加标签
              </DialogTitle>

              <div class="max-h-[70vh] overflow-y-auto">
                <div v-if="isLoadingTags" class="flex items-center justify-center py-8">
                  <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500"></div>
                </div>
                <div v-else-if="groupedTags.size === 0" class="text-center py-8 text-gray-500 dark:text-gray-400">
                  没有可添加的标签
                </div>
                
                <div v-else>
                  <div v-for="[type, tags] in groupedTags" :key="type" class="mb-6">
                    <Disclosure :default-open="true">
                      <DisclosureButton class="flex items-center justify-between w-full text-left cursor-pointer">
                        <h4 class="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3 uppercase tracking-wide">
                          {{ type }}
                        </h4>
                        <svg 
                          class="w-4 h-4 text-gray-400 transition-transform duration-200"
                          fill="none" 
                          stroke="currentColor" 
                          viewBox="0 0 24 24"
                        >
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
                        </svg>
                      </DisclosureButton>
                      <DisclosurePanel class="grid grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2">
                        <button
                          v-for="tag in tags"
                          :key="tag.id"
                          @click="toggleTagSelection(tag.id)"
                          :class="[
                            'text-left px-2 py-1.5 rounded border transition-colors text-sm',
                            isTagSelected(tag.id)
                              ? 'border-green-500 bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300 cursor-pointer'
                              : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-700 hover:bg-gray-50 dark:hover:bg-gray-700/50 text-gray-700 dark:text-gray-300 cursor-pointer'
                          ]"
                        >
                          <div class="flex items-center justify-between gap-1">
                            <span class="truncate">{{ tag.name }}</span>
                            <svg
                              v-if="isTagSelected(tag.id)"
                              class="w-3 h-3 text-green-500 flex-shrink-0"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                            </svg>
                          </div>
                        </button>
                      </DisclosurePanel>
                    </Disclosure>
                  </div>
                </div>
              </div>

              <div class="mt-6 flex gap-3">
                <button 
                  @click="handleSave"
                  class="flex-1 bg-indigo-600 text-white px-4 py-2 rounded-md hover:bg-indigo-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  保存
                </button>
                <button 
                  @click="handleClose"
                  class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-md hover:bg-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  取消
                </button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Dialog, DialogPanel, DialogTitle, TransitionRoot, TransitionChild, Disclosure, DisclosureButton, DisclosurePanel } from '@headlessui/vue'
import { API_BASE_URL } from '../utils/constants'

// 接口定义
interface Tag {
  id: number
  name: string
  category: string
}

// Props 定义
interface Props {
  isOpen: boolean
  availableTags?: Tag[]
  currentTags?: Tag[]
}

const props = withDefaults(defineProps<Props>(), {
  availableTags: () => [],
  currentTags: () => []
})

// Emits 定义
const emit = defineEmits<{
  close: []
  addTag: [tagId: number]
  saveTags: [tagIds: number[]]
}>()

// 组件内响应式数据
const searchQuery = ref('')
const tags = ref<Tag[]>([...props.availableTags])
const isLoadingTags = ref(false)
// 本地选中标签集合 - 初始化为当前已有的标签
const selectedTags = ref<Set<number>>(new Set(props.currentTags.map(tag => tag.id)))

// 获取所有标签
const fetchTags = async (): Promise<Tag[]> => {
  try {
    isLoadingTags.value = true
    const response = await fetch(`${API_BASE_URL}/api/tag`)
    if (!response.ok) {
      throw new Error('获取标签数据失败')
    }
    return await response.json()
  } catch (error) {
    console.error('获取标签失败:', error)
    return []
  } finally {
    isLoadingTags.value = false
  }
}

// 检查标签是否已经被选中
const isTagSelected = (tagId: number): boolean => {
  return selectedTags.value.has(tagId)
}

// 监听isOpen变化，当模态框打开时获取标签
watch(() => props.isOpen, async (isOpen) => {
  if (isOpen) {
    // 当弹窗打开时，重新初始化selectedTags为当前最新的标签
    selectedTags.value = new Set(props.currentTags.map(tag => tag.id))
    
    // 如果没有可用标签，则获取所有标签
    if (tags.value.length === 0) {
      const tagsData = await fetchTags()
      tags.value = tagsData
    }
  }
})

// 监听currentTags变化，同步更新selectedTags
watch(() => props.currentTags, (newTags) => {
  selectedTags.value = new Set(newTags.map(tag => tag.id))
}, { deep: true })

// 计算属性：过滤、排序并分组后的标签列表
const groupedTags = computed(() => {
  // 1. 按搜索条件过滤
  let filtered = tags.value
  const query = searchQuery.value.toLowerCase()
  if (query) {
    filtered = filtered.filter(tag => 
      tag.name.toLowerCase().includes(query) ||
      tag.category.toLowerCase().includes(query)
    )
  }
  
  // 2. 按名称升序排序
  const sorted = filtered.sort((a, b) => a.name.localeCompare(b.name))
  
  // 3. 按分类分组
  const grouped = new Map<string, typeof sorted>()
  for (const tag of sorted) {
    if (!grouped.has(tag.category)) {
      grouped.set(tag.category, [])
    }
    grouped.get(tag.category)!.push(tag)
  }
  
  return grouped
})

// 事件处理函数
const handleClose = () => {
  searchQuery.value = '' // 重置搜索查询
  emit('close')
}

// 切换标签选中状态
const toggleTagSelection = (tagId: number) => {
  if (selectedTags.value.has(tagId)) {
    selectedTags.value.delete(tagId)
  } else {
    selectedTags.value.add(tagId)
  }
}

// 此函数已不再使用，改为批量保存方式
// const handleAddTag = (tagId: number) => {
//   emit('addTag', tagId)
//   searchQuery.value = '' // 重置搜索查询
// }

// 保存选中的标签
const handleSave = () => {
  // 将Set转换为数组
  const selectedTagIds = Array.from(selectedTags.value)
  emit('saveTags', selectedTagIds)
  searchQuery.value = '' // 重置搜索查询
  emit('close')
}
</script>