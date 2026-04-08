<template>
  <div class="min-h-screen bg-[var(--bg-secondary)] dark:bg-gradient-to-b dark:from-[rgb(32,26,27)] dark:to-[rgb(65,32,68)] bg-fixed transition-colors">
    <Navbar />
    <div class="md:pl-16">
      <router-view v-slot="{ Component }">
        <keep-alive :include="['Media', 'Actor', 'Message']">
          <component :is="Component" />
        </keep-alive>
      </router-view>
    </div>
    <BottomNavBar />
    <ToastContainer />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import Navbar from './components/Navbar.vue'
import BottomNavBar from './components/BottomNavBar.vue'
import ToastContainer from './components/ToastContainer.vue'
import { useTheme } from './composables/useTheme'

const { initTheme } = useTheme()

onMounted(() => {
  initTheme()
})
</script>
