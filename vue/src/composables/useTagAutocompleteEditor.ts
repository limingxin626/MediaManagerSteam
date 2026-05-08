import { ref, type Ref, type ComputedRef } from 'vue'
import type { TagItem } from '../types'
import { matchTags, pushRecentTag } from '../utils/tagMatch'

interface MilkdownEditorExposed {
  focus(): void
  getMarkdown(): string
  getCursorCoords(): { top: number; left: number; bottom: number } | null
  getTextBeforeCursor(maxBack?: number): string
  deleteBeforeCursor(count: number): void
  registerKeydown(handler: (view: unknown, e: KeyboardEvent) => boolean): () => void
}

export function useTagAutocompleteEditor(
  editorRef: Ref<MilkdownEditorExposed | null>,
  allTags: Ref<TagItem[]> | ComputedRef<TagItem[]> | (() => TagItem[]),
  onTagPicked?: (tag: TagItem) => void,
) {
  const tagSuggestions = ref<TagItem[]>([])
  const tagSuggestionVisible = ref(false)
  const tagSuggestionIndex = ref(0)
  const tagSuggestionPosition = ref({ top: 0, left: 0 })
  const suggestionListRef = ref<HTMLElement | null>(null)

  const recentTags = ref<number[]>([])
  let currentMatchLen = 0

  const getTags = () =>
    typeof allTags === 'function' ? (allTags as () => TagItem[])() : allTags.value

  function onUpdate() {
    const editor = editorRef.value
    if (!editor) return
    const before = editor.getTextBeforeCursor(64)

    let hashPos = -1
    for (let i = before.length - 1; i >= 0; i--) {
      const ch = before[i]
      if (ch === '#') { hashPos = i; break }
      if (ch === ' ' || ch === '\n' || ch === '\t') break
    }

    if (hashPos === -1) {
      hide()
      return
    }
    const query = before.substring(hashPos + 1).toLowerCase()
    if (/[\s\n]/.test(query)) {
      hide()
      return
    }

    currentMatchLen = before.length - hashPos
    tagSuggestions.value = matchTags(query, getTags(), recentTags.value, 8)

    if (tagSuggestions.value.length === 0) {
      hide()
      return
    }
    tagSuggestionVisible.value = true
    tagSuggestionIndex.value = 0

    const c = editor.getCursorCoords()
    if (c) tagSuggestionPosition.value = { top: c.top - 4, left: c.left }
  }

  function selectTag(tag: TagItem) {
    const editor = editorRef.value
    if (!editor) return
    if (currentMatchLen > 0) editor.deleteBeforeCursor(currentMatchLen)
    recentTags.value = pushRecentTag(recentTags.value, tag.id)
    onTagPicked?.(tag)
    hide()
    setTimeout(() => editor.focus(), 0)
  }

  function onKeydownHandler(_view: unknown, e: KeyboardEvent): boolean {
    if (!tagSuggestionVisible.value) return false
    if (e.key === 'ArrowDown') {
      tagSuggestionIndex.value = Math.min(tagSuggestionIndex.value + 1, tagSuggestions.value.length - 1)
      scrollToActive()
      return true
    }
    if (e.key === 'ArrowUp') {
      tagSuggestionIndex.value = Math.max(tagSuggestionIndex.value - 1, 0)
      scrollToActive()
      return true
    }
    if (e.key === 'Enter' || e.key === 'Tab') {
      const sel = tagSuggestions.value[tagSuggestionIndex.value]
      if (sel) selectTag(sel)
      return true
    }
    if (e.key === 'Escape') {
      hide()
      return true
    }
    return false
  }

  function scrollToActive() {
    requestAnimationFrame(() => {
      const list = suggestionListRef.value
      if (!list) return
      const item = list.children[tagSuggestionIndex.value] as HTMLElement | undefined
      item?.scrollIntoView({ block: 'nearest' })
    })
  }

  function hide() {
    tagSuggestionVisible.value = false
    currentMatchLen = 0
  }

  let unregister: (() => void) | null = null
  function attach() {
    const editor = editorRef.value
    if (!editor) return
    unregister?.()
    unregister = editor.registerKeydown(onKeydownHandler)
  }
  function detach() {
    unregister?.()
    unregister = null
  }

  return {
    tagSuggestions,
    tagSuggestionVisible,
    tagSuggestionIndex,
    tagSuggestionPosition,
    suggestionListRef,
    onUpdate,
    selectTag,
    hide,
    attach,
    detach,
  }
}
