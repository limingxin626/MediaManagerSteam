<template>
  <div ref="cardRef" class="flex items-end gap-2" :class="{ 'animate-in': isVisible, 'opacity-0': !isVisible }"
    :style="singleMediaCardStyle">
  <div
    class="group flex-1 min-w-0 bg-[var(--bg-card)] rounded-xl shadow-sm border border-[var(--border-color)] overflow-hidden hover:shadow-lg transition-all duration-200"
    :class="{ 'ring-2 ring-[var(--color-primary-500)] border-[var(--color-primary-500)]': props.selected }">
    <div class="px-4">
      <!-- Actor Info -->
      <div class="flex items-center justify-between gap-3">
        <!-- Selection checkbox -->
        <div v-if="props.selectable" @click.stop="emit('toggle-select', props.message.id)"
          class="shrink-0 w-6 h-6 rounded-md border-2 flex items-center justify-center transition-colors" :class="props.selected
            ? 'bg-[var(--color-primary-600)] border-[var(--color-primary-600)] text-white'
            : 'border-gray-600 hover:border-[var(--color-primary-500)]'">
          <svg v-if="props.selected" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div v-if="message.actor_name"
          class="w-10 h-10 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white font-semibold">
          {{ actorInitial }}
        </div>
        <div class="flex-1 min-w-0">
          <h3 v-if="message.actor_name" class="text-sm font-semibold text-white truncate">
            {{ message.actor_name }}
          </h3>
        </div>
      </div>

      <!-- Unified Media Preview -->
      <div v-if="mediaPreviewItems.length > 0" class="relative overflow-hidden mb-2 -mx-4">
        <!-- Single image -->
        <template v-if="mediaPreviewItems.length === 1">
          <div class="relative overflow-hidden bg-gray-100 dark:bg-gray-800 cursor-pointer group/media"
            :style="{ aspectRatio: getAspectRatio(mediaPreviewItems[0]) }"
            @click.stop="handleMediaClick(0)">
            <img :src="resolveUrl(mediaPreviewItems[0].thumb_url)" alt="Media 1"
              class="w-full h-full object-cover transition-transform duration-200 group-hover/media:scale-105" />
            <div class="absolute inset-0 bg-black/0 group-hover/media:bg-black/20 transition-colors duration-200 pointer-events-none"></div>
            <template v-if="isVideo(mediaPreviewItems[0].mime_type)">
              <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div class="w-10 h-10 bg-black/50 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/20">
                  <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                </div>
              </div>
            </template>
            <div v-if="mediaPreviewItems[0].duration_ms"
              class="absolute bottom-1.5 left-1.5 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded backdrop-blur-sm font-medium">
              {{ formatDuration(mediaPreviewItems[0].duration_ms) }}
            </div>
            <!-- Star and Menu for single -->
            <div class="absolute top-1.5 right-1.5 flex gap-1.5">
              <button @click.stop="handleMediaToggleStar(mediaPreviewItems[0])"
                class="w-6 h-6 rounded-full flex items-center justify-center backdrop-blur-sm transition-colors" :class="mediaPreviewItems[0].starred
                  ? 'text-yellow-400 bg-yellow-900/30 hover:bg-yellow-900/50'
                  : 'text-white/70 hover:text-yellow-400 hover:bg-white/10'">
                <svg class="w-3.5 h-3.5" :class="{ 'star-bounce': mediaStarBouncing === mediaPreviewItems[0].id }" :fill="mediaPreviewItems[0].starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </button>
              <button @click.stop="toggleMenu(0)"
                class="w-6 h-6 bg-black/50 hover:bg-black/80 text-white rounded-full flex items-center justify-center backdrop-blur-sm transition-colors opacity-0 hover:opacity-100"
                :class="{ 'opacity-100!': activeMenuIndex === 0 }">
                <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
                </svg>
              </button>
              <div v-if="activeMenuIndex === 0"
                class="absolute top-8 right-0 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-white/10 py-1 min-w-[140px] z-10">
                <button @click.stop="findMessagesByMedia(mediaPreviewItems[0].id)"
                  class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                  查找所有message
                </button>
              </div>
            </div>
            <div v-if="remainingCount > 0"
              class="absolute inset-0 bg-black/50 flex items-center justify-center pointer-events-none">
              <span class="text-white text-2xl font-semibold">+{{ remainingCount }}</span>
            </div>
          </div>
        </template>

        <!-- Mosaic: ROWS layout -->
        <template v-else-if="mosaicLayout.type === 'rows'">
          <div class="flex flex-col gap-0.5" :style="{ aspectRatio: mosaicRowsAspectRatio }">
            <div v-for="(row, rowIdx) in mosaicLayout.rows" :key="rowIdx"
              class="flex gap-0.5" :style="{ flex: row.heightWeight }">
              <div v-for="mosaicItem in row.items" :key="mosaicItem.index"
                class="relative overflow-hidden bg-gray-100 dark:bg-gray-800 cursor-pointer group/media"
                :style="{ flex: mosaicItem.widthWeight }"
                @click.stop="handleMediaClick(mosaicItem.index)">
                <img :src="resolveUrl(mediaPreviewItems[mosaicItem.index].thumb_url)" :alt="`Media ${mosaicItem.index + 1}`"
                  class="w-full h-full object-cover transition-transform duration-200 group-hover/media:scale-105" />
                <div class="absolute inset-0 bg-black/0 group-hover/media:bg-black/20 transition-colors duration-200 pointer-events-none"></div>
                <template v-if="isVideo(mediaPreviewItems[mosaicItem.index].mime_type)">
                  <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div class="w-10 h-10 bg-black/50 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/20">
                      <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                    </div>
                  </div>
                </template>
                <div v-if="mediaPreviewItems[mosaicItem.index].duration_ms"
                  class="absolute bottom-1.5 left-1.5 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded backdrop-blur-sm font-medium">
                  {{ formatDuration(mediaPreviewItems[mosaicItem.index].duration_ms) }}
                </div>
                <div class="absolute top-1.5 right-1.5 flex gap-1.5">
                  <button @click.stop="handleMediaToggleStar(mediaPreviewItems[mosaicItem.index])"
                    class="w-6 h-6 rounded-full flex items-center justify-center backdrop-blur-sm transition-colors" :class="mediaPreviewItems[mosaicItem.index].starred
                      ? 'text-yellow-400 bg-yellow-900/30 hover:bg-yellow-900/50'
                      : 'text-white/70 hover:text-yellow-400 hover:bg-white/10'">
                    <svg class="w-3.5 h-3.5" :class="{ 'star-bounce': mediaStarBouncing === mediaPreviewItems[mosaicItem.index].id }" :fill="mediaPreviewItems[mosaicItem.index].starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                    </svg>
                  </button>
                  <button @click.stop="toggleMenu(mosaicItem.index)"
                    class="w-6 h-6 bg-black/50 hover:bg-black/80 text-white rounded-full flex items-center justify-center backdrop-blur-sm transition-colors opacity-0 hover:opacity-100"
                    :class="{ 'opacity-100!': activeMenuIndex === mosaicItem.index }">
                    <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                      <path d="M12 8c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2zm0 2c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2zm0 6c-1.1 0-2 .9-2 2s.9 2 2 2 2-.9 2-2-.9-2-2-2z" />
                    </svg>
                  </button>
                  <div v-if="activeMenuIndex === mosaicItem.index"
                    class="absolute top-8 right-0 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-white/10 py-1 min-w-[140px] z-10">
                    <button @click.stop="findMessagesByMedia(mediaPreviewItems[mosaicItem.index].id)"
                      class="w-full px-4 py-2 text-left text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-white/10 transition-colors">
                      查找所有message
                    </button>
                  </div>
                </div>
                <div v-if="mosaicItem.index === mediaPreviewItems.length - 1 && remainingCount > 0"
                  class="absolute inset-0 bg-black/50 flex items-center justify-center pointer-events-none">
                  <span class="text-white text-2xl font-semibold">+{{ remainingCount }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <!-- Mosaic: LEFT_COLUMN layout -->
        <template v-else>
          <div class="flex gap-0.5" :style="{ aspectRatio: `${MOSAIC_CONTAINER_WIDTH} / ${mosaicLeftColumnHeight}` }">
            <!-- Left big image -->
            <div class="relative overflow-hidden bg-gray-100 dark:bg-gray-800 cursor-pointer group/media"
              :style="{ width: (mosaicLayout.leftColumnWidth * 100) + '%' }"
              @click.stop="handleMediaClick(mosaicLayout.leftColumnIndex)">
              <img :src="resolveUrl(mediaPreviewItems[mosaicLayout.leftColumnIndex].thumb_url)" :alt="`Media ${mosaicLayout.leftColumnIndex + 1}`"
                class="w-full h-full object-cover transition-transform duration-200 group-hover/media:scale-105" />
              <div class="absolute inset-0 bg-black/0 group-hover/media:bg-black/20 transition-colors duration-200 pointer-events-none"></div>
              <template v-if="isVideo(mediaPreviewItems[mosaicLayout.leftColumnIndex].mime_type)">
                <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div class="w-10 h-10 bg-black/50 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/20">
                    <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                  </div>
                </div>
              </template>
              <div v-if="mediaPreviewItems[mosaicLayout.leftColumnIndex].duration_ms"
                class="absolute bottom-1.5 left-1.5 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded backdrop-blur-sm font-medium">
                {{ formatDuration(mediaPreviewItems[mosaicLayout.leftColumnIndex].duration_ms) }}
              </div>
              <div class="absolute top-1.5 right-1.5 flex gap-1.5">
                <button @click.stop="handleMediaToggleStar(mediaPreviewItems[mosaicLayout.leftColumnIndex])"
                  class="w-6 h-6 rounded-full flex items-center justify-center backdrop-blur-sm transition-colors" :class="mediaPreviewItems[mosaicLayout.leftColumnIndex].starred
                    ? 'text-yellow-400 bg-yellow-900/30 hover:bg-yellow-900/50'
                    : 'text-white/70 hover:text-yellow-400 hover:bg-white/10'">
                  <svg class="w-3.5 h-3.5" :class="{ 'star-bounce': mediaStarBouncing === mediaPreviewItems[mosaicLayout.leftColumnIndex].id }" :fill="mediaPreviewItems[mosaicLayout.leftColumnIndex].starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                  </svg>
                </button>
              </div>
            </div>
            <!-- Right stacked images -->
            <div class="flex flex-col gap-0.5" :style="{ width: ((1 - mosaicLayout.leftColumnWidth) * 100) + '%' }">
              <div v-for="(row, rowIdx) in mosaicLayout.rows" :key="rowIdx"
                class="relative overflow-hidden bg-gray-100 dark:bg-gray-800 cursor-pointer group/media"
                :style="{ flex: row.heightWeight }"
                @click.stop="handleMediaClick(row.items[0].index)">
                <img :src="resolveUrl(mediaPreviewItems[row.items[0].index].thumb_url)" :alt="`Media ${row.items[0].index + 1}`"
                  class="w-full h-full object-cover transition-transform duration-200 group-hover/media:scale-105" />
                <div class="absolute inset-0 bg-black/0 group-hover/media:bg-black/20 transition-colors duration-200 pointer-events-none"></div>
                <template v-if="isVideo(mediaPreviewItems[row.items[0].index].mime_type)">
                  <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
                    <div class="w-10 h-10 bg-black/50 rounded-full flex items-center justify-center backdrop-blur-sm border border-white/20">
                      <svg class="w-5 h-5 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                    </div>
                  </div>
                </template>
                <div v-if="mediaPreviewItems[row.items[0].index].duration_ms"
                  class="absolute bottom-1.5 left-1.5 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded backdrop-blur-sm font-medium">
                  {{ formatDuration(mediaPreviewItems[row.items[0].index].duration_ms) }}
                </div>
                <div class="absolute top-1.5 right-1.5 flex gap-1.5">
                  <button @click.stop="handleMediaToggleStar(mediaPreviewItems[row.items[0].index])"
                    class="w-6 h-6 rounded-full flex items-center justify-center backdrop-blur-sm transition-colors" :class="mediaPreviewItems[row.items[0].index].starred
                      ? 'text-yellow-400 bg-yellow-900/30 hover:bg-yellow-900/50'
                      : 'text-white/70 hover:text-yellow-400 hover:bg-white/10'">
                    <svg class="w-3.5 h-3.5" :class="{ 'star-bounce': mediaStarBouncing === mediaPreviewItems[row.items[0].index].id }" :fill="mediaPreviewItems[row.items[0].index].starred ? 'currentColor' : 'none'" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                    </svg>
                  </button>
                </div>
                <div v-if="row.items[0].index === mediaPreviewItems.length - 1 && remainingCount > 0"
                  class="absolute inset-0 bg-black/50 flex items-center justify-center pointer-events-none">
                  <span class="text-white text-2xl font-semibold">+{{ remainingCount }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <!-- Message Text -->
      <div v-if="message.text" class="mb-2 prose dark:prose-invert prose-sm max-w-none text-gray-700 dark:text-gray-300">
        <div class="line-clamp-10" v-html="renderedText"></div>
      </div>

      <!-- Tags & Media count row -->
      <div v-if="messageTags.length > 0 || message.media_count > 0" class="flex items-center gap-2 mt-2 flex-wrap">
        <span v-for="tag in messageTags" :key="tag.id"
          class="tag-chip">
          {{ tag.name }}
        </span>
        <span v-if="message.media_count > 0" class="inline-flex items-center gap-1 text-xs text-gray-500 ml-auto">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          {{ message.media_count }}
        </span>
      </div>

      <!-- Timestamp Info & Actions -->
      <div class="flex items-center justify-between mt-3 pt-2 border-t border-[var(--border-color)] text-xs text-gray-500">
          <div class="flex items-center gap-3">
            <span class="flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              创建: {{ formatDate(message.created_at) }}
            </span>
            <span v-if="message.updated_at && message.updated_at !== message.created_at" class="flex items-center gap-1">
              <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
              修改: {{ formatDate(message.updated_at) }}
            </span>
          </div>
          <div class="flex items-center gap-1">
            <button @click.stop="handleToggleStar" class="p-1 rounded transition-colors" :class="props.message.starred
              ? 'text-yellow-400 hover:text-yellow-500'
              : 'text-gray-500 hover:text-yellow-400'"
              :title="props.message.starred ? '取消收藏' : '收藏'">
              <svg class="w-3.5 h-3.5" :class="{ 'star-bounce': starBouncing }" :fill="props.message.starred ? 'currentColor' : 'none'" stroke="currentColor"
                viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
              </svg>
            </button>
            <button @click.stop="handleEdit"
              class="p-1 text-gray-500 hover:text-blue-500 rounded transition-colors"
              title="编辑消息">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </button>
            <button @click.stop="handleDelete"
              class="p-1 text-gray-500 hover:text-red-500 rounded transition-colors"
              title="删除消息">
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                  d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
        </div>
    </div>
  </div>
    <!-- Detail arrow button (Telegram-style) -->
    <button @click="handleClick"
      class="shrink-0 w-8 h-8 mb-1 rounded-full bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-500)] text-white flex items-center justify-center shadow-md hover:shadow-lg transition-all active:scale-95"
      title="查看详情">
      <svg class="w-4 h-4" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </button>
  </div>

</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { marked } from 'marked'
import type { Message, MessageMediaItem, TagItem } from '../types'
import { isVideo, formatDuration, resolveUrl } from '../utils/media'
import { formatRelativeTime } from '../utils/date'
import { calculateMosaicLayout } from '../utils/mosaic'

interface Props {
  message: Message
  mediaItems?: MessageMediaItem[]
  tags?: TagItem[]
  selectable?: boolean
  selected?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  click: [id: number]
  'media-click': [mediaIndex: number]
  delete: [id: number]
  'find-messages-by-media': [mediaId: number]
  'toggle-select': [id: number]
  'toggle-star': [id: number]
  'toggle-media-star': [mediaId: number]
  'edit': [id: number]
}>()

const maxPreviewItems = 9
const activeMenuIndex = ref<number | null>(null)
const cardRef = ref<HTMLElement | null>(null)
const isVisible = ref(false)
const starBouncing = ref(false)
const mediaStarBouncing = ref<number | null>(null)

let observer: IntersectionObserver | null = null

onMounted(() => {
  if (cardRef.value) {
    observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) {
          isVisible.value = true
          observer?.disconnect()
        }
      },
      { rootMargin: '50px' }
    )
    observer.observe(cardRef.value)
  }
})

