<template>
  <div ref="rootEl" class="vditor-host" />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import Vditor from 'vditor'
import 'vditor/dist/index.css'

interface Props {
  modelValue: string
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), { placeholder: '' })

const emit = defineEmits<{
  'update:modelValue': [value: string]
  ready: []
  update: []
}>()

const rootEl = ref<HTMLDivElement | null>(null)
let vditor: Vditor | null = null
let ready = false
let pendingFocus = false
let lastEmitted = ''

const keydownHandlers = new Set<(view: unknown, e: KeyboardEvent) => boolean>()

function getEditableEl(): HTMLElement | null {
  if (!rootEl.value) return null
  return rootEl.value.querySelector<HTMLElement>('.vditor-ir .vditor-reset')
}

function focus() {
  if (!vditor || !ready) {
    pendingFocus = true
    return
  }
  vditor.focus()
}

function getMarkdown(): string {
  if (!vditor || !ready) return ''
  try {
    return vditor.getValue()
  } catch {
    return ''
  }
}

function getCursorCoords(): { top: number; left: number; bottom: number } | null {
  const sel = window.getSelection()
  if (!sel || sel.rangeCount === 0) return null
  const range = sel.getRangeAt(0).cloneRange()
  range.collapse(true)
  const rects = range.getClientRects()
  let rect: DOMRect | null = rects.length > 0 ? rects[0] : null
  if (!rect || (rect.top === 0 && rect.left === 0)) {
    const r = range.getBoundingClientRect()
    if (r && (r.top !== 0 || r.left !== 0)) rect = r
  }
  if (!rect) {
    const el = getEditableEl()
    if (!el) return null
    const r = el.getBoundingClientRect()
    return { top: r.bottom, left: r.left, bottom: r.bottom }
  }
  return { top: rect.top, left: rect.left, bottom: rect.bottom }
}

function getTextBeforeCursor(maxBack = 64): string {
  if (!vditor || !ready) return ''
  const md = vditor.getValue()
  const body = md.endsWith('\n') ? md.slice(0, -1) : md
  return body.slice(-maxBack)
}

function moveCursorToEnd() {
  const el = getEditableEl()
  if (!el) return
  el.focus()
  const range = document.createRange()
  range.selectNodeContents(el)
  range.collapse(false)
  const sel = window.getSelection()
  if (!sel) return
  sel.removeAllRanges()
  sel.addRange(range)
}

function deleteBeforeCursor(count: number) {
  if (count <= 0 || !vditor || !ready) return
  const md = vditor.getValue()
  const body = md.endsWith('\n') ? md.slice(0, -1) : md
  if (body.length < count) return
  const next = body.slice(0, body.length - count)
  vditor.setValue(next)
  lastEmitted = next
  emit('update:modelValue', next)
  requestAnimationFrame(moveCursorToEnd)
}

function registerKeydown(handler: (view: unknown, e: KeyboardEvent) => boolean) {
  keydownHandlers.add(handler)
  return () => keydownHandlers.delete(handler)
}

defineExpose({
  focus,
  getMarkdown,
  getCursorCoords,
  getTextBeforeCursor,
  deleteBeforeCursor,
  registerKeydown,
})

function handleDomKeydown(e: KeyboardEvent) {
  for (const h of keydownHandlers) {
    if (h(null, e)) {
      e.preventDefault()
      e.stopPropagation()
      return
    }
  }
}

function handleDomInput() {
  emit('update')
}

onMounted(() => {
  if (!rootEl.value) return
  vditor = new Vditor(rootEl.value, {
    mode: 'ir',
    height: '100%',
    minHeight: 28,
    placeholder: props.placeholder,
    value: props.modelValue,
    cache: { enable: false },
    toolbar: [],
    toolbarConfig: { hide: true, pin: false },
    counter: { enable: false },
    preview: { hljs: { enable: false } },
    after: () => {
      ready = true
      const el = getEditableEl()
      if (el) {
        el.addEventListener('keydown', handleDomKeydown, true)
        el.addEventListener('input', handleDomInput, true)
      }
      if (pendingFocus) {
        pendingFocus = false
        vditor?.focus()
      }
      emit('ready')
    },
    input: (md: string) => {
      lastEmitted = md
      emit('update:modelValue', md)
    },
  })
})

watch(() => props.modelValue, (val) => {
  if (!vditor || !ready) return
  if (val === lastEmitted) return
  try {
    vditor.setValue(val ?? '')
    lastEmitted = val ?? ''
  } catch {
    /* not ready */
  }
})

onBeforeUnmount(() => {
  ready = false
  const el = getEditableEl()
  if (el) {
    el.removeEventListener('keydown', handleDomKeydown, true)
    el.removeEventListener('input', handleDomInput, true)
  }
  if (vditor) {
    try { vditor.destroy() } catch { /* ignore */ }
    vditor = null
  }
})
</script>

<style scoped>
.vditor-host {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.vditor-host :deep(.vditor) {
  border: none;
  background: transparent;
  flex: 1;
  min-height: 0;
}
.vditor-host :deep(.vditor-toolbar),
.vditor-host :deep(.vditor-counter),
.vditor-host :deep(.vditor-resize) {
  display: none !important;
}
.vditor-host :deep(.vditor-content) {
  min-height: 0;
}
.vditor-host :deep(.vditor-reset) {
  background: transparent;
  padding: 0;
  font-size: 0.875rem;
  color: inherit;
  min-height: 1.5rem;
  line-height: 1.5rem;
}
.vditor-host :deep(.vditor-ir) {
  background: transparent;
  padding: 0;
}
.vditor-host :deep(.vditor-reset > p) {
  margin: 0;
}
.vditor-host :deep(.vditor-reset > p:first-child) {
  margin-top: 0;
}
</style>
