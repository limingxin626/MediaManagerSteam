<template>
  <textarea
    ref="ta"
    :value="modelValue"
    :placeholder="placeholder"
    rows="1"
    class="block w-full min-h-[28px] resize-none bg-transparent outline-none border-none text-[var(--text-primary)] placeholder:text-gray-400"
    @input="onInput"
    @keydown="onKeydown"
  />
</template>

<script setup lang="ts">
// 原始文本输入框（不渲染 Markdown）。对外暴露与 VditorEditor 相同的接口，
// 以复用 useTagAutocompleteEditor 的 #tag 自动补全。
import { ref, nextTick, watch, onMounted } from 'vue'

const props = defineProps<{
  modelValue: string
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  update: []
  ready: []
}>()

const ta = ref<HTMLTextAreaElement | null>(null)
let keydownHandler: ((view: unknown, e: KeyboardEvent) => boolean) | null = null

function autoResize() {
  const el = ta.value
  if (!el) return
  el.style.height = 'auto'
  // parent 可能在挂载瞬间还没布局，scrollHeight 为 0；此时保底一行高度，
  // 否则 inline height:0 会把 textarea 压没，导致点不到。
  const h = Math.max(el.scrollHeight, 28)
  el.style.height = h + 'px'
}

watch(() => props.modelValue, () => nextTick(autoResize))

function onInput(e: Event) {
  emit('update:modelValue', (e.target as HTMLTextAreaElement).value)
  emit('update')
  autoResize()
}

function onKeydown(e: KeyboardEvent) {
  // 先让自动补全消费（方向键 / Enter / Tab / Esc）
  if (keydownHandler && keydownHandler(null, e)) {
    e.preventDefault()
    return
  }
}

function focus() {
  ta.value?.focus()
}

function getMarkdown(): string {
  return ta.value?.value ?? props.modelValue
}

function getTextBeforeCursor(maxBack = 64): string {
  const el = ta.value
  if (!el) return ''
  const pos = el.selectionStart ?? el.value.length
  return el.value.substring(Math.max(0, pos - maxBack), pos)
}

function deleteBeforeCursor(count: number) {
  const el = ta.value
  if (!el) return
  const pos = el.selectionStart ?? el.value.length
  const start = Math.max(0, pos - count)
  const next = el.value.substring(0, start) + el.value.substring(pos)
  el.value = next
  el.setSelectionRange(start, start)
  emit('update:modelValue', next)
  autoResize()
}

function getCursorCoords(): { top: number; left: number; bottom: number } | null {
  const el = ta.value
  if (!el) return null
  const rect = el.getBoundingClientRect()
  // 简化：贴着输入框上沿弹出建议列表
  return { top: rect.top, left: rect.left, bottom: rect.bottom }
}

function registerKeydown(handler: (view: unknown, e: KeyboardEvent) => boolean) {
  keydownHandler = handler
  return () => {
    if (keydownHandler === handler) keydownHandler = null
  }
}

onMounted(() => {
  autoResize()
  emit('ready')
})

defineExpose({
  focus,
  getMarkdown,
  getCursorCoords,
  getTextBeforeCursor,
  deleteBeforeCursor,
  registerKeydown,
})
</script>
