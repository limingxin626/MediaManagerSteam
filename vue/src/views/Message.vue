<template>
  <div class="h-screen flex transition-colors">
    <!-- Left Tag Column -->
    <div class="flex flex-col w-48 shrink-0 border-r border-[var(--border-color)] overflow-y-auto">
      <div class="px-3 pt-4 pb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider shrink-0">标签</div>
      <div class="flex flex-col gap-0.5 px-2 pb-4">
        <button @click="selectTag(null)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left" :class="selectedTagId === null && selectedActorId === null
            ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
          <span>全部</span>
        </button>
        <div v-for="(parentTag, index) in tagTree" :key="index" class="flex flex-col gap-0.5">
          <!-- 一级标签 -->
          <button @click="selectTag(parentTag.id)"
            class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left" :class="selectedTagId === parentTag.id
              ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
              : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'">
            <span class="truncate">{{ parentTag.name }}</span>
            <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ parentTag.message_count }}</span>
          </button>
          <!-- 二级标签 -->
          <div v-if="parentTag.children && parentTag.children.length > 0" class="pl-6 flex flex-col gap-0.5">
            <button v-for="childTag in parentTag.children" :key="childTag.id" @click="selectTag(childTag.id)"
              class="flex items-center justify-between px-3 py-1.5 rounded-lg text-sm transition-colors text-left" :class="selectedTagId === childTag.id
                ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
                : 'text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-white/10'">
              <span class="truncate">{{ childTag.name }}</span>
              <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ childTag.message_count }}</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Actor List -->
      <div class="px-3 pt-4 pb-2 text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider shrink-0">演员</div>
      <div class="flex flex-col gap-0.5 px-2 pb-4">
        <button
          v-if="noActorCount > 0 || selectedActorId === 0"
          @click="selectActor(0)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left"
          :class="selectedActorId === 0
            ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'"
        >
          <span class="truncate">无</span>
          <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ noActorCount }}</span>
        </button>
        <button
          v-for="actor in actors"
          :key="actor.id"
          @click="selectActor(actor.id)"
          class="flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors text-left"
          :class="selectedActorId === actor.id
            ? 'bg-[var(--color-primary-600)]/30 text-[var(--color-primary-600)] dark:text-[var(--color-primary-500)]'
            : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10'"
        >
          <span class="truncate">{{ actor.name }}</span>
          <span class="ml-1 text-xs text-gray-400 dark:text-gray-500 shrink-0">{{ actor.message_count }}</span>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex min-w-0">
      <!-- Left Feed Section -->
      <div class="flex flex-col min-w-0 relative" :class="selectedMessage ? 'w-1/2' : 'flex-1'">
        <!-- Search Header -->
        <div class="shrink-0 border-b border-[var(--border-color)] shadow-sm">
          <div class="w-full mx-auto px-3 py-3">
            <div class="flex gap-2 items-center max-w-4xl mx-auto">
              <h2 class="text-lg font-bold text-gray-900 dark:text-white">消息流</h2>
              <!-- Merge toggle -->
              <button @click="toggleMergeMode" class="px-2 py-1 text-xs rounded-md transition-colors" :class="mergeMode
                ? 'bg-[var(--color-primary-600)] text-white hover:bg-[var(--color-primary-700)]'
                : 'bg-gray-100 dark:bg-white/10 text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-white/20'">
                {{ mergeMode ? '取消合并' : '合并' }}
              </button>
              <!-- Starred filter -->
              <button @click="starredFilter = !starredFilter; resetAndFetch()"
                class="p-1 rounded-md transition-colors" :class="starredFilter
                  ? 'text-yellow-400 bg-yellow-900/20'
                  : 'text-gray-400 hover:text-yellow-400 bg-gray-100 dark:bg-white/10'" title="仅看收藏">
                <svg class="w-4 h-4" :fill="starredFilter ? 'currentColor' : 'none'" stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
              <!-- Search -->
              <SearchInput v-model="searchQuery" placeholder="搜索消息..." @search="onSearch" />
            </div>
          </div>
        </div>

        <!-- Scrollable Content Area -->
        <div ref="scrollContainer" class="flex-1 overflow-y-auto min-h-0 relative">
          <!-- Floating date badge (clickable to open calendar) -->
          <div v-if="currentVisibleDate" class="sticky top-0 z-20 flex justify-center py-2">
            <div class="relative">
              <button @click="toggleCalendar"
                class="px-3 py-1 text-xs text-[var(--text-secondary)] bg-[var(--bg-card)]/80 dark:bg-white/10 backdrop-blur-md rounded-full border border-[var(--border-color)] shadow-sm hover:bg-[var(--bg-card)] dark:hover:bg-white/20 transition-colors cursor-pointer flex items-center gap-1">
                <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                {{ currentVisibleDate }}
              </button>
              <!-- Calendar popover -->
              <div v-show="calendarOpen" ref="calendarPopover"
                class="absolute top-full left-1/2 -translate-x-1/2 mt-2 z-50 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-xl shadow-xl p-3"
                @focusin.stop @focusout.stop>
                <Calendar
                  :attributes="calendarAttributes"
                  :is-dark="isDark"
                  @update:pages="onCalendarPageChange"
                  @dayclick="onCalendarDayClick"
                  borderless
                  transparent
                />
              </div>
            </div>
          </div>
          <!-- Scroll sentinel for loading older messages -->
          <div ref="topSentinel" class="h-1"></div>

          <div class="w-full mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <!-- Loading skeleton (initial load) -->
            <div v-if="loading && messages.length === 0" class="flex flex-col gap-4 max-w-4xl mx-auto">
              <div v-for="i in 3" :key="i"
                class="bg-[var(--bg-card)] rounded-xl border border-[var(--border-color)] p-4 animate-pulse">
                <div class="flex items-center gap-3 mb-3">
                  <div class="w-10 h-10 rounded-full bg-gray-200 dark:bg-white/10"></div>
                  <div class="flex-1">
                    <div class="h-4 w-20 bg-gray-200 dark:bg-white/10 rounded"></div>
                    <div class="h-3 w-16 bg-gray-200 dark:bg-white/10 rounded mt-1.5"></div>
                  </div>
                </div>
                <div class="aspect-video bg-gray-200 dark:bg-white/10 rounded-xl mb-2"></div>
                <div class="h-3 w-3/4 bg-gray-200 dark:bg-white/10 rounded"></div>
                <div class="h-3 w-1/2 bg-gray-200 dark:bg-white/10 rounded mt-1.5"></div>
              </div>
            </div>
            <div v-if="loading && messages.length > 0" class="text-center py-4">
              <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
            </div>

            <!-- No more data -->
            <div v-if="!loading && !hasMoreData && messages.length > 0" class="text-center py-8">
              <p class="text-sm text-gray-400">已经到底了</p>
            </div>

            <!-- Messages Feed -->
            <div v-if="messages.length > 0" class="flex flex-col gap-4 max-w-3xl mx-auto">
              <template v-for="(message, idx) in messages" :key="message.id">
                <!-- Date separator -->
                <div v-if="idx === 0 || getDateStr(message.created_at) !== getDateStr(messages[idx - 1]?.created_at ?? '')"
                  class="flex justify-center py-2">
                  <span class="px-3 py-1 text-xs text-[var(--text-secondary)] bg-[var(--bg-card)]/80 dark:bg-white/10 backdrop-blur-md rounded-full border border-[var(--border-color)] shadow-sm">{{ formatDateLabel(message.created_at) }}</span>
                </div>
                <div :data-message-id="message.id" :data-message-date="message.created_at.substring(0, 10)">
                  <MessageCard :message="message" :media-items="message.media_items" :tags="message.tags"
                    :all-tags="tags"
                    :selectable="mergeMode" :selected="selectedMessageIds.has(message.id)"
                    @click="handleMessageClick(message)" @media-click="(index) => handleMediaClick(message.id, index)"
                    @delete="handleDeleteMessage" @find-messages-by-media="handleFindMessagesByMedia"
                    @toggle-select="toggleSelectMessage" @toggle-star="handleToggleStar"
                    @toggle-media-star="(mediaId, msgId) => handleToggleMediaStar(mediaId, msgId)" @edit="openEditDialog"
                    @add-tag="handleQuickAddTag" />
                </div>
              </template>
            </div>

            <!-- Empty State -->
            <div v-if="messages.length === 0 && !loading" class="flex flex-col items-center justify-center py-20">
              <div class="relative w-24 h-24 mb-4">
                <div class="absolute inset-0 rounded-2xl bg-[var(--color-primary-500)]/10 rotate-6"></div>
                <div class="absolute inset-0 rounded-2xl bg-[var(--color-primary-500)]/5 -rotate-3"></div>
                <div class="absolute inset-0 flex items-center justify-center">
                  <svg class="w-10 h-10 text-[var(--color-primary-500)]/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                      d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                  </svg>
                </div>
              </div>
              <h3 class="text-sm font-medium text-[var(--text-primary)]">暂无消息</h3>
              <p class="mt-1 text-sm text-[var(--text-muted)]">还没有任何消息内容</p>
            </div>

            <!-- Loading indicator (bottom, for loading newer) -->
            <div v-if="loadingForward" class="text-center py-4">
              <div class="inline-block animate-spin rounded-full h-6 w-6 border-t-2 border-b-2 border-[var(--color-primary-500)]"></div>
            </div>
          </div>

          <!-- Scroll sentinel for loading newer messages -->
          <div ref="bottomSentinel" class="h-1"></div>

          <!-- Merge action bar -->
          <div v-if="mergeMode && selectedMessageIds.size > 0"
            class="sticky bottom-4 z-50 flex items-center justify-center pointer-events-none">
            <div
              class="pointer-events-auto flex items-center gap-3 px-5 py-3 bg-gray-900/90 backdrop-blur-sm rounded-full shadow-xl text-white text-sm">
              <span>已选 {{ selectedMessageIds.size }} 条</span>
              <button @click="handleMerge" :disabled="selectedMessageIds.size < 2"
                class="px-4 py-1.5 bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-700)] disabled:bg-gray-600 rounded-full font-medium transition-colors">
                合并
              </button>
              <button @click="toggleMergeMode"
                class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded-full transition-colors">
                取消
              </button>
            </div>
          </div>

          <!-- "回到最新" floating button -->
          <button v-if="isViewingHistory" @click="backToLatest"
            class="sticky bottom-4 left-full -translate-x-6 z-50 flex items-center gap-2 px-4 py-2 bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-700)] text-white text-sm font-medium rounded-full shadow-lg transition-colors w-fit ml-auto mr-6">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
            回到最新
          </button>
        </div>

        <!-- Bottom Input Bar -->
        <div class="shrink-0 px-4 py-3 border-t border-[var(--border-color)] mb-20 md:mb-0">
          <div class="max-w-4xl mx-auto">
            <button @click="openCreateDialog"
              class="w-full flex items-center gap-3 px-4 py-3 bg-[var(--bg-card)] border border-[var(--border-color)] rounded-full text-sm text-[var(--text-muted)] hover:border-[var(--color-primary-500)] transition-colors cursor-text">
              <span class="flex-1 text-left">写点什么...</span>
              <svg class="w-5 h-5 text-[var(--color-primary-500)]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      <!-- Right Detail Panel -->
      <div v-if="selectedMessage" class="flex-1 min-w-0 border-l border-[var(--border-color)] flex flex-col overflow-hidden">
        <!-- Header -->
        <div class="px-4 py-3 border-b border-[var(--border-color)] flex items-center justify-between shrink-0">
          <div class="flex flex-col min-w-0">
            <span class="text-sm font-semibold text-gray-900 dark:text-white">消息详情</span>
            <span class="text-xs text-gray-500 dark:text-gray-400">{{ formatDateLabel(selectedMessage.created_at) }}</span>
          </div>
          <div class="flex items-center gap-1">
            <button @click="handleDetailToggleStar"
              class="p-1.5 rounded transition-colors" :class="selectedMessage.starred
                ? 'text-yellow-400'
                : 'text-gray-400 hover:text-yellow-400'"
              title="收藏">
              <svg class="w-4 h-4" :fill="selectedMessage.starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            </button>
            <button @click="openEditDialog(selectedMessage.id)"
              class="p-1.5 rounded text-gray-400 hover:text-blue-400 transition-colors" title="编辑">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button @click="handleDetailDelete"
              class="p-1.5 rounded text-gray-400 hover:text-red-400 transition-colors" title="删除">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
            <div class="w-px h-4 bg-[var(--border-color)] mx-0.5"></div>
            <button v-if="selectedMessage.media_items && selectedMessage.media_items.length > 1"
              @click="toggleSplitMode"
              class="p-1.5 rounded transition-colors" :class="splitMode
                ? 'text-[var(--color-primary-500)]'
                : 'text-gray-400 hover:text-gray-200'"
              :title="splitMode ? '退出拆分' : '拆分媒体'">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h8M8 12h4m-4 5h8M4 4v16m16-16v16" />
              </svg>
            </button>
            <div v-if="selectedMessageLoading"
              class="inline-block animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-[var(--color-primary-500)]">
            </div>
            <button @click="selectedMessage = null"
              class="p-1.5 text-gray-400 hover:text-gray-200 rounded transition-colors" title="关闭">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        <!-- Scrollable body -->
        <div class="flex-1 overflow-y-auto p-4 flex flex-col gap-5">
          <!-- Actor -->
          <div v-if="selectedMessage.actor_name" class="flex items-center gap-2.5">
            <img :src="resolveUrl(`/data/actor_cover/${selectedMessage.actor_id}.webp`)"
              class="w-8 h-8 rounded-full object-cover bg-gray-700"
              @error="($event.target as HTMLImageElement).style.display = 'none'" />
            <span class="text-sm font-medium text-gray-800 dark:text-gray-200">{{ selectedMessage.actor_name }}</span>
          </div>
          <!-- Full text -->
          <div v-if="selectedMessage.text"
            class="prose dark:prose-invert prose-sm max-w-none text-gray-700 dark:text-gray-300 leading-relaxed"
            v-html="renderDetailText(selectedMessage.text)">
          </div>
          <!-- Tags -->
          <div v-if="selectedMessage.tags && selectedMessage.tags.length > 0" class="flex flex-wrap gap-1.5">
            <span v-for="t in selectedMessage.tags" :key="t.id"
              class="tag-chip">
              {{ t.name }}
            </span>
          </div>
          <!-- All media -->
          <div v-if="selectedMessage.media_items && selectedMessage.media_items.length > 0"
            :class="[
              'grid gap-1.5',
              selectedMessage.media_items.length === 1 ? 'grid-cols-1' :
              selectedMessage.media_items.length === 2 ? 'grid-cols-2' : 'grid-cols-3'
            ]">
            <div v-for="(media, index) in selectedMessage.media_items" :key="media.id"
              class="group aspect-square overflow-hidden relative rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
              :class="splitMode && splitSelectedIds.has(media.id) ? 'ring-2 ring-[var(--color-primary-500)]' : ''"
              @click="handleSelectedMessageMediaClick(index)">
              <img :src="resolveUrl(media.thumb_url)" class="w-full h-full object-cover" />
              <div v-if="splitMode"
                class="absolute top-1 left-1 w-5 h-5 rounded-full border-2 flex items-center justify-center"
                :class="splitSelectedIds.has(media.id)
                  ? 'bg-[var(--color-primary-500)] border-[var(--color-primary-500)]'
                  : 'border-white/70 bg-black/30'">
                <svg v-if="splitSelectedIds.has(media.id)" class="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div v-if="media.mime_type && media.mime_type.startsWith('video')"
                class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div class="w-8 h-8 bg-black/40 rounded-full flex items-center justify-center border border-white/30">
                  <svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
              </div>
              <div v-if="media.duration_ms"
                class="absolute bottom-1 right-1 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
                {{ formatDuration(media.duration_ms) }}
              </div>
              <button @click.stop="handleToggleMediaStar(media.id)"
                class="absolute top-1 right-1 p-1 rounded-full transition-all" :class="media.starred
                  ? 'text-yellow-400'
                  : 'text-white/70 hover:text-yellow-400 opacity-0 group-hover:opacity-100'">
                <svg class="w-4 h-4" :fill="media.starred ? 'currentColor' : 'none'" stroke="currentColor"
                  viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                    d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
            </div>
          </div>
          <!-- Split action bar -->
          <div v-if="splitMode && splitSelectedIds.size > 0"
            class="flex items-center justify-between bg-[var(--color-primary-500)]/10 border border-[var(--color-primary-500)]/30 rounded-lg px-3 py-2">
            <span class="text-sm text-[var(--color-primary-400)]">已选 {{ splitSelectedIds.size }} 项</span>
            <div class="flex gap-2">
              <button @click="toggleSplitMode"
                class="px-3 py-1 text-sm text-gray-400 hover:text-white transition-colors">取消</button>
              <button @click="handleSplit"
                class="px-3 py-1 text-sm bg-[var(--color-primary-500)] text-white rounded hover:bg-[var(--color-primary-600)] transition-colors">
                确认拆分
              </button>
            </div>
          </div>
        </div>
      </div>

      <MessageComposeDialog :visible="dialogVisible" :mode="dialogMode" :message-id="dialogMessageId"
        :initial-text="dialogInitialText" :initial-date="dialogInitialDate" :initial-media="dialogInitialMedia"
        :initial-tags="dialogInitialTags"
        :all-tags="tags" :tag-id="selectedTagId ?? null" :actor-id="selectedActorId ?? undefined" @close="dialogVisible = false"
        @created="onDialogCreated" @updated="onDialogUpdated" @media-changed="onMediaChanged" />

      <MediaPreview :is-open="previewOpen" :items="previewItems" :start-index="previewStartIndex"
        :starred="previewMessageStarred" :message-id="previewMessageId" :all-tags="tags" @close="closePreview" @navigate-prev="navigateToPrevMessage"
        @navigate-next="navigateToNextMessage" @toggle-star="handlePreviewToggleStar" @media-deleted="handleMediaDeleted"
        @media-rotated="handleMediaRotated" @media-tags-changed="handleMediaTagsChanged" />

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { renderMarkdown } from '../utils/markdown'
import { Calendar } from 'v-calendar'
import 'v-calendar/style.css'
import { type Actor, type MessageDetail, type MessageMediaItem, type TagWithCount } from '../types'
import MessageCard from '../components/MessageCard.vue'
import MediaPreview from '../components/MediaPreview.vue'
import SearchInput from '../components/SearchInput.vue'
import MessageComposeDialog from '../components/MessageComposeDialog.vue'
import { api } from '../composables/useApi'
import { useToast } from '../composables/useToast'
import { useConfirm } from '../composables/useConfirm'
import { resolveUrl, formatDuration, toggleMediaStar } from '../utils/media'
import { formatDateLabel } from '../utils/date'
import { useTheme } from '../composables/useTheme'