onUnmounted(() => {
  observer?.disconnect()
})

const handleEdit = () => {
  emit('edit', props.message.id)
}

const actorInitial = computed(() => {
  if (!props.message.actor_name) return '?'
  return props.message.actor_name.charAt(0).toUpperCase()
})

const messageTags = computed(() => {
  return props.tags || []
})

const mediaPreviewItems = computed(() => {
  if (!props.mediaItems) return []
  return props.mediaItems.slice(0, maxPreviewItems)
})

const remainingCount = computed(() => {
  if (!props.mediaItems) return 0
  return Math.max(0, props.mediaItems.length - maxPreviewItems)
})

const renderedText = computed(() => {
  if (!props.message.text) return ''
  // 在 --- 或 === 独占行前后插入空行，防止上方文字被解析为 setext heading
  const normalized = props.message.text.replace(
    /([^\n])\n([-=]{2,})\n/g,
    '$1\n\n$2\n\n'
  )
  marked.setOptions({ breaks: true })
  return marked.parse(normalized) as string
})

// Mosaic layout — 使用容器虚拟宽度 400px 计算
const MOSAIC_CONTAINER_WIDTH = 400

// 单图时限制卡片宽度，防止竖图过高
// 最大图片高度 500px 等效，通过 max-width = maxHeight * ratio 限制
const MAX_SINGLE_IMAGE_HEIGHT = 800
const singleMediaCardStyle = computed(() => {
  if (mediaPreviewItems.value.length !== 1) return {}
  const rawRatio = mediaRatios.value[0]
  const ratio = Math.min(1.7, Math.max(0.667, rawRatio))
  if (ratio >= 1) return {} // 横图不限制
  const maxWidth = MAX_SINGLE_IMAGE_HEIGHT * ratio
  return { maxWidth: maxWidth + 'px' }
})

