<script setup>
import { computed } from 'vue'
import InputText from 'primevue/inputtext'
import InputNumber from 'primevue/inputnumber'
import Checkbox from 'primevue/checkbox'
import Dropdown from 'primevue/dropdown'
import Password from 'primevue/password'

const props = defineProps({
  schema: {
    type: Object,
    required: true
  },
  modelValue: {
    type: Object,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const properties = computed(() => props.schema.properties || {})
const required = computed(() => props.schema.required || [])

const getFieldType = (prop) => {
  if (prop.type === 'string') {
    if (prop.format === 'password') return 'password'
    if (prop.enum) return 'dropdown'
    if (prop.description && prop.description.includes('long')) return 'textarea'
    return 'text'
  }
  if (prop.type === 'number' || prop.type === 'integer') return 'number'
  if (prop.type === 'boolean') return 'checkbox'
  if (prop.enum) return 'dropdown'
  return 'text'
}

const getEnumOptions = (prop) => {
  return (prop.enum || []).map(value => ({
    label: prop.enumLabels?.[value] || value,
    value
  }))
}

const isRequired = (fieldName) => required.value.includes(fieldName)

const updateField = (fieldName, value) => {
  emit('update:modelValue', {
    ...props.modelValue,
    [fieldName]: value
  })
}
</script>

<template>
  <div class="dynamic-schema-form">
    <div v-for="(prop, fieldName) in properties" :key="fieldName" class="form-field">
      <label :for="fieldName" class="field-label">
        {{ prop.title || fieldName }}
        <span v-if="isRequired(fieldName)" class="required">*</span>
      </label>

      <!-- Text Input -->
      <InputText
        v-if="getFieldType(prop) === 'text'"
        :id="fieldName"
        :model-value="modelValue[fieldName]"
        :placeholder="prop.description"
        :disabled="loading"
        class="w-full"
        @update:model-value="updateField(fieldName, $event)"
      />

      <!-- Password Input -->
      <Password
        v-else-if="getFieldType(prop) === 'password'"
        :id="fieldName"
        :model-value="modelValue[fieldName]"
        :placeholder="prop.description"
        :disabled="loading"
        toggle-mask
        class="w-full"
        input-class="w-full"
        @update:model-value="updateField(fieldName, $event)"
      />

      <!-- Number Input -->
      <InputNumber
        v-else-if="getFieldType(prop) === 'number'"
        :id="fieldName"
        :model-value="modelValue[fieldName]"
        :placeholder="prop.description"
        :disabled="loading"
        class="w-full"
        @update:model-value="updateField(fieldName, $event)"
      />

      <!-- Checkbox -->
      <div v-else-if="getFieldType(prop) === 'checkbox'" class="checkbox-wrapper">
        <Checkbox
          :id="fieldName"
          :model-value="modelValue[fieldName]"
          :binary="true"
          :disabled="loading"
          @update:model-value="updateField(fieldName, $event)"
        />
        <label :for="fieldName" class="checkbox-label">
          {{ prop.description || fieldName }}
        </label>
      </div>

      <!-- Dropdown -->
      <Dropdown
        v-else-if="getFieldType(prop) === 'dropdown'"
        :id="fieldName"
        :model-value="modelValue[fieldName]"
        :options="getEnumOptions(prop)"
        :placeholder="`Select ${fieldName}`"
        :disabled="loading"
        option-label="label"
        option-value="value"
        class="w-full"
        @update:model-value="updateField(fieldName, $event)"
      />

      <!-- Textarea -->
      <textarea
        v-else-if="getFieldType(prop) === 'textarea'"
        :id="fieldName"
        :value="modelValue[fieldName]"
        :placeholder="prop.description"
        :disabled="store.loading"
        rows="4"
        class="w-full textarea-input"
        @input="updateField(fieldName, $event.target.value)"
      />

      <!-- Fallback: Text Input -->
      <InputText
        v-else
        :id="fieldName"
        :model-value="modelValue[fieldName]"
        :placeholder="prop.description"
        :disabled="loading"
        class="w-full"
        @update:model-value="updateField(fieldName, $event)"
      />

      <!-- Help text -->
      <small v-if="prop.description && getFieldType(prop) !== 'textarea'" class="form-help">
        {{ prop.description }}
      </small>
    </div>
  </div>
</template>

<style scoped lang="scss">
.dynamic-schema-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-label {
  font-weight: 500;
  font-size: 0.875rem;
  color: #374151;
}

.required {
  color: #ef4444;
  margin-left: 0.25rem;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.checkbox-label {
  font-weight: normal;
  cursor: pointer;
}

.form-help {
  color: #6b7280;
  font-size: 0.75rem;
}

.textarea-input {
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 0.375rem;
  font-family: inherit;
  font-size: 0.875rem;
}

.textarea-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.textarea-input:disabled {
  background-color: #f3f4f6;
  cursor: not-allowed;
}

:deep(.p-inputtext),
:deep(.p-inputnumber),
:deep(.p-dropdown),
:deep(.p-inputtextarea) {
  width: 100%;
}
</style>
