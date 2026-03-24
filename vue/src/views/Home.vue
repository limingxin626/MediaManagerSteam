<template>
  <div class="min-h-screen transition-colors">
    <!-- Hero Section -->
    <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <div class="text-center">
        <h2 class="text-5xl font-bold text-white mb-4">
          欢迎使用信息管理系统
        </h2>
        <p class="text-xl text-gray-300 mb-8">
          高效管理您的数据,轻松查看和编辑信息
        </p>
        <router-link 
          to="/actor" 
          class="inline-block bg-indigo-600 text-white px-8 py-3 rounded-lg text-lg font-semibold hover:bg-indigo-700 transition-colors shadow-lg hover:shadow-xl"
        >
          开始使用
        </router-link>
      </div>

      <!-- Feature Cards -->
      <div class="mt-20 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
        <router-link 
          to="/actor" 
          class="group bg-purple-900/30 backdrop-blur-sm p-8 rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-purple-700/50 hover:border-pink-500 hover:scale-105"
        >
          <div class="w-16 h-16 bg-gradient-to-br from-green-400 to-green-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-lg">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          </div>
          <h3 class="text-2xl font-bold text-white mb-3">人员管理</h3>
          <p class="text-gray-300 text-lg">管理团队成员信息和资料</p>
        </router-link>

        <router-link 
          to="/group" 
          class="group bg-purple-900/30 backdrop-blur-sm p-8 rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-purple-700/50 hover:border-pink-500 hover:scale-105"
        >
          <div class="w-16 h-16 bg-gradient-to-br from-blue-400 to-blue-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-lg">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 class="text-2xl font-bold text-white mb-3">分组管理</h3>
          <p class="text-gray-300 text-lg">组织和管理项目团队分组</p>
        </router-link>

        <router-link 
          to="/media" 
          class="group bg-purple-900/30 backdrop-blur-sm p-8 rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-purple-700/50 hover:border-pink-500 hover:scale-105"
        >
          <div class="w-16 h-16 bg-gradient-to-br from-purple-400 to-purple-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-lg">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 class="text-2xl font-bold text-white mb-3">媒体管理</h3>
          <p class="text-gray-300 text-lg">管理项目相关的媒体资源</p>
        </router-link>

        <router-link 
          to="/article" 
          class="group bg-purple-900/30 backdrop-blur-sm p-8 rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-purple-700/50 hover:border-pink-500 hover:scale-105"
        >
          <div class="w-16 h-16 bg-gradient-to-br from-orange-400 to-orange-600 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform shadow-lg">
            <svg class="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 class="text-2xl font-bold text-white mb-3">文章阅读</h3>
          <p class="text-gray-300 text-lg">浏览和阅读技术文章</p>
        </router-link>
      </div>

      <!-- Statistics Section -->
      <div class="mt-20 bg-purple-900/30 backdrop-blur-sm rounded-xl shadow-lg p-8 border border-purple-700/50 transition-colors">
        <h3 class="text-2xl font-bold text-white mb-8 text-center">系统统计</h3>
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          <div class="text-center">
            <div class="text-4xl font-bold text-indigo-400 mb-2">{{ totalRecords }}</div>
            <div class="text-gray-300">总记录数</div>
          </div>
          <div class="text-center">
            <div class="text-4xl font-bold text-green-400 mb-2">{{ activeUsers }}</div>
            <div class="text-gray-300">活跃用户</div>
          </div>
          <div class="text-center">
            <div class="text-4xl font-bold text-purple-400 mb-2">{{ todayUpdates }}</div>
            <div class="text-gray-300">今日更新</div>
          </div>
          <div class="text-center">
            <div class="text-4xl font-bold text-orange-400 mb-2">{{ categories }}</div>
            <div class="text-gray-300">数据分类</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="backdrop-blur-sm mt-20 transition-colors">
      <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <p class="text-center text-gray-300">
          © 2026 信息管理系统. All rights reserved.
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTheme } from '../composables/useTheme'

defineOptions({
  name: 'Home'
})

const { initTheme } = useTheme()

const totalRecords = ref(1248)
const activeUsers = ref(86)
const todayUpdates = ref(23)
const categories = ref(12)

onMounted(() => {
  initTheme()
})
</script>
