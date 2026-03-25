<template>
  <div class="min-h-screen transition-colors">
    <!-- Fixed Search Header -->
    <div class="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 shadow-sm">
      <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div class="flex flex-col sm:flex-row gap-4 items-start sm:items-center max-w-2xl mx-auto">
          <h2 class="text-2xl font-bold text-gray-900 dark:text-white">消息流</h2>
          <!-- Search -->
          <div class="relative flex-1 max-w-md">
            <input 
              v-model="searchQuery"
              type="text" 
              placeholder="搜索消息..." 
              class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
            />
            <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          <div class="flex items-center gap-3">
            <!-- View Toggle -->
            <ViewToggle v-model="currentView" />
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content with top padding for fixed header -->
    <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24 pt-24">
      <!-- Messages Feed View -->
      <div v-if="messages.length > 0" class="flex flex-col gap-4 max-w-2xl mx-auto" ref="messagesContainer">
        <MessageCard
          v-for="message in messages" 
          :key="message.id"
          :message="message"
          :media-items="message.media_items"
          :tags="message.tags"
          @click="goToMessage"
          @media-click="(index) => handleMediaClick(message.id, index)"
        />
        <!-- 加载更多指示器 -->
        <div v-if="loading" class="col-span-full text-center py-8">
          <div class="inline-block animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"></div>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-400">加载中...</p>
        </div>
        <!-- 没有更多数据提示 -->
        <div v-if="!loading && !hasMoreData" class="col-span-full text-center py-8">
          <p class="text-sm text-gray-500 dark:text-gray-400">已经到底了</p>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="messages.length === 0 && !loading" class="text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">暂无消息</h3>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">还没有任何消息内容</p>
      </div>
    </div>

    <MediaPreview
      :is-open="previewOpen"
      :items="previewItems"
      :start-index="previewStartIndex"
      @close="closePreview"
      @navigate-prev="navigateToPrevMessage"
      @navigate-next="navigateToNextMessage"
    />

    <!-- Fixed Input Area at Bottom -->
    <div class="fixed bottom-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 shadow-lg">
      <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div class="flex gap-2 items-end max-w-2xl mx-auto">
          <!-- Attachment Button -->
          <button
            @click="triggerFileInput"
            class="flex-shrink-0 p-2 text-gray-600 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors"
            title="添加附件"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          </button>
          
          <!-- File Input (Hidden) -->
          <input
            ref="fileInput"
            type="file"
            multiple
            class="hidden"
            @change="handleFileSelect"
          />
          
          <!-- Text Input -->
          <div class="flex-1 relative">
            <textarea
              v-model="newMessageText"
              placeholder="输入消息..."
              rows="1"
              class="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
              @keydown.enter.prevent="handleEnterKey"
            />
          </div>
          
          <!-- Send Button -->
          <button
            @click="sendMessage"
            :disabled="!newMessageText.trim() && selectedFiles.length === 0"
            class="flex-shrink-0 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 text-white rounded-lg transition-colors"
            title="发送"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          </button>
        </div>
        
        <!-- Selected Files Preview -->
        <div v-if="selectedFiles.length > 0" class="mt-2 max-w-2xl mx-auto">
          <div class="flex flex-wrap gap-2">
            <div
              v-for="(filePath, index) in selectedFiles"
              :key="index"
              class="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded-md text-sm"
            >
              <span class="text-gray-700 dark:text-gray-300 truncate max-w-xs">{{ filePath.split('\\').pop() || filePath }}</span>
              <button
                @click="removeFile(index)"
                class="text-gray-500 hover:text-red-500 transition-colors"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTheme } from '../composables/useTheme'
import { type MessageDetail } from '../types'
import MessageCard from '../components/MessageCard.vue'
import ViewToggle from '../components/ViewToggle.vue'
import MediaPreview from '../components/MediaPreview.vue'
import type { ViewMode } from '../components/ViewToggle.vue'
import { API_BASE_URL } from '../utils/constants'

defineOptions({
  name: 'Message'
})

const router = useRouter()
const { initTheme } = useTheme()

const messages = ref<MessageDetail[]>([])
const loading = ref(false)
const searchQuery = ref('')
const currentView = ref<ViewMode>('grid')

const pageSize = ref(20)
const hasMoreData = ref(true)
const messagesContainer = ref<HTMLElement | null>(null)
const nextCursor = ref<string | null>(null)

const previewOpen = ref(false)
const previewItems = ref<any[]>([])
const previewStartIndex = ref(0)
const currentMessageIndex = ref(-1)

const newMessageText = ref('')
const selectedFiles = ref<string[]>([])
const fileInput = ref<HTMLInputElement | null>(null)

const triggerFileInput = () => {
  // 尝试在 Electron 环境中获取完整文件路径
  try {
    // 检查是否在 Electron 环境中
    const isElectron = navigator.userAgent.indexOf('Electron') > -1
    console.log('Is Electron:', isElectron)
    
    if (isElectron) {
      // 在 Electron 中，使用 dialog 模块获取完整文件路径
      const { dialog } = require('electron')
      dialog.showOpenDialog({
        properties: ['openFile', 'multiSelections']
      }).then(result => {
        if (!result.canceled && result.filePaths) {
          console.log('Electron file paths:', result.filePaths)
          selectedFiles.value = [...selectedFiles.value, ...result.filePaths]
        }
      }).catch(err => {
        console.error('Error opening dialog:', err)
        // 回退到标准文件输入
        fileInput.value?.click()
      })
    } else {
      // 非 Electron 环境，使用标准文件输入
      fileInput.value?.click()
    }
  } catch (error) {
    console.error('Error in triggerFileInput:', error)
    // 回退到标准文件输入
    fileInput.value?.click()
  }
}

