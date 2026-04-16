import { ref, markRaw } from 'vue'

export interface ConfirmOptions {
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
}

interface ConfirmState {
  visible: boolean
  options: ConfirmOptions
  resolve: ((value: boolean) => void) | null
}

const state = ref<ConfirmState>({
  visible: false,
  options: { title: '', message: '' },
  resolve: null,
})

export function useConfirm() {
  const confirm = (options: ConfirmOptions): Promise<boolean> => {
    return new Promise((resolve) => {
      state.value = {
        visible: true,
        options,
        resolve: markRaw(resolve),
      }
    })
  }

  const handleConfirm = () => {
    state.value.resolve?.(true)
    state.value.visible = false
    state.value.resolve = null
  }

  const handleCancel = () => {
    state.value.resolve?.(false)
    state.value.visible = false
    state.value.resolve = null
  }

  return { state, confirm, handleConfirm, handleCancel }
}
