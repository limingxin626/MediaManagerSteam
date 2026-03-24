<template>
  <div v-if="showInstallButton" class="fixed bottom-6 right-6 z-50">
    <button 
      @click="installApp"
      class="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-full shadow-lg flex items-center space-x-2 transition-all hover:scale-105"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
      </svg>
      <span>安装应用</span>
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const emit = defineEmits(['install'])
const showInstallButton = ref(false)
let deferredPrompt: Event | null = null

const handleBeforeInstallPrompt = (e: Event) => {
  // 阻止Chrome 67及更早版本自动显示安装提示
  e.preventDefault()
  // 存储事件以便后续触发安装
  deferredPrompt = e
  // 显示安装按钮
  showInstallButton.value = true
}

const installApp = async () => {
  if (!deferredPrompt) return
  
  // 显示安装提示
  ;(deferredPrompt as any).prompt()
  
  // 等待用户响应
  const { outcome } = await (deferredPrompt as any).userChoice
  
  // 重置事件对象
  deferredPrompt = null
  
  // 隐藏安装按钮
  showInstallButton.value = false
  
  // 发送安装事件
  emit('install', outcome)
}

const handleAppInstalled = () => {
  // 应用已安装，隐藏安装按钮
  showInstallButton.value = false
  deferredPrompt = null
}

onMounted(() => {
  // 监听安装提示事件
  window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
  // 监听应用安装完成事件
  window.addEventListener('appinstalled', handleAppInstalled)
})

onUnmounted(() => {
  // 移除事件监听
  window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt)
  window.removeEventListener('appinstalled', handleAppInstalled)
})
</script>