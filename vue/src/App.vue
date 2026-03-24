<template>
  <div class="min-h-screen bg-gradient-to-b from-[rgb(32,26,27)] to-[rgb(65,32,68)] dark:from-[rgb(32,26,27)] dark:to-[rgb(65,32,68)] bg-fixed transition-colors">
    <div v-if="!isOnline" class="fixed top-0 left-64 right-0 bg-red-600 text-white text-center py-2 z-50">
      您当前处于离线状态，部分功能可能受限
    </div>
    
    <Navbar />
    <div class="pl-64">
      <router-view v-slot="{ Component }">
        <keep-alive :include="['Media', 'Actor', 'ActorDetail', 'Message', 'Article', 'Home']">
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </div>
    <PwaInstallPrompt @install="handleInstall" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import Navbar from './components/Navbar.vue'
import PwaInstallPrompt from './components/PwaInstallPrompt.vue'

const handleInstall = (outcome: string) => {
  console.log('PWA installation outcome:', outcome)
}

const isOnline = ref(navigator.onLine)

const handleOnlineStatusChange = () => {
  isOnline.value = navigator.onLine
}

onMounted(() => {
  window.addEventListener('online', handleOnlineStatusChange)
  window.addEventListener('offline', handleOnlineStatusChange)
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnlineStatusChange)
  window.removeEventListener('offline', handleOnlineStatusChange)
})
</script>
