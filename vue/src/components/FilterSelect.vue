<template>
  <Listbox :model-value="modelValue" @update:model-value="handleChange">
    <div class="relative flex-shrink-0 w-36">
      <ListboxButton class="relative w-full cursor-pointer rounded-xl bg-select-bg dark:bg-select-bg-dark py-2 pl-3 pr-10 text-left text-select-text dark:text-select-text-dark border border-select-border dark:border-select-border-dark focus:outline-none focus:ring-2 focus:ring-select-focus-ring">
        <span class="block truncate">{{ selectedLabel }}</span>
        <span class="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-2">
          <svg class="h-5 w-5 text-select-icon" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
          </svg>
        </span>
      </ListboxButton>
      <transition
        leave-active-class="transition duration-100 ease-in"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <ListboxOptions class="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md bg-select-menu-bg dark:bg-select-menu-bg-dark py-1 text-base shadow-lg ring-1 ring-black/5 dark:ring-white/10 focus:outline-none">
          <ListboxOption
            v-for="option in options"
            :key="option.value"
            :value="option.value"
            v-slot="{ active, selected }"
            as="template"
          >
            <li :class="[
              active ? 'bg-select-option-active-bg dark:bg-select-option-active-bg-dark text-select-option-active-text dark:text-select-option-active-text-dark' : 'text-select-text dark:text-select-text-dark',
              'relative cursor-pointer select-none py-2 pl-3 pr-9'
            ]">
              <span :class="[selected ? 'font-medium' : 'font-normal', 'block truncate']">
                {{ option.label }}
              </span>
              <span v-if="selected" class="absolute inset-y-0 right-0 flex items-center pr-4 text-select-selected-icon dark:text-select-selected-icon-dark">
                <svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
                </svg>
              </span>
            </li>
          </ListboxOption>
        </ListboxOptions>
      </transition>
    </div>
  </Listbox>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Listbox, ListboxButton, ListboxOptions, ListboxOption } from '@headlessui/vue'

interface Option {
  value: string
  label: string
}

const props = defineProps<{
  modelValue: string
  options: Option[]
  placeholder?: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'change': [value: string]
}>()

const handleChange = (value: string) => {
  emit('update:modelValue', value)
  emit('change', value)
}

const selectedLabel = computed(() => {
  const selected = props.options.find(opt => opt.value === props.modelValue)
  return selected?.label || props.placeholder || ''
})
</script>
