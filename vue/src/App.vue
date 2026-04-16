<template>
  <div class="min-h-screen bg-[var(--bg-secondary)] dark:bg-gradient-to-b dark:from-[rgb(32,26,27)] dark:to-[rgb(65,32,68)] bg-fixed transition-colors">
    <Navbar />
    <div class="md:pl-16">
      <!-- Message 始终挂载，v-show 切显隐，滚动位置天然保留 -->
      <Message v-show="route.path === '/'" />
      <router-view v-slot="{ Component }">
        <Transition name="route" mode="out-in">
          <keep-alive :include="['Media', 'Actor']">
            <component :is="Component" />
          </keep-alive>
        </Transition>
      </router-view>
    </div>
    <BottomNavBar />
    <ToastContainer />
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './components/Navbar.vue'
import BottomNavBar from './components/BottomNavBar.vue'
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