defineOptions({ name: 'Message' })

const route = useRoute()
const pendingRestore = ref<{ messageId: number; scrollOffset: number } | null>(null)

const toast = useToast()
const { confirm } = useConfirm()
const { theme } = useTheme()
const isDark = computed(() => theme.value === 'dark')

// --- Calendar date jump ---
const calendarOpen = ref(false)
const calendarPopover = ref<HTMLElement | null>(null)
const calendarDatesCache = new Map<string, Set<string>>() // "YYYY-MM" -> Set of "YYYY-MM-DD"
let calendarAttributesUpdating = false

const calendarAttributes = ref<Array<{ key: string; dot: { color: string }; dates: Date[] }>>([])

const toggleCalendar = () => {
  calendarOpen.value = !calendarOpen.value
}

const loadCalendarMonth = async (year: number, month: number) => {
  const key = `${year}-${String(month).padStart(2, '0')}`
  if (calendarDatesCache.has(key)) {
    return
  }
  try {
    const data = await api.get<{ dates: Array<{ date: string; count: number }> }>('/messages/dates', {
      year,
      month,
      tag_id: selectedTagId.value ?? undefined,
      actor_id: selectedActorId.value ?? undefined,
      query_text: searchQuery.value || undefined,
    })
    const dateSet = new Set(data.dates.map(d => d.date))
    calendarDatesCache.set(key, dateSet)
    updateCalendarAttributes()
  } catch {
    // silent fail
  }
}