const getAspectRatio = (item: MessageMediaItem): string => {
  if (item.width && item.height) {
    const ratio = Math.min(1.7, Math.max(0.667, item.width / item.height))
    return `${ratio}`
  }
  return '16 / 9'
}

const mediaRatios = computed(() => {
  return mediaPreviewItems.value.map(item => {
    if (item.width && item.height && item.height > 0) return item.width / item.height
    return 1.5
  })
})

const mosaicLayout = computed(() => {
  if (mediaPreviewItems.value.length <= 1) return null!
  return calculateMosaicLayout(mediaRatios.value, MOSAIC_CONTAINER_WIDTH)
})

// ROWS 布局：整个容器的宽高比 = containerWidth / totalHeight
const mosaicRowsAspectRatio = computed(() => {
  if (!mosaicLayout.value || mosaicLayout.value.type !== 'rows') return '16 / 9'
  const totalHeight = mosaicLayout.value.rows.reduce((s, r) => s + r.heightWeight, 0)
  // 加上 gap (rows.length - 1) * 2px 的近似，忽略不计
  return `${MOSAIC_CONTAINER_WIDTH} / ${totalHeight}`
})

// ROWS 布局：每行高度占总高度的比例，用 flex 权重
const mosaicLeftColumnHeight = computed(() => {
  if (!mosaicLayout.value || mosaicLayout.value.type !== 'left_column') return 0
  const leftIdx = mosaicLayout.value.leftColumnIndex
  const leftRatio = mediaRatios.value[leftIdx]
  const leftWidth = mosaicLayout.value.leftColumnWidth * MOSAIC_CONTAINER_WIDTH
  return leftWidth / leftRatio
})

const formatDate = formatRelativeTime

const handleClick = () => {
  emit('click', props.message.id)
}

const handleMediaClick = (index: number) => {
  emit('media-click', index)
}

const handleDelete = () => {
  emit('delete', props.message.id)
}

const handleToggleStar = () => {
  starBouncing.value = true
  setTimeout(() => { starBouncing.value = false }, 300)
  emit('toggle-star', props.message.id)
}

const toggleMenu = (index: number) => {
  if (activeMenuIndex.value === index) {
    activeMenuIndex.value = null
  } else {
    activeMenuIndex.value = index
  }
}

const findMessagesByMedia = (mediaId: number) => {
  activeMenuIndex.value = null
  emit('find-messages-by-media', mediaId)
}

const handleMediaToggleStar = (mediaItem: MessageMediaItem) => {
  mediaStarBouncing.value = mediaItem.id
  setTimeout(() => { mediaStarBouncing.value = null }, 300)
  emit('toggle-media-star', mediaItem.id)
}
</script>
