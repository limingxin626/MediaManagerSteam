<template>
  <div class="min-h-screen pb-24 md:pb-8">
    <div class="max-w-7xl w-full mx-auto px-4 pt-6 space-y-4">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">主页</h1>

      <HeatmapCard />

      <TodoBoard />

      <RecentMedia />
    </div>
  </div>
</template>

<script setup lang="ts">
import HeatmapCard from '../components/dashboard/HeatmapCard.vue'
import TodoBoard from '../components/dashboard/TodoBoard.vue'
import RecentMedia from '../components/dashboard/RecentMedia.vue'

defineOptions({ name: 'Dashboard' })
</script>