const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  if (target.files) {
    const filePaths = Array.from(target.files).map(file => {
      // 在 Electron 中，文件对象有 path 属性，包含绝对路径
      // 尝试不同的方式获取路径
      const filePath = (file as any).path || (file as any).webkitRelativePath || file.name
      console.log('File path:', filePath)
      return filePath
    })
    selectedFiles.value = [...selectedFiles.value, ...filePaths]
  }
  target.value = ''
}

const removeFile = (index: number) => {
  selectedFiles.value.splice(index, 1)
}

const handleEnterKey = (event: KeyboardEvent) => {
  if (!event.shiftKey) {
    sendMessage()
  }
}

const sendMessage = async () => {
  if (!newMessageText.value.trim() && selectedFiles.value.length === 0) {
    return
  }

  try {
    const messageData = {
      text: newMessageText.value || null,
      files: selectedFiles.value
    }

    const response = await fetch(`${API_BASE_URL}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(messageData)
    })

    if (!response.ok) {
      throw new Error('Failed to send message')
    }

    const newMessage = await response.json()
    
    messages.value.push(newMessage)
    
    newMessageText.value = ''
    selectedFiles.value = []
    
    setTimeout(() => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
    }, 100)
    
  } catch (error) {
    console.error('Error sending message:', error)
    alert('发送消息失败，请稍后重试')
  }
}

const fetchMessages = async (isLoadingMore = false) => {
  if (loading.value) return
  if (isLoadingMore && !hasMoreData.value) return
  
  loading.value = true
  try {
    let url = `${API_BASE_URL}/messages/with-detail?limit=${pageSize.value}`
    if (isLoadingMore && nextCursor.value) {
      url += `&cursor=${encodeURIComponent(nextCursor.value)}`
    }
    if (searchQuery.value) {
      url += `&query_text=${encodeURIComponent(searchQuery.value)}`
    }
    
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error('Failed to fetch messages')
    }
    const data = await response.json()
    
    hasMoreData.value = data.has_more
    nextCursor.value = data.next_cursor
    
    const previousScrollY = window.scrollY
    const previousHeight = document.body.scrollHeight
    
    if (isLoadingMore) {
      messages.value = [...data.items.reverse(), ...messages.value]
    } else {
      messages.value = data.items.reverse()
    }
    
    if (!isLoadingMore) {
      setTimeout(() => {
        window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
      }, 100)
    } else {
      setTimeout(() => {
        const newHeight = document.body.scrollHeight
        const scrollDelta = newHeight - previousHeight
        window.scrollTo({ top: previousScrollY + scrollDelta, behavior: 'auto' })
      }, 100)
    }
  } catch (error) {
    console.error('Error fetching messages:', error)
    alert('获取消息数据失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

const goToMessage = (messageId: number) => {
  router.push(`/message/${messageId}`)
}

const handleMediaClick = (messageId: number, mediaIndex: number) => {
  const message = messages.value.find(m => m.id === messageId)
  if (!message || !message.media_items) return
  
  currentMessageIndex.value = messages.value.findIndex(m => m.id === messageId)
  previewItems.value = message.media_items
  previewStartIndex.value = mediaIndex
  previewOpen.value = true
}

const closePreview = () => {
  previewOpen.value = false
  previewItems.value = []
  currentMessageIndex.value = -1
}

const navigateToPrevMessage = () => {
  if (currentMessageIndex.value > 0) {
    const prevMessage = messages.value[currentMessageIndex.value - 1]
    if (prevMessage && prevMessage.media_items && prevMessage.media_items.length > 0) {
      currentMessageIndex.value--
      previewItems.value = prevMessage.media_items
      previewStartIndex.value = 0
    }
  }
}

const navigateToNextMessage = () => {
  if (currentMessageIndex.value < messages.value.length - 1) {
    const nextMessage = messages.value[currentMessageIndex.value + 1]
    if (nextMessage && nextMessage.media_items && nextMessage.media_items.length > 0) {
      currentMessageIndex.value++
      previewItems.value = nextMessage.media_items
      previewStartIndex.value = 0
    }
  }
}

let searchTimeout: ReturnType<typeof setTimeout> | null = null

watch(searchQuery, () => {
  if (searchTimeout) {
    clearTimeout(searchTimeout)
  }
  searchTimeout = setTimeout(() => {
    messages.value = []
    nextCursor.value = null
    hasMoreData.value = true
    fetchMessages()
  }, 300)
})

// 记录上一次滚动位置
const lastScrollTop = ref(0)

// 节流函数
const throttle = (func: Function, delay: number) => {
  let lastCall = 0
  return function(...args: any[]) {
    const now = Date.now()
    if (now - lastCall < delay) {
      return
    }
    lastCall = now
    func.apply(this, args)
  }
}

const handleScroll = throttle(() => {
  const windowScrollTop = window.scrollY
  
  const isNearTop = windowScrollTop <= window.innerHeight * 2
  const isScrollingUp = windowScrollTop < lastScrollTop.value
  
  if (isNearTop && isScrollingUp && !loading.value && hasMoreData.value) {
    fetchMessages(true)
  }
  
  lastScrollTop.value = windowScrollTop
}, 300)

onMounted(() => {
  initTheme()
  fetchMessages()
  
  // 添加滚动事件监听
  if (messagesContainer.value) {
    messagesContainer.value.addEventListener('scroll', handleScroll)
  }
  // 也监听窗口滚动，以防容器本身不滚动
  window.addEventListener('scroll', handleScroll)
})

onUnmounted(() => {
  // 移除滚动事件监听
  if (messagesContainer.value) {
    messagesContainer.value.removeEventListener('scroll', handleScroll)
  }
  window.removeEventListener('scroll', handleScroll)
})

</script>