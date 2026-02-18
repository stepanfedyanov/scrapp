<script setup>
const props = defineProps({
  text: { type: String, default: '' },
  level: { type: Number, default: 2 },
})

const emit = defineEmits(['update:text', 'update:level', 'delete'])

const levels = [
  { value: 2, label: 'H2' },
  { value: 3, label: 'H3' },
]
</script>

<template>
  <div class="block-header">
    <div class="level-selector">
      <button
        v-for="lvl in levels"
        :key="lvl.value"
        type="button"
        :class="['level-btn', { active: level === lvl.value }]"
        @click="emit('update:level', lvl.value)"
      >
        {{ lvl.label }}
      </button>
    </div>

    <input
      type="text"
      :value="text"
      :placeholder="$t('blocks.headingPlaceholder', { level })"
      class="header-input"
      :style="{ fontSize: level === 1 ? '26px' : level === 2 ? '20px' : '16px', fontWeight: level === 1 ? '800' : '700' }"
      @input="emit('update:text', $event.target.value)"
    />

    <button class="delete-btn" type="button" :title="$t('blocks.deleteBlock')" @click="emit('delete')">
      <i class="pi pi-trash" />
    </button>
  </div>
</template>

<style scoped lang="scss">
.block-header {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  border-radius: 6px;

  &:hover .delete-btn {
    opacity: 1;
  }
}

.level-selector {
  display: flex;
  gap: 2px;
  flex-shrink: 0;
}

.level-btn {
  padding: 2px 7px;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background: #f9fafb;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  transition: background 0.15s, border-color 0.15s, color 0.15s;

  &:hover {
    background: #e5e7eb;
  }

  &.active {
    background: #dbeafe;
    border-color: #93c5fd;
    color: #1d4ed8;
  }
}

.header-input {
  flex: 1;
  border: none;
  outline: none;
  background: transparent;
  border-bottom: 2px solid transparent;
  color: #111827;
  line-height: 1.3;
  width: 100%;
  transition: border-color 0.15s;
  padding: 2px 0;

  &::placeholder {
    color: #9ca3af;
  }

  &:focus {
    border-bottom-color: #6366f1;
  }
}

.delete-btn {
  position: absolute;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  color: #9ca3af;
  font-size: 13px;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s, border-color 0.15s;
  padding: 3px 6px;

  &:hover {
    color: #ef4444;
    border-color: #fca5a5;
  }
}
</style>
