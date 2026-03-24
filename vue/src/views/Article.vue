<template>
  <div class="transition-colors">
    <!-- Main Content -->
    <div class="w-full max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="flex gap-6 h-[calc(100vh-8rem)]">
        <!-- Left Sidebar - Article List -->
        <div class="w-80 flex-shrink-0">
          <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 h-full flex flex-col">
            <!-- Search -->
            <div class="p-4 border-b border-gray-200 dark:border-gray-700">
              <div class="relative">
                <input 
                  v-model="searchQuery"
                  type="text" 
                  placeholder="搜索文章..." 
                  class="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
                <svg class="absolute left-3 top-2.5 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            <!-- Article List -->
            <div class="flex-1 overflow-y-auto p-2">
              <div 
                v-for="article in filteredArticles" 
                :key="article.id"
                @click="selectArticle(article)"
                :class="[
                  'p-4 rounded-lg cursor-pointer transition-all mb-2',
                  selectedArticle?.id === article.id 
                    ? 'bg-indigo-50 dark:bg-indigo-900/30 border-2 border-indigo-500' 
                    : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700 border-2 border-transparent'
                ]"
              >
                <h3 class="font-semibold text-gray-900 dark:text-white mb-1 line-clamp-2">
                  {{ article.title }}
                </h3>
                <p class="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  {{ article.date }}
                </p>
              </div>

              <div v-if="filteredArticles.length === 0" class="text-center py-8">
                <p class="text-gray-500 dark:text-gray-400">没有找到文章</p>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Content - Article View -->
        <div class="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col">
          <div v-if="selectedArticle" class="h-full flex flex-col">
            <!-- Article Header -->
            <div class="p-6 border-b border-gray-200 dark:border-gray-700">
              <div class="flex items-start justify-between mb-3">
                <h1 class="text-3xl font-bold text-gray-900 dark:text-white flex-1">
                  {{ selectedArticle.title }}
                </h1>
                <div class="flex items-center gap-2 ml-4">
                  <button
                    v-if="!isEditing"
                    @click="startEditing"
                    class="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors flex items-center gap-2"
                  >
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                    编辑
                  </button>
                  <template v-else>
                    <button
                      @click="saveArticle"
                      class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
                    >
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                      </svg>
                      保存
                    </button>
                    <button
                      @click="cancelEditing"
                      class="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
                    >
                      取消
                    </button>
                  </template>
                </div>
              </div>
              <div class="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                <div class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <span>{{ selectedArticle.date }}</span>
                </div>
                <div v-if="selectedArticle.url" class="flex items-center gap-1">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  <a :href="selectedArticle.url" target="_blank" class="hover:text-indigo-600 dark:hover:text-indigo-400">
                    原文链接
                  </a>
                </div>
              </div>
            </div>

            <!-- Article Content - Edit/Preview Mode -->
            <div class="flex-1 overflow-hidden flex">
              <!-- Editor Mode -->
              <div v-if="isEditing" class="flex-1 flex gap-4 p-4">
                <!-- Markdown Editor -->
                <div class="flex-1 flex flex-col">
                  <div class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">Markdown 编辑</div>
                  <textarea
                    v-model="editContent"
                    class="flex-1 w-full p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
                    placeholder="在此输入 Markdown 内容..."
                  ></textarea>
                </div>
                
                <!-- Live Preview -->
                <div class="flex-1 flex flex-col">
                  <div class="mb-2 text-sm font-medium text-gray-700 dark:text-gray-300">实时预览</div>
                  <div class="flex-1 overflow-y-auto p-4 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-900">
                    <div 
                      class="prose prose-lg dark:prose-invert max-w-none
                             prose-headings:text-gray-900 dark:prose-headings:text-white
                             prose-p:text-gray-700 dark:prose-p:text-gray-300
                             prose-a:text-indigo-600 dark:prose-a:text-indigo-400
                             prose-code:text-pink-600 dark:prose-code:text-pink-400
                             prose-pre:bg-gray-100 dark:prose-pre:bg-gray-900
                             prose-img:rounded-lg prose-img:shadow-lg"
                      v-html="previewContent"
                    ></div>
                  </div>
                </div>
              </div>

              <!-- Preview Mode -->
              <div v-else ref="previewContainer" class="flex-1 overflow-y-auto p-6">
                <div 
                  class="prose prose-lg dark:prose-invert max-w-none
                       prose-headings:text-gray-900 dark:prose-headings:text-white
                       prose-p:text-gray-700 dark:prose-p:text-gray-300
                       prose-a:text-indigo-600 dark:prose-a:text-indigo-400
                       prose-code:text-pink-600 dark:prose-code:text-pink-400
                       prose-pre:bg-gray-100 dark:prose-pre:bg-gray-900
                       prose-img:rounded-lg prose-img:shadow-lg"
                  v-html="renderedContent"
                ></div>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else class="h-full flex items-center justify-center">
            <div class="text-center">
              <svg class="mx-auto h-16 w-16 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p class="text-lg text-gray-500 dark:text-gray-400">选择一篇文章开始阅读</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTheme } from '../composables/useTheme'
import { marked } from 'marked'

defineOptions({
  name: 'Article'
})

const { initTheme } = useTheme()

interface Article {
  id: number
  title: string
  filename: string
  date: string
  url?: string
  content?: string
}

