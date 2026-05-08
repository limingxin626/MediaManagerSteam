import { ref, nextTick, type Ref } from 'vue'
import type { TagItem } from '../types'
import { matchTags, pushRecentTag } from '../utils/tagMatch'

export function useTagAutocomplete(
  textareaRef: Ref<HTMLTextAreaElement | null>,
  text: Ref<string>,
  allTags: Ref<TagItem[]> | (() => TagItem[]),
  onTagPicked?: (tag: TagItem) => void
) {
  const tagSuggestions = ref<TagItem[]>([])
  const tagSuggestionVisible = ref(false)
  const tagSuggestionIndex = ref(0)
  const tagSuggestionPosition = ref({ top: 0, left: 0 })
  const suggestionListRef = ref<HTMLElement | null>(null)
  let currentTagStart = -1
  
  // 存储最近使用的标签ID，按使用顺序排列（最近的在前）
  const recentTags = ref<number[]>([])

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
    tagSuggestions.value = matchTags(query, getTags(), recentTags.value, 8)

    if (tagSuggestions.value.length > 0) {
      tagSuggestionVisible.value = true
      tagSuggestionIndex.value = 0
      updateSuggestionPosition()
    } else {
      tagSuggestionVisible.value = false
    }
  }

  // 更新最近使用的标签
  const updateRecentTags = (tagId: number) => {
    recentTags.value = pushRecentTag(recentTags.value, tagId)
  }

  const scrollToActiveItem = () => {
    nextTick(() => {
      const list = suggestionListRef.value
      if (!list) return
      const item = list.children[tagSuggestionIndex.value] as HTMLElement | undefined
      item?.scrollIntoView({ block: 'nearest' })
    })
  }

  // Returns true if the key event was handled (caller should return early)
  const onKeydown = (e: KeyboardEvent): boolean => {
    if (!tagSuggestionVisible.value) return false

    if (e.key === 'ArrowDown') {
      e.preventDefault()
      tagSuggestionIndex.value = Math.min(tagSuggestionIndex.value + 1, tagSuggestions.value.length - 1)
      scrollToActiveItem()
      return true
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      tagSuggestionIndex.value = Math.max(tagSuggestionIndex.value - 1, 0)
      scrollToActiveItem()
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

    text.value = before + after

    updateRecentTags(tag.id)
    onTagPicked?.(tag)

    tagSuggestionVisible.value = false
    const restorePos = before.length
    currentTagStart = -1

    setTimeout(() => {
      textarea.setSelectionRange(restorePos, restorePos)
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
    suggestionListRef,
    onInput,
    onKeydown,
    selectTag,
    hide,
  }
}