const updateCalendarAttributes = () => {
  if (calendarAttributesUpdating) return
  calendarAttributesUpdating = true
  const dotDates: Date[] = []
  for (const [, dateSet] of calendarDatesCache) {
    for (const dateStr of dateSet) {
      dotDates.push(new Date(dateStr + 'T12:00:00'))
    }
  }
  calendarAttributes.value = dotDates.length > 0
    ? [{ key: 'messages', dot: { color: 'indigo' }, dates: dotDates }]
    : []
  queueMicrotask(() => { calendarAttributesUpdating = false })
}

const onCalendarPageChange = (pages: Array<{ year: number; month: number }>) => {
  for (const page of pages) {
    loadCalendarMonth(page.year, page.month)
  }
}

const onCalendarDayClick = (day: { id: string; date: Date }) => {
  // day.id is "YYYY-MM-DD"
  const monthKey = day.id.substring(0, 7)
  const dateSet = calendarDatesCache.get(monthKey)
  if (!dateSet || !dateSet.has(day.id)) return // disabled date

  calendarOpen.value = false
  jumpToDate(day.id)
}

const jumpToDate = async (dateStr: string) => {
  // Use end-of-day as cursor to get messages from this date (desc order)
  const cursor = `${dateStr}T23:59:59.999999`
  loading.value = true
  try {
    const data = await api.get<{ items: MessageDetail[]; next_cursor: string | null; has_more: boolean }>(
      '/messages/with-detail',
      {
        limit: pageSize,
        cursor,
        query_text: searchQuery.value || undefined,
        media_id: activeMediaFilter.value ?? undefined,
        starred: starredFilter.value || undefined,
        tag_id: selectedTagId.value ?? undefined,
        actor_id: selectedActorId.value ?? undefined,
      },
    )

    hasMoreData.value = data.has_more
    nextCursor.value = data.next_cursor
    messages.value = data.items.reverse()

    // Enable forward scrolling from the last message's time
    if (messages.value.length > 0) {
      const lastMsg = messages.value[messages.value.length - 1]
      forwardCursor.value = lastMsg.created_at
      hasMoreForward.value = true
      isViewingHistory.value = true
    }

    await nextTick()
    // Scroll to bottom where the target date's messages are
    scrollToBottom('auto')
  } catch {
    toast.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

// Close calendar on outside click
const onDocumentClick = (e: MouseEvent) => {
  if (calendarOpen.value && calendarPopover.value && !calendarPopover.value.contains(e.target as Node)) {
    // Check if click was on the toggle button
    const btn = calendarPopover.value.parentElement?.querySelector('button')
    if (btn && btn.contains(e.target as Node)) return
    calendarOpen.value = false
  }
}

const tags = ref<TagWithCount[]>([])
const selectedTagId = ref<number | null>(null)

const actors = ref<Actor[]>([])
const noActorCount = ref(0)
const selectedActorId = ref<number | null>(null)

interface FilterScrollCache {
  messageId: number
  scrollOffset: number
  nextCursor: string | null
  cachedMessages: MessageDetail[]
  hasMoreData: boolean
  forwardCursor: string | null
  hasMoreForward: boolean
}

const scrollPositionCache = new Map<string, FilterScrollCache>()

const getFilterKey = (): string => {
  if (selectedTagId.value !== null) return `tag:${selectedTagId.value}`
  if (selectedActorId.value !== null) return `actor:${selectedActorId.value}`
  return 'all'
}

const getFirstVisibleMessageId = (): { messageId: number; scrollOffset: number } | null => {
  const container = scrollContainer.value
  if (!container) return null
  const containerRect = container.getBoundingClientRect()
  const elements = container.querySelectorAll<HTMLElement>('[data-message-id]')
  for (const el of elements) {
    const rect = el.getBoundingClientRect()
    if (rect.bottom > containerRect.top) {
      return { messageId: parseInt(el.dataset.messageId!), scrollOffset: rect.top - containerRect.top }
    }
  }
  return null
}

const saveScrollPosition = () => {
  const visible = getFirstVisibleMessageId()
  if (!visible) return
  const key = getFilterKey()
  scrollPositionCache.set(key, {
    messageId: visible.messageId,
    scrollOffset: visible.scrollOffset,
    nextCursor: nextCursor.value,
    cachedMessages: [...messages.value],
    hasMoreData: hasMoreData.value,
    forwardCursor: forwardCursor.value,
    hasMoreForward: hasMoreForward.value,
  })
}

const restoreFromCache = (key: string): boolean => {
  const cached = scrollPositionCache.get(key)
  if (!cached) return false
  messages.value = [...cached.cachedMessages]
  nextCursor.value = cached.nextCursor
  hasMoreData.value = cached.hasMoreData
  forwardCursor.value = cached.forwardCursor
  hasMoreForward.value = cached.hasMoreForward
  isViewingHistory.value = false
  nextTick(() => {
    const container = scrollContainer.value
    if (!container) return
    const el = container.querySelector<HTMLElement>(`[data-message-id="${cached.messageId}"]`)
    if (el) {
      const containerRect = container.getBoundingClientRect()
      const elRect = el.getBoundingClientRect()
      container.scrollTo({ top: container.scrollTop + (elRect.top - containerRect.top) - cached.scrollOffset, behavior: 'auto' })
    }
  })
  return true
}

const SCROLL_POS_KEY = 'msg_scroll_pos'

const saveScrollPositionToStorage = () => {
  const visible = getFirstVisibleMessageId()
  if (!visible || messages.value.length === 0) return
  const msg = messages.value.find(m => m.id === visible.messageId)
  if (!msg) return
  localStorage.setItem(SCROLL_POS_KEY, JSON.stringify({
    messageId: msg.id,
    createdAt: msg.created_at,
    scrollOffset: visible.scrollOffset,
  }))
}

let scrollSaveTimer: ReturnType<typeof setTimeout> | null = null
const debouncedSaveToStorage = () => {
  if (scrollSaveTimer) clearTimeout(scrollSaveTimer)
  scrollSaveTimer = setTimeout(saveScrollPositionToStorage, 500)
}

const fetchTags = async () => {
  try {
    tags.value = await api.get<TagWithCount[]>('/tags')
  } catch {
    // Tags are non-critical; silent fail
  }
}

const fetchActors = async () => {
  try {
    const data = await api.get<{ items: Actor[]; no_actor_count: number }>('/actors')
    actors.value = data.items
    noActorCount.value = data.no_actor_count
  } catch {
    // silent fail
  }
}

const selectTag = (tagId: number | null) => {
  if (tagId !== null && tagId < 0) {
    return
  }
  saveScrollPosition()
  selectedTagId.value = tagId
  selectedActorId.value = null
  if (!restoreFromCache(getFilterKey())) {
    resetAndFetch()
  }
}

const selectActor = (actorId: number | null) => {
  saveScrollPosition()
  selectedActorId.value = actorId
  selectedTagId.value = null
  if (!restoreFromCache(getFilterKey())) {
    resetAndFetch()
  }
}

// 计算标签树结构，支持二级标签
const tagTree = computed(() => {
  const tagMap = new Map<number, TagWithCount & { children?: TagWithCount[] }>()
  const rootTags: (TagWithCount & { children?: TagWithCount[] })[] = []
  const virtualParentTags = new Map<string, TagWithCount & { children?: TagWithCount[] }>()
  
  // 首先将所有标签放入映射
  tags.value.forEach(tag => {
    tagMap.set(tag.id, { ...tag, children: [] })
  })
  
  // 构建树形结构
  tags.value.forEach(tag => {
    const parts = tag.name.split('/')
    if (parts.length === 1) {
      // 一级标签
      rootTags.push(tagMap.get(tag.id)!)
    } else if (parts.length === 2) {
      // 二级标签，找到对应的一级标签
      const parentName = parts[0]
      let parentTag = tags.value.find(t => t.name === parentName)
      
      if (parentTag && tagMap.has(parentTag.id)) {
        // 一级标签存在
        tagMap.get(parentTag.id)!.children!.push(tag)
      } else {
        // 一级标签不存在，创建虚拟一级标签
        if (!virtualParentTags.has(parentName)) {
          const virtualTag: TagWithCount & { children?: TagWithCount[] } = {
            id: -1, // 虚拟标签，使用负数 ID
            name: parentName,
            message_count: 0, // 虚拟标签的消息数为 0
            children: []
          }
          virtualParentTags.set(parentName, virtualTag)
          rootTags.push(virtualTag)
        }
        // 将二级标签添加到虚拟一级标签下
        virtualParentTags.get(parentName)!.children!.push(tag)
      }
    } else {
      // 超过二级的标签，作为一级标签处理
      rootTags.push(tagMap.get(tag.id)!)
    }
  })
  
  // 按消息数量降序排序，数量相同则按名称排序
  rootTags.sort((a, b) => {
    if (b.message_count !== a.message_count) {
      return b.message_count - a.message_count
    }
    return a.name.localeCompare(b.name)
  })
  rootTags.forEach(tag => {
    if (tag.children) {
      tag.children.sort((a, b) => {
        if (b.message_count !== a.message_count) {
          return b.message_count - a.message_count
        }
        return a.name.localeCompare(b.name)
      })
    }
  })
  
  return rootTags
})

const messages = ref<MessageDetail[]>([])
const loading = ref(false)
const searchQuery = ref('')

const pageSize = 20
const hasMoreData = ref(true)
const nextCursor = ref<string | null>(null)
const activeMediaFilter = ref<number | null>(null)
const starredFilter = ref(false)

const scrollContainer = ref<HTMLElement | null>(null)
const topSentinel = ref<HTMLElement | null>(null)
const bottomSentinel = ref<HTMLElement | null>(null)

const previewOpen = ref(false)
const previewItems = ref<MessageMediaItem[]>([])
const previewStartIndex = ref(0)
const previewMessageId = ref<number | undefined>(undefined)
const currentMessageIndex = ref(-1)
const selectedMessage = ref<MessageDetail | null>(null)
const selectedMessageLoading = ref(false)

const previewMessageStarred = computed(() => {
  if (currentMessageIndex.value < 0) return false
  return messages.value[currentMessageIndex.value]?.starred ?? false
})


// --- Merge selection mode ---
const mergeMode = ref(false)
const selectedMessageIds = ref<Set<number>>(new Set())

// --- Split mode ---
const splitMode = ref(false)
const splitSelectedIds = ref<Set<number>>(new Set())

// --- Forward (newer) pagination state ---
const forwardCursor = ref<string | null>(null)
const hasMoreForward = ref(false)
const loadingForward = ref(false)
const isViewingHistory = ref(false)

// --- Scroll helpers ---

const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
  const el = scrollContainer.value
  if (el) el.scrollTo({ top: el.scrollHeight, behavior })
}

const fetchForwardMessages = async () => {
  if (loadingForward.value || !hasMoreForward.value || !forwardCursor.value) return

  loadingForward.value = true
  try {
    const data = await api.get<{
      items: MessageDetail[]
      next_cursor: string | null
      has_more: boolean
    }>('/messages/with-detail', {
      cursor: forwardCursor.value,
      direction: 'forward',
      limit: pageSize,
      query_text: searchQuery.value || undefined,
      media_id: activeMediaFilter.value ?? undefined,
      starred: starredFilter.value || undefined,
      tag_id: selectedTagId.value ?? undefined,
      actor_id: selectedActorId.value ?? undefined,
    })

    const container = scrollContainer.value
    const previousScrollY = container?.scrollTop ?? 0
    const previousHeight = container?.scrollHeight ?? 0

    messages.value.push(...data.items)
    hasMoreForward.value = data.has_more
    forwardCursor.value = data.next_cursor

    if (!data.has_more) {
      isViewingHistory.value = false
    }

    await nextTick()
    if (container) {
      const scrollDelta = container.scrollHeight - previousHeight
      if (scrollDelta > 0 && previousScrollY + container.clientHeight < previousHeight) {
        container.scrollTo({ top: previousScrollY, behavior: 'auto' })
      }
    }
  } catch {
    toast.error('加载消息失败')
  } finally {
    loadingForward.value = false
  }
}

const backToLatest = () => {
  isViewingHistory.value = false
  hasMoreForward.value = false
  forwardCursor.value = null
  resetAndFetch()
}

// --- Compose dialog state ---

const dialogVisible = ref(false)
const dialogMode = ref<'create' | 'edit'>('create')
const dialogMessageId = ref<number | undefined>(undefined)
const dialogInitialText = ref('')
const dialogInitialDate = ref('')
const dialogInitialMedia = ref<MessageMediaItem[]>([])
const dialogInitialTags = ref<{ id: number; name: string }[]>([])

const openCreateDialog = () => {
  dialogMode.value = 'create'
  dialogMessageId.value = undefined
  dialogInitialText.value = ''
  dialogInitialDate.value = ''
  dialogInitialTags.value = []
  dialogVisible.value = true
}

const openEditDialog = (messageId: number) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (!msg) return

  dialogMode.value = 'edit'
  dialogMessageId.value = messageId
  dialogInitialText.value = msg.text || ''
  dialogInitialMedia.value = msg.media_items || []
  dialogInitialTags.value = msg.tags ? msg.tags.map(t => ({ id: t.id, name: t.name })) : []

  const dateStr = msg.created_at
  if (dateStr) {
    const date = new Date(dateStr)
    if (!isNaN(date.getTime())) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      dialogInitialDate.value = `${year}-${month}-${day}T${hours}:${minutes}`
    }
  }

  dialogVisible.value = true
}

