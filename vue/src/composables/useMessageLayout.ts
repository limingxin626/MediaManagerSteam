import { ref } from 'vue'

export type MessageView = 'feed' | 'grid'
export type MessageMediaLayout = 'mosaic' | 'grid'

const VIEW_STORAGE_KEY = 'message_view'
const MEDIA_LAYOUT_STORAGE_KEY = 'message_media_layout'
const LEGACY_STORAGE_KEY = 'message_layout'

// 模块级单例：所有消费方共享同一份页面视图与消息内媒体布局。
const view = ref<MessageView>('feed')
const mediaLayout = ref<MessageMediaLayout>('grid')

export function useMessageLayout() {
  const setView = (newView: MessageView) => {
    view.value = newView
    localStorage.setItem(VIEW_STORAGE_KEY, newView)
  }

  const setMediaLayout = (newLayout: MessageMediaLayout) => {
    mediaLayout.value = newLayout
    localStorage.setItem(MEDIA_LAYOUT_STORAGE_KEY, newLayout)
  }

  const toggleView = () => setView(view.value === 'feed' ? 'grid' : 'feed')
  const toggleMediaLayout = () => setMediaLayout(mediaLayout.value === 'grid' ? 'mosaic' : 'grid')

  const initLayout = () => {
    const savedView = localStorage.getItem(VIEW_STORAGE_KEY)
    const savedMediaLayout = localStorage.getItem(MEDIA_LAYOUT_STORAGE_KEY)
    const legacy = localStorage.getItem(LEGACY_STORAGE_KEY)

    view.value = savedView === 'feed' || savedView === 'grid'
      ? savedView
      : legacy === 'card' ? 'grid' : 'feed'
    mediaLayout.value = savedMediaLayout === 'grid' || savedMediaLayout === 'mosaic'
      ? savedMediaLayout
      : legacy === 'mosaic' ? 'mosaic' : 'grid'

    localStorage.setItem(VIEW_STORAGE_KEY, view.value)
    localStorage.setItem(MEDIA_LAYOUT_STORAGE_KEY, mediaLayout.value)
    localStorage.removeItem(LEGACY_STORAGE_KEY)
  }

  return {
    view,
    mediaLayout,
    setView,
    setMediaLayout,
    toggleView,
    toggleMediaLayout,
    initLayout,
  }
}
