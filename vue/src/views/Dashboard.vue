<template>
  <div class="min-h-screen pb-24 md:pb-8">
    <div class="max-w-7xl w-full mx-auto px-4 pt-6 space-y-4">
      <h1 class="text-xl font-bold text-gray-900 dark:text-white">主页</h1>

      <TodoBoard />

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div class="lg:col-span-2">
          <RecentMedia />
        </div>
        <div>
          <StatsCard />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import TodoBoard from '../components/dashboard/TodoBoard.vue'
import RecentMedia from '../components/dashboard/RecentMedia.vue'
import StatsCard from '../components/dashboard/StatsCard.vue'
</script>
