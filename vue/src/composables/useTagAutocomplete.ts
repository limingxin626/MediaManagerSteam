import { ref, type Ref } from 'vue'
import type { TagItem } from '../types'
import { getPinyinInitials } from '../utils/pinyinInitial'

export function useTagAutocomplete(
  textareaRef: Ref<HTMLTextAreaElement | null>,
  text: Ref<string>,
  allTags: Ref<TagItem[]> | (() => TagItem[])
) {
  const tagSuggestions = ref<TagItem[]>([])
  const tagSuggestionVisible = ref(false)
  const tagSuggestionIndex = ref(0)
  const tagSuggestionPosition = ref({ top: 0, left: 0 })
  let currentTagStart = -1
  
  // 存储最近使用的标签ID，按使用顺序排列（最近的在前）
  const recentTags = ref<number[]>([])
  const MAX_RECENT_TAGS = 10

  const getTags = () => (typeof allTags === 'function' ? allTags() : allTags.value)

  const updateSuggestionPosition = () => {
    const textarea = textareaRef.value
    if (!textarea) return

    const caretPos = textarea.selectionStart
    const cs = window.getComputedStyle(textarea)
    const textareaRect = textarea.getBoundingClientRect()

    const mirror = document.createElement('div')
    ;[
      'font-family', 'font-size', 'font-weight', 'font-style',
      'letter-spacing', 'word-spacing', 'line-height',
      'padding-top', 'padding-right', 'padding-bottom', 'padding-left',
      'border-top-width', 'border-right-width', 'border-bottom-width', 'border-left-width',
      'box-sizing', 'word-wrap', 'overflow-wrap',
    ].forEach((prop) => mirror.style.setProperty(prop, cs.getPropertyValue(prop)))

    mirror.style.position = 'fixed'
    mirror.style.visibility = 'hidden'
    mirror.style.pointerEvents = 'none'
    mirror.style.top = textareaRect.top + 'px'
    mirror.style.left = textareaRect.left + 'px'
    mirror.style.width = textareaRect.width + 'px'
    mirror.style.height = textareaRect.height + 'px'
    mirror.style.whiteSpace = 'pre-wrap'
    mirror.style.wordBreak = 'break-word'
    mirror.style.overflow = 'hidden'

    mirror.textContent = textarea.value.substring(0, caretPos)

    const caretSpan = document.createElement('span')
    caretSpan.textContent = '\u200b'
    mirror.appendChild(caretSpan)

    document.body.appendChild(mirror)
    const spanRect = caretSpan.getBoundingClientRect()
    document.body.removeChild(mirror)

    tagSuggestionPosition.value = {
      top: spanRect.top - textarea.scrollTop - 4,
      left: spanRect.left - textarea.scrollLeft,
    }
  }

  const onInput = () => {
    const textarea = textareaRef.value
    if (!textarea) return

    const cursorPos = textarea.selectionStart
    let hashPos = -1
    for (let i = cursorPos - 1; i >= 0; i--) {
      if (text.value[i] === '#') {
        hashPos = i
        break
      }
      if (text.value[i] === ' ' || text.value[i] === '\n') break
    }

    if (hashPos === -1) {
      tagSuggestionVisible.value = false
      return
    }

    const afterHash = text.value.substring(hashPos + 1, cursorPos)
    if (afterHash.includes(' ') || afterHash.includes('\n')) {
      tagSuggestionVisible.value = false
      return
    }

    currentTagStart = hashPos
    const query = afterHash.toLowerCase()
    
    const allTagList = getTags()
    const textMatched = new Set<number>()
    const textResults: TagItem[] = []
    const pinyinResults: TagItem[] = []

    for (const tag of allTagList) {
      if (tag.name.toLowerCase().includes(query)) {
        textResults.push(tag)
        textMatched.add(tag.id)
      }
    }

    if (query && /^[a-z]+$/.test(query)) {
      for (const tag of allTagList) {
        if (!textMatched.has(tag.id)) {
          const initials = getPinyinInitials(tag.name)
          if (initials.startsWith(query)) {
            pinyinResults.push(tag)
          }
        }
      }
    }

    tagSuggestions.value = [
      ...sortTagsByRecentUse(textResults),
      ...sortTagsByRecentUse(pinyinResults),
    ].slice(0, 8)

    if (tagSuggestions.value.length > 0) {
      tagSuggestionVisible.value = true
      tagSuggestionIndex.value = 0
      updateSuggestionPosition()
    } else {
      tagSuggestionVisible.value = false
    }
  }

  // 按最近使用排序标签
  const sortTagsByRecentUse = (tags: TagItem[]): TagItem[] => {
    return tags.sort((a, b) => {
      const aIndex = recentTags.value.indexOf(a.id)
      const bIndex = recentTags.value.indexOf(b.id)
      
      // 最近使用的标签排前面
      if (aIndex !== -1 && bIndex !== -1) {
        return aIndex - bIndex
      }
      // 只有一个在最近使用列表中，排前面
      if (aIndex !== -1) return -1
      if (bIndex !== -1) return 1
      // 都不在最近使用列表中，按名称排序
      return a.name.localeCompare(b.name)
    })
  }

  // 更新最近使用的标签
  const updateRecentTags = (tagId: number) => {
    // 移除已存在的，放到最前面
    const currentIndex = recentTags.value.indexOf(tagId)
    if (currentIndex !== -1) {
      recentTags.value.splice(currentIndex, 1)
    }
    // 添加到最前面
    recentTags.value.unshift(tagId)
    // 限制数量
    if (recentTags.value.length > MAX_RECENT_TAGS) {
      recentTags.value = recentTags.value.slice(0, MAX_RECENT_TAGS)
    }
  }

  // Returns true if the key event was handled (caller should return early)
  const onKeydown = (e: KeyboardEvent): boolean => {
    if (!tagSuggestionVisible.value) return false

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      tagSuggestionIndex.value = Math.min(tagSuggestionIndex.value + 1, tagSuggestions.value.length - 1)
      return true
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      tagSuggestionIndex.value = Math.max(tagSuggestionIndex.value - 1, 0)
      return true
    }
    if (e.key === 'Enter' || e.key === 'Tab') {
      e.preventDefault()
      const selected = tagSuggestions.value[tagSuggestionIndex.value]
      if (selected) selectTag(selected)
      return true
    }
    if (e.key === 'Escape') {
      tagSuggestionVisible.value = false
      return true
    }
    return false
  }

  const selectTag = (tag: TagItem) => {
    if (!tag || currentTagStart === -1) return

    const textarea = textareaRef.value
    if (!textarea) return

    const cursorPos = textarea.selectionStart
    const before = text.value.substring(0, currentTagStart)
    const after = text.value.substring(cursorPos)
    const tagName = tag.name.includes(' ') ? `#${tag.name}#` : `#${tag.name}`

    text.value = before + tagName + (after.startsWith(' ') ? '' : ' ') + after

    // 更新最近使用的标签
    updateRecentTags(tag.id)

    tagSuggestionVisible.value = false
    currentTagStart = -1

    setTimeout(() => {
      const newPos = before.length + tagName.length + 1
      textarea.setSelectionRange(newPos, newPos)
      textarea.focus()
    }, 0)
  }

  const hide = () => {
    tagSuggestionVisible.value = false
  }

  return {
    tagSuggestions,
    tagSuggestionVisible,
    tagSuggestionIndex,
    tagSuggestionPosition,
    onInput,
    onKeydown,
    selectTag,
    hide,
  }
}
