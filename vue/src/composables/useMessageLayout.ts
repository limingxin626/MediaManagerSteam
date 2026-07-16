import { ref } from 'vue'

// 两个维度混用同一个开关：
// - 'grid' / 'mosaic' 描述「卡片内媒体」的排列方式（消息流布局下每张 MessageCard 内部）
// - 'card' 是页面级布局：整条 message 变成一张固定大小的卡片，网格排列
// 保持单一状态最简单，toggle 三态循环 grid → mosaic → card。
export type MessageLayout = 'mosaic' | 'grid' | 'card'

const STORAGE_KEY = 'message_layout'

// 模块级单例：所有消费方共享同一份布局状态
const layout = ref<MessageLayout>('grid')

const CYCLE: MessageLayout[] = ['grid', 'mosaic', 'card']

export function useMessageLayout() {
  const setLayout = (newLayout: MessageLayout) => {
    layout.value = newLayout
    localStorage.setItem(STORAGE_KEY, newLayout)
  }

  const toggleLayout = () => {
    const idx = CYCLE.indexOf(layout.value)
    setLayout(CYCLE[(idx + 1) % CYCLE.length])
  }

  const initLayout = () => {
    const saved = localStorage.getItem(STORAGE_KEY) as MessageLayout | null
    // 未知/空值一律回退到 grid（默认）
    layout.value = saved && CYCLE.includes(saved) ? saved : 'grid'
  }

  return {
    layout,
    setLayout,
    toggleLayout,
    initLayout,
  }
}
