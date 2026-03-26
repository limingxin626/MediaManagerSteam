<template>
  <div class="min-h-screen flex flex-col items-center justify-center text-gray-500 dark:text-gray-400">
    <h1 class="text-6xl font-bold mb-4">404</h1>
    <p class="text-lg mb-8">页面不存在</p>
    <router-link
      to="/"
      class="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
    >
      返回首页
    </router-link>
  </div>
</template>

<script setup lang="ts">
defineOptions({ name: 'NotFound' })
</script>
