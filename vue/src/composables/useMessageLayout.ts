import { ref } from 'vue'

export type MessageLayout = 'mosaic' | 'grid'

const STORAGE_KEY = 'message_layout'

// 模块级单例：所有消费方共享同一份布局状态
const layout = ref<MessageLayout>('grid')

export function useMessageLayout() {
  const setLayout = (newLayout: MessageLayout) => {
    layout.value = newLayout
    localStorage.setItem(STORAGE_KEY, newLayout)
  }

  const toggleLayout = () => {
    setLayout(layout.value === 'grid' ? 'mosaic' : 'grid')
  }

  const initLayout = () => {
    const saved = localStorage.getItem(STORAGE_KEY) as MessageLayout | null
    // 未知/空值一律回退到 grid（默认）
    layout.value = saved === 'mosaic' ? 'mosaic' : 'grid'
  }

  return {
    layout,
    setLayout,
    toggleLayout,
    initLayout,
  }
}