const onDialogCreated = async (message: MessageDetail) => {
  messages.value.push(message)
  await nextTick()
  scrollToBottom()
  fetchTags()
}

const onDialogUpdated = async (messageId: number, text: string, date: string, tagIds: number[]) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (!msg) return

  try {
    const updateData: Record<string, unknown> = { text: text || null, tag_ids: tagIds }
    if (date) updateData.created_at = date

    const updated = await api.patch<MessageDetail>(`/messages/${messageId}`, updateData)
    msg.text = updated.text
    msg.created_at = updated.created_at
    msg.updated_at = updated.updated_at
    if (updated.tags) msg.tags = updated.tags
    toast.success('消息已更新')
    fetchTags()
  } catch {
    toast.error('更新消息失败')
  }
}

const onMediaChanged = async (messageId: number) => {
  try {
    const updated = await api.get<MessageDetail>(`/messages/${messageId}`)
    const msg = messages.value.find(m => m.id === messageId)
    if (msg) {
      msg.media_items = updated.media_items
      msg.media_count = updated.media_count
    }
    if (selectedMessage.value?.id === messageId) {
      selectedMessage.value = updated
    }
  } catch {
    // silent
  }
}

const handleQuickAddTag = async (messageId: number, tagName: string) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (!msg) return

  const text = msg.text || ''
  // Check if tag already exists in text
  const escaped = tagName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  if (new RegExp(`#${escaped}(?![\\w\\u4e00-\\u9fff])`).test(text)) {
    toast.error('该 Tag 已存在')
    return
  }

  // Insert tag: if text starts with hashtags, prepend with space; otherwise prepend with newline
  const hashtagLineRegex = /^((?:#[\w\u4e00-\u9fff\u3400-\u4dbf/\-]+\s*)+)/
  let newText: string
  const match = text.match(hashtagLineRegex)
  if (match) {
    // Existing hashtags at start — prepend before them with space
    newText = `#${tagName} ${text}`
  } else if (text) {
    // No hashtags at start — prepend with newline
    newText = `#${tagName}\n${text}`
  } else {
    newText = `#${tagName}`
  }

  try {
    const updated = await api.patch<MessageDetail>(`/messages/${messageId}`, { text: newText })
    msg.text = updated.text
    msg.updated_at = updated.updated_at
    if (updated.tags) msg.tags = updated.tags
    toast.success('标签已添加')
    fetchTags()
  } catch {
    toast.error('添加标签失败')
  }
}

// --- Fetch messages (unified) ---

const resetAndFetch = (params?: { mediaId?: number }) => {
  nextCursor.value = null
  hasMoreData.value = true
  activeMediaFilter.value = params?.mediaId ?? null
  forwardCursor.value = null
  hasMoreForward.value = false
  isViewingHistory.value = false
  calendarDatesCache.clear()
  calendarAttributes.value = []
  fetchMessages()
}

const fetchMessages = async (isLoadingMore = false) => {
  if (loading.value) return
  if (isLoadingMore && !hasMoreData.value) return

  loading.value = true
  try {
    const data = await api.get<{ items: MessageDetail[]; next_cursor: string | null; has_more: boolean }>(
      '/messages/with-detail',
      {
        limit: pageSize,
        cursor: isLoadingMore ? nextCursor.value : undefined,
        query_text: searchQuery.value || undefined,
        media_id: activeMediaFilter.value ?? undefined,
        starred: starredFilter.value || undefined,
        tag_id: selectedTagId.value ?? undefined,
        actor_id: selectedActorId.value ?? undefined,
      },
    )

    hasMoreData.value = data.has_more
    nextCursor.value = data.next_cursor

    const container = scrollContainer.value
    const previousScrollY = container?.scrollTop ?? 0
    const previousHeight = container?.scrollHeight ?? 0

    if (isLoadingMore) {
      messages.value = [...data.items.reverse(), ...messages.value]
    } else {
      messages.value = data.items.reverse()
    }

    await nextTick()
    if (!isLoadingMore) {
      scrollToBottom('auto')
    } else if (container) {
      const scrollDelta = container.scrollHeight - previousHeight
      container.scrollTo({ top: previousScrollY + scrollDelta, behavior: 'auto' })
    }
  } catch (error) {
    toast.error('加载消息失败')
  } finally {
    loading.value = false
  }
}

// --- Media preview ---

const handleMediaClick = (messageId: number, mediaIndex: number) => {
  const message = messages.value.find(m => m.id === messageId)
  if (!message?.media_items) return

  currentMessageIndex.value = messages.value.findIndex(m => m.id === messageId)
  previewItems.value = message.media_items
  previewStartIndex.value = mediaIndex
  previewMessageId.value = messageId
  previewOpen.value = true
}
const closePreview = () => {
  previewOpen.value = false
  previewItems.value = []
  currentMessageIndex.value = -1
}

const handlePreviewToggleStar = async (mediaId: number) => {
  const currentItem = previewItems.value.find(item => item.id === mediaId)
  if (!currentItem) return

  await toggleMediaStar(currentItem)

  if (currentMessageIndex.value >= 0) {
    const msg = messages.value[currentMessageIndex.value]
    const mediaItem = msg?.media_items?.find(item => item.id === mediaId)
    if (mediaItem) {
      mediaItem.starred = currentItem.starred
    }
  }
}

const handleMediaDeleted = (mediaId: number) => {
  // 更新消息中的媒体项（API调用已在MediaPreview中完成）
  if (currentMessageIndex.value >= 0) {
    const msg = messages.value[currentMessageIndex.value]
    if (msg?.media_items) {
      const itemIndex = msg.media_items.findIndex(item => item.id === mediaId)
      if (itemIndex !== -1) {
        msg.media_items.splice(itemIndex, 1)
      }
    }
  }
}

const handleMediaRotated = (mediaId: number) => {
  const t = Date.now()
  for (const msg of messages.value) {
    if (!msg.media_items) continue
    for (const item of msg.media_items) {
      if (item.id === mediaId) {
        item.thumb_url = item.thumb_url.split('?')[0] + `?t=${t}`
        item.file_path = item.file_path.split('?')[0] + `?t=${t}`
      }
    }
  }
  for (const item of previewItems.value) {
    if (item.id === mediaId) {
      item.thumb_url = item.thumb_url.split('?')[0] + `?t=${t}`
      item.file_path = item.file_path.split('?')[0] + `?t=${t}`
    }
  }
}

const handleMediaTagsChanged = (mediaId: number, newTags: { id: number; name: string; category?: string | null }[]) => {
  for (const msg of messages.value) {
    if (!msg.media_items) continue
    for (const item of msg.media_items) {
      if (item.id === mediaId) {
        item.tags = newTags
      }
    }
  }
  fetchTags()
}

const handleToggleMediaStar = async (mediaId: number, messageId?: number) => {
  const msg = messageId
    ? messages.value.find(m => m.id === messageId)
    : messages.value.find(m => m.media_items?.some(item => item.id === mediaId))
  const mediaItem = msg?.media_items?.find(item => item.id === mediaId)
  if (mediaItem) {
    await toggleMediaStar(mediaItem)
  }
}

const navigateToPrevMessage = () => {
  for (let i = currentMessageIndex.value - 1; i >= 0; i--) {
    const msg = messages.value[i]
    if (msg?.media_items?.length) {
      currentMessageIndex.value = i
      previewItems.value = msg.media_items
      previewStartIndex.value = msg.media_items.length - 1
      previewMessageId.value = msg.id
      return
    }
  }
}

const navigateToNextMessage = () => {
  for (let i = currentMessageIndex.value + 1; i < messages.value.length; i++) {
    const msg = messages.value[i]
    if (msg?.media_items?.length) {
      currentMessageIndex.value = i
      previewItems.value = msg.media_items
      previewStartIndex.value = 0
      previewMessageId.value = msg.id
      return
    }
  }
}

// --- Star toggle ---

const handleToggleStar = async (messageId: number) => {
  const msg = messages.value.find(m => m.id === messageId)
  if (!msg) return

  try {
    const updated = await api.patch<MessageDetail>(`/messages/${messageId}`, {
      starred: !msg.starred,
    })
    msg.starred = updated.starred
  } catch {
    toast.error('操作失败')
  }
}

// --- Delete ---

const handleDeleteMessage = async (messageId: number) => {
  const ok = await confirm({ title: '确认删除', message: '确定要删除这条消息吗？', danger: true })
  if (!ok) return

  try {
    await api.del(`/messages/${messageId}`)
    messages.value = messages.value.filter((m: MessageDetail) => m.id !== messageId)
    toast.success('消息已删除')
    fetchTags()
  } catch (error) {
    toast.error('删除消息失败')
  }
}

// --- Merge ---

const toggleMergeMode = () => {
  mergeMode.value = !mergeMode.value
  selectedMessageIds.value.clear()
}

const toggleSelectMessage = (id: number) => {
  if (selectedMessageIds.value.has(id)) {
    selectedMessageIds.value.delete(id)
  } else {
    selectedMessageIds.value.add(id)
  }
}

const handleMerge = async () => {
  if (selectedMessageIds.value.size < 2) {
    toast.error('请至少选择两条消息')
    return
  }
  const ok = await confirm({
    title: '确认合并',
    message: `确定要合并这 ${selectedMessageIds.value.size} 条消息吗？合并后不可撤销。`,
    danger: true,
  })
  if (!ok) return

  try {
    const merged = await api.post<MessageDetail>('/messages/merge', {
      message_ids: Array.from(selectedMessageIds.value),
    })

    // 移除被合并的消息，替换为合并结果
    const mergedIds = selectedMessageIds.value
    const firstIdx = messages.value.findIndex(m => mergedIds.has(m.id))
    messages.value = messages.value.filter(m => !mergedIds.has(m.id))
    messages.value.splice(firstIdx >= 0 ? firstIdx : 0, 0, merged)

    mergeMode.value = false
    selectedMessageIds.value.clear()
    toast.success('消息合并成功')
    fetchTags()
  } catch (error) {
    toast.error('合并消息失败')
  }
}

// --- Find by media ---

const handleFindMessagesByMedia = (mediaId: number) => {
  resetAndFetch({ mediaId })
}

const handleSelectedMessageMediaClick = (mediaIndex: number) => {
  if (splitMode.value) {
    const media = selectedMessage.value?.media_items?.[mediaIndex]
    if (!media) return
    if (splitSelectedIds.value.has(media.id)) {
      splitSelectedIds.value.delete(media.id)
    } else {
      splitSelectedIds.value.add(media.id)
    }
    splitSelectedIds.value = new Set(splitSelectedIds.value)
    return
  }
  if (!selectedMessage.value?.media_items) return
  currentMessageIndex.value = messages.value.findIndex(m => m.id === selectedMessage.value!.id)
  previewItems.value = selectedMessage.value.media_items
  previewStartIndex.value = mediaIndex
  previewMessageId.value = selectedMessage.value.id
  previewOpen.value = true
}

const toggleSplitMode = () => {
  splitMode.value = !splitMode.value
  splitSelectedIds.value = new Set()
}

const handleSplit = async () => {
  if (!selectedMessage.value || splitSelectedIds.value.size === 0) return
  try {
    await api.post(`/messages/${selectedMessage.value.id}/split`, {
      media_ids: Array.from(splitSelectedIds.value),
    })
    toast.success('拆分成功')
    splitMode.value = false
    splitSelectedIds.value = new Set()
    const full = await api.get<MessageDetail>(`/messages/${selectedMessage.value.id}`)
    selectedMessage.value = full
    await resetAndFetch({})
  } catch (e: any) {
    toast.error(e?.message || '拆分失败')
  }
}

const handleMessageClick = async (message: MessageDetail) => {
  selectedMessage.value = message
  selectedMessageLoading.value = true
  splitMode.value = false
  splitSelectedIds.value = new Set()
  try {
    const full = await api.get<MessageDetail>(`/messages/${message.id}`)
    if (selectedMessage.value?.id === message.id) {
      selectedMessage.value = full
    }
  } catch {
    // keep preview data on failure
  } finally {
    selectedMessageLoading.value = false
  }
}

const handleDetailToggleStar = async () => {
  if (!selectedMessage.value) return
  await handleToggleStar(selectedMessage.value.id)
  if (selectedMessage.value) {
    selectedMessage.value = { ...selectedMessage.value, starred: !selectedMessage.value.starred }
  }
}

const handleDetailDelete = async () => {
  if (!selectedMessage.value) return
  const id = selectedMessage.value.id
  await handleDeleteMessage(id)
  selectedMessage.value = null
}

const renderDetailText = (text: string) => {
  return renderMarkdown(text)
}

// --- Date helpers ---

const getDateStr = (dateString: string) => dateString.substring(0, 10)

// --- Floating date badge ---
const currentVisibleDate = ref('')

const updateVisibleDate = () => {
  const container = scrollContainer.value
  if (!container || messages.value.length === 0) return

  // Find the first message element whose top is at or below the container's scroll top
  const containerRect = container.getBoundingClientRect()
  // offset to account for the sticky date badge height (~36px)
  const probeY = containerRect.top + 40

  const dateEls = container.querySelectorAll<HTMLElement>('[data-message-date]')
  let found = ''
  for (const el of dateEls) {
    const rect = el.getBoundingClientRect()
    if (rect.top <= probeY) {
      found = el.dataset.messageDate || ''
    } else {
      break
    }
  }

  if (!found && dateEls.length > 0) {
    found = dateEls[0].dataset.messageDate || ''
  }

  if (found) {
    currentVisibleDate.value = formatDateLabel(found + 'T00:00:00')
  }
}

let scrollRaf = 0
const onScrollForDate = () => {
  if (scrollRaf) cancelAnimationFrame(scrollRaf)
  scrollRaf = requestAnimationFrame(updateVisibleDate)
}

function onSearch() {
  activeMediaFilter.value = null
  resetAndFetch()
}

// --- Infinite scroll via IntersectionObserver ---

let topObserver: IntersectionObserver | null = null
let bottomObserver: IntersectionObserver | null = null

const setupObservers = () => {
  teardownObservers()
  const root = scrollContainer.value

  topObserver = new IntersectionObserver(
    (entries) => {
      const container = scrollContainer.value
      if (entries[0]?.isIntersecting && !loading.value && hasMoreData.value && container && container.scrollTop > 0) {
        fetchMessages(true)
      }
    },
    { root, rootMargin: '200px' }
  )
  if (topSentinel.value) topObserver.observe(topSentinel.value)

  bottomObserver = new IntersectionObserver(
    (entries) => {
      if (entries[0]?.isIntersecting && !loadingForward.value && hasMoreForward.value) {
        fetchForwardMessages()
      }
    },
    { root, rootMargin: '200px' }
  )
  if (bottomSentinel.value) bottomObserver.observe(bottomSentinel.value)
}

const teardownObservers = () => {
  topObserver?.disconnect()
  topObserver = null
  bottomObserver?.disconnect()
  bottomObserver = null
}

const tryRestoreScroll = () => {
  if (!pendingRestore.value) return
  const container = scrollContainer.value
  if (!container) return
  const { messageId, scrollOffset } = pendingRestore.value
  const attempt = (n: number) => {
    if (!pendingRestore.value) return
    const el = container.querySelector<HTMLElement>(`[data-message-id="${messageId}"]`)
    // 容器不可见（v-show: none）时 scrollHeight 为 0，等可见再试
    if (!el || container.scrollHeight === 0 || container.clientHeight === 0) {
      if (n < 60) requestAnimationFrame(() => attempt(n + 1))
      return
    }
    const containerRect = container.getBoundingClientRect()
    const elRect = el.getBoundingClientRect()
    const targetTop = container.scrollTop + (elRect.top - containerRect.top) - scrollOffset
    container.scrollTo({ top: targetTop, behavior: 'auto' })
    pendingRestore.value = null
  }
  attempt(0)
}

watch(() => route.path, (path) => {
  if (path === '/messages' && pendingRestore.value) {
    nextTick(tryRestoreScroll)
  }
}, { immediate: true })

onMounted(() => {
  fetchTags()
  fetchActors()
  const saved = localStorage.getItem(SCROLL_POS_KEY)
  if (saved) {
    try {
      const { messageId, createdAt, scrollOffset } = JSON.parse(saved) as { messageId: number; createdAt: string; scrollOffset?: number }
      loading.value = true
      Promise.all([
        api.get<{ items: MessageDetail[]; next_cursor: string | null; has_more: boolean }>(
          '/messages/with-detail',
          {
            limit: pageSize,
            cursor: createdAt,
            inclusive: true,
            query_text: searchQuery.value || undefined,
            media_id: activeMediaFilter.value ?? undefined,
            starred: starredFilter.value || undefined,
            tag_id: selectedTagId.value ?? undefined,
            actor_id: selectedActorId.value ?? undefined,
          },
        ),
        api.get<{ items: MessageDetail[]; next_cursor: string | null; has_more: boolean }>(
          '/messages/with-detail',
          {
            limit: pageSize,
            cursor: createdAt,
            query_text: searchQuery.value || undefined,
            media_id: activeMediaFilter.value ?? undefined,
            starred: starredFilter.value || undefined,
            tag_id: selectedTagId.value ?? undefined,
            actor_id: selectedActorId.value ?? undefined,
            direction: 'forward',
          },
        ),
      ]).then(([backwardData, forwardData]) => {
        const allItems = [...backwardData.items.reverse(), ...forwardData.items]
        const seen = new Set<number>()
        messages.value = allItems.filter(m => {
          if (seen.has(m.id)) return false
          seen.add(m.id)
          return true
        })
        nextCursor.value = backwardData.next_cursor
        hasMoreData.value = backwardData.has_more
        if (forwardData.items.length > 0) {
          const lastMsg = forwardData.items[forwardData.items.length - 1]
          forwardCursor.value = lastMsg.created_at
          hasMoreForward.value = forwardData.has_more
          isViewingHistory.value = true
        } else {
          forwardCursor.value = null
          hasMoreForward.value = false
        }
        nextTick(() => {
          pendingRestore.value = { messageId, scrollOffset: scrollOffset ?? 0 }
          tryRestoreScroll()
          setupObservers()
        })
      }).catch(() => {
        fetchMessages()
        setupObservers()
      }).finally(() => {
        loading.value = false
      })
    } catch {
      fetchMessages()
      setupObservers()
    }
  } else {
    fetchMessages()
    setupObservers()
  }
  scrollContainer.value?.addEventListener('scroll', onScrollForDate, { passive: true })
  scrollContainer.value?.addEventListener('scroll', debouncedSaveToStorage, { passive: true })
  document.addEventListener('click', onDocumentClick, true)
})

onUnmounted(() => {
  teardownObservers()
  scrollContainer.value?.removeEventListener('scroll', onScrollForDate)
  scrollContainer.value?.removeEventListener('scroll', debouncedSaveToStorage)
  document.removeEventListener('click', onDocumentClick, true)
  if (scrollRaf) cancelAnimationFrame(scrollRaf)
  if (scrollSaveTimer) clearTimeout(scrollSaveTimer)
})

// Update floating date after messages change
watch(messages, () => nextTick(updateVisibleDate), { flush: 'post' })
</script>

