<script setup>
import { ref } from 'vue'

const emit = defineEmits(['add'])

const open = ref(false)

function add(type) {
  open.value = false
  emit('add', type)
}
</script>

<template>
  <div class="block-adder">
    <div class="adder-line" @click="open = !open">
      <div class="line" />
      <button type="button" class="plus-btn" :class="{ active: open }">
        <i class="pi pi-plus" />
      </button>
      <div class="line" />
    </div>

    <Transition name="menu">
      <div v-if="open" class="add-menu">
        <button type="button" class="add-option" @click="add('header')">
          <i class="pi pi-hashtag" />
          {{ $t('blocks.header') }}
        </button>
        <button type="button" class="add-option" @click="add('text')">
          <i class="pi pi-align-left" />
          {{ $t('blocks.text') }}
        </button>
      </div>
    </Transition>
  </div>
</template>

<style scoped lang="scss">
.block-adder {
  margin: 4px 0;
}

.adder-line {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.line {
  flex: 1;
  height: 1px;
  background: #e5e7eb;
  transition: background 0.15s;

  .adder-line:hover & {
    background: #6366f1;
  }
}

.plus-btn {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1px solid #d1d5db;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  cursor: pointer;
  color: #6b7280;
  flex-shrink: 0;
  transition: background 0.15s, border-color 0.15s, color 0.15s, transform 0.15s;

  &:hover,
  &.active {
    background: #6366f1;
    border-color: #6366f1;
    color: #ffffff;
  }

  &.active {
    transform: rotate(45deg);
  }
}

.add-menu {
  display: flex;
  gap: 6px;
  justify-content: center;
  padding: 4px 0;
}

.add-option {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 20px;
  background: #ffffff;
  font-size: 13px;
  color: #374151;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;

  i { font-size: 12px; }

  &:hover {
    background: #f0f5ff;
    border-color: #6366f1;
    color: #6366f1;
  }
}

// Transition
.menu-enter-active,
.menu-leave-active {
  transition: opacity 0.15s, transform 0.15s;
}
.menu-enter-from,
.menu-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
