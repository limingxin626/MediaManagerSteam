<template>
  <div class="flex h-screen flex-col overflow-hidden bg-[var(--bg-secondary)] dark:bg-[var(--bg-primary)] bg-fixed transition-colors">
    <div class="flex min-h-0 flex-1">
      <Navbar />
      <main class="min-w-0 flex-1 overflow-hidden">
      <!-- Message 始终挂载，v-show 切显隐，滚动位置天然保留 -->
      <Message v-show="route.path === '/messages'" />
      <router-view v-slot="{ Component }">
        <Transition name="route" mode="out-in">
          <keep-alive :include="['Dashboard', 'Media', 'Folder', 'Collection', 'People']">
            <component :is="Component" />
          </keep-alive>
        </Transition>
      </router-view>
      </main>
    </div>
    <ToastContainer />
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './components/Navbar.vue'
import ToastContainer from './components/ToastContainer.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
import Message from './views/Message.vue'
import { useTheme } from './composables/useTheme'

const route = useRoute()
const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})
</script>
