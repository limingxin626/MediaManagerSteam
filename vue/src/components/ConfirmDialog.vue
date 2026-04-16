<template>
  <TransitionRoot appear :show="state.visible" as="template">
    <Dialog as="div" class="relative z-[200]" @close="handleCancel">
      <TransitionChild
        as="template"
        enter="duration-200 ease-out"
        enter-from="opacity-0"
        enter-to="opacity-100"
        leave="duration-150 ease-in"
        leave-from="opacity-100"
        leave-to="opacity-0"
      >
        <div class="fixed inset-0 bg-black/60 backdrop-blur-sm" />
      </TransitionChild>

      <div class="fixed inset-0 flex items-center justify-center p-4">
        <TransitionChild
          as="template"
          enter="duration-200 ease-out"
          enter-from="opacity-0 scale-95"
          enter-to="opacity-100 scale-100"
          leave="duration-150 ease-in"
          leave-from="opacity-100 scale-100"
          leave-to="opacity-0 scale-95"
        >
          <DialogPanel
            class="w-full max-w-sm bg-[var(--bg-card)] rounded-2xl border border-[var(--border-color)] shadow-2xl p-6"
          >
            <DialogTitle class="text-base font-semibold text-[var(--text-primary)]">
              {{ state.options.title }}
            </DialogTitle>
            <p class="mt-2 text-sm text-[var(--text-secondary)]">
              {{ state.options.message }}
            </p>
            <div class="mt-5 flex justify-end gap-2">
              <button
                @click="handleCancel"
                class="px-4 py-2 text-sm rounded-lg text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)] transition-colors"
              >
                {{ state.options.cancelText || '取消' }}
              </button>
              <button
                @click="handleConfirm"
                class="px-4 py-2 text-sm font-medium rounded-lg text-white transition-colors"
                :class="state.options.danger
                  ? 'bg-[var(--color-danger)] hover:bg-red-700'
                  : 'bg-[var(--color-primary-600)] hover:bg-[var(--color-primary-700)]'"
              >
                {{ state.options.confirmText || '确认' }}
              </button>
            </div>
          </DialogPanel>
        </TransitionChild>
      </div>
    </Dialog>
  </TransitionRoot>
</template>

<script setup lang="ts">
import {
  Dialog,
  DialogPanel,
  DialogTitle,
  TransitionRoot,
  TransitionChild,
} from '@headlessui/vue'
import { useConfirm } from '../composables/useConfirm'

const { state, handleConfirm, handleCancel } = useConfirm()
</script>
