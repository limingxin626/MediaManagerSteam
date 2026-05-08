<template>
  <div ref="rootEl" class="milkdown-host" />
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'
import { Crepe } from '@milkdown/crepe'
import { editorViewCtx } from '@milkdown/kit/core'
import { replaceAll } from '@milkdown/kit/utils'
import { listener, listenerCtx } from '@milkdown/kit/plugin/listener'
import type { EditorView } from '@milkdown/kit/prose/view'

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
let crepe: Crepe | null = null
let ready = false
let pendingFocus = false
let lastEmitted = ''

const keydownHandlers = new Set<(view: EditorView, e: KeyboardEvent) => boolean>()

function getView(): EditorView | null {
  if (!crepe || !ready) return null
  let view: EditorView | null = null
  try {
    crepe.editor.action(ctx => { view = ctx.get(editorViewCtx) })
  } catch {
    return null
  }
  return view
}

function focus() {
  const v = getView()
  if (v) {
    v.focus()
  } else {
    pendingFocus = true
  }
}

function getMarkdown(): string {
  if (!crepe || !ready) return ''
  try {
    return crepe.getMarkdown()
  } catch {
    return ''
  }
}

function getCursorCoords(): { top: number; left: number; bottom: number } | null {
  const view = getView()
  if (!view) return null
  const pos = view.state.selection.from
  const c = view.coordsAtPos(pos)
  return { top: c.top, left: c.left, bottom: c.bottom }
}

function getTextBeforeCursor(maxBack = 64): string {
  const view = getView()
  if (!view) return ''
  const { from } = view.state.selection
  const start = Math.max(0, from - maxBack)
  return view.state.doc.textBetween(start, from, '\n', '\n')
}

function deleteBeforeCursor(count: number) {
  const view = getView()
  if (!view) return
  const { from } = view.state.selection
  const start = Math.max(0, from - count)
  view.dispatch(view.state.tr.delete(start, from))
}

function registerKeydown(handler: (view: EditorView, e: KeyboardEvent) => boolean) {
  keydownHandlers.add(handler)
  return () => keydownHandlers.delete(handler)
}

defineExpose({
  focus,
  getMarkdown,
  getView,
  getCursorCoords,
  getTextBeforeCursor,
  deleteBeforeCursor,
  registerKeydown,
})

onMounted(async () => {
  if (!rootEl.value) return
  crepe = new Crepe({
    root: rootEl.value,
    defaultValue: props.modelValue,
    featureConfigs: {
      [Crepe.Feature.Placeholder]: { text: props.placeholder, mode: 'block' },
    },
  })

  crepe.editor.config(ctx => {
    ctx.update(listenerCtx, l => l
      .markdownUpdated((_, md) => {
        lastEmitted = md
        emit('update:modelValue', md)
        emit('update')
      })
    )
  })
  crepe.editor.use(listener)

  await crepe.create()
  ready = true

  const view = getView()
  if (view) {
    view.dom.addEventListener('keydown', handleDomKeydown, true)
  }

  if (pendingFocus) {
    pendingFocus = false
    view?.focus()
  }

  emit('ready')
})

function handleDomKeydown(e: KeyboardEvent) {
  const view = getView()
  if (!view) return
  for (const h of keydownHandlers) {
    if (h(view, e)) {
      e.preventDefault()
      e.stopPropagation()
      return
    }
  }
}

watch(() => props.modelValue, (val) => {
  if (!crepe || !ready) return
  if (val === lastEmitted) return
  try {
    crepe.editor.action(replaceAll(val ?? ''))
    lastEmitted = val ?? ''
  } catch {
    /* editor not ready yet */
  }
})

onBeforeUnmount(async () => {
  ready = false
  const view = getView()
  if (view) view.dom.removeEventListener('keydown', handleDomKeydown, true)
  if (crepe) {
    await crepe.destroy()
    crepe = null
  }
})
</script>

<style scoped>
.milkdown-host {
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}
.milkdown-host :deep(.milkdown) {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}
</style>