const searchQuery = ref('')
const selectedArticle = ref<Article | null>(null)
const articles = ref<Article[]>([])
const isEditing = ref(false)
const editContent = ref('')
const originalContent = ref('')
const previewContainer = ref<HTMLElement | null>(null)

// Import all markdown files from the markdown folder
const markdownModules = import.meta.glob('/markdown/*.md', { as: 'raw', eager: true })

const filteredArticles = computed(() => {
  const query = searchQuery.value.toLowerCase()
  if (!query) return articles.value
  return articles.value.filter(article => 
    article.title.toLowerCase().includes(query)
  )
})

const renderedContent = computed(() => {
  if (!selectedArticle.value?.content) return ''
  
  // Remove frontmatter
  let content = selectedArticle.value.content
  if (content.startsWith('---')) {
    const endOfFrontmatter = content.indexOf('---', 3)
    if (endOfFrontmatter !== -1) {
      content = content.substring(endOfFrontmatter + 3).trim()
    }
  }
  
  // Fix relative image paths to absolute paths
  // Replace markdown image syntax: ![alt](images/xxx.png) -> ![alt](/markdown/images/xxx.png)
  content = content.replace(/!\[([^\]]*)\]\(images\/([^)]+)\)/g, '![$1](/markdown/images/$2)')
  
  return marked(content)
})

const previewContent = computed(() => {
  if (!editContent.value) return ''
  
  let content = editContent.value
  
  // Remove frontmatter for preview
  if (content.startsWith('---')) {
    const endOfFrontmatter = content.indexOf('---', 3)
    if (endOfFrontmatter !== -1) {
      content = content.substring(endOfFrontmatter + 3).trim()
    }
  }
  
  // Fix relative image paths
  content = content.replace(/!\[([^\]]*)\]\(images\/([^)]+)\)/g, '![$1](/markdown/images/$2)')
  
  return marked(content)
})

const selectArticle = (article: Article) => {
  selectedArticle.value = article
  isEditing.value = false
  // 重置预览区域滚动位置到顶部
  setTimeout(() => {
    if (previewContainer.value) {
      previewContainer.value.scrollTop = 0
    }
  }, 0)
}

const startEditing = () => {
  if (!selectedArticle.value?.content) return
  editContent.value = selectedArticle.value.content
  originalContent.value = selectedArticle.value.content
  isEditing.value = true
}

const cancelEditing = () => {
  editContent.value = originalContent.value
  isEditing.value = false
}

const saveArticle = async () => {
  if (!selectedArticle.value) return
  
  try {
    // TODO: 调用后端 API 保存文章
    // const response = await fetch('/api/articles/' + selectedArticle.value.id, {
    //   method: 'PUT',
    //   headers: { 'Content-Type': 'application/json' },
    //   body: JSON.stringify({
    //     filename: selectedArticle.value.filename,
    //     content: editContent.value
    //   })
    // })
    // 
    // if (!response.ok) throw new Error('保存失败')
    
    // 临时更新本地内容
    selectedArticle.value.content = editContent.value
    isEditing.value = false
    
    alert('保存成功！(注意: 这是临时保存在内存中，需要后端 API 支持才能持久化)')
  } catch (error) {
    console.error('保存文章失败:', error)
    alert('保存失败，请稍后重试')
  }
}

const parseFrontmatter = (content: string) => {
  const frontmatterRegex = /^---\n([\s\S]*?)\n---/
  const match = content.match(frontmatterRegex)
  
  if (!match || !match[1]) return {}
  
  const frontmatter: Record<string, string> = {}
  const lines = match[1].split('\n')
  
  for (const line of lines) {
    const colonIndex = line.indexOf(':')
    if (colonIndex > 0) {
      const key = line.substring(0, colonIndex).trim()
      const value = line.substring(colonIndex + 1).trim()
      frontmatter[key] = value
    }
  }
  
  return frontmatter
}

const loadArticles = async () => {
  const loadedArticles: Article[] = []
  let idCounter = 1
  
  for (const [path, content] of Object.entries(markdownModules)) {
    const filename = path.split('/').pop() || ''
    const frontmatter = parseFrontmatter(content as string)
    
    // Extract title from frontmatter or filename
    let title = frontmatter.title || filename.replace('.md', '')
    // Remove extra info after |
    if (title && title.includes('|')) {
      title = title.split('|')[0].trim()
    }
    
    // Extract date from frontmatter or use current date
    let date = '2022-11-30'
    if (frontmatter.date) {
      try {
        const parsedDate = new Date(frontmatter.date)
        date = parsedDate.toISOString().split('T')[0]
      } catch {
        date = '2022-11-30'
      }
    }
    
    loadedArticles.push({
      id: idCounter++,
      title,
      filename,
      date,
      url: frontmatter.url,
      content: content as string
    })
  }
  
  articles.value = loadedArticles
  
  // Auto-select first article if available
  if (articles.value.length > 0 && articles.value[0]) {
    selectArticle(articles.value[0])
  }
}

onMounted(() => {
  initTheme()
  loadArticles()
})

</script>

<style scoped>
/* Hide custom scrollbar for article list */
.overflow-y-auto::-webkit-scrollbar {
  display: none;
}

.overflow-y-auto {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
