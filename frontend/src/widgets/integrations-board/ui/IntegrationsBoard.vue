<script setup>
import { onMounted, ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useIntegrationsStore } from '~/src/entities/integrations'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import InputText from 'primevue/inputtext'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import DynamicSchemaForm from '~/src/shared/ui/forms/DynamicSchemaForm.vue'

const { t } = useI18n()
const confirm = useConfirm()
const toast = useToast()
const store = useIntegrationsStore()

const showDialog = ref(false)
const editingIntegration = ref(null)
const formData = ref({})
const selectedDefinitionCode = ref(null)
const integrationTitle = ref('')

const selectedIntegrations = ref([])

const statusSeverityMap = {
  active: 'success',
  disabled: 'warning',
  error: 'danger'
}

const statusLabelMap = {
  active: 'Active',
  disabled: 'Disabled',
  error: 'Error'
}

const loadData = async () => {
  try {
    await store.fetchIntegrations()
    await store.fetchDefinitions()
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load integrations',
      life: 3000
    })
  }
}

onMounted(loadData)

const openCreateDialog = () => {
  editingIntegration.value = null
  selectedDefinitionCode.value = null
  integrationTitle.value = ''
  formData.value = {}
  showDialog.value = true
}

const openEditDialog = (integration) => {
  editingIntegration.value = integration
  selectedDefinitionCode.value = integration.definition?.code || null
  integrationTitle.value = integration.title || ''
  formData.value = { ...integration.credentials }
  showDialog.value = true
}

const saveIntegration = async () => {
  if (!selectedDefinitionCode.value) {
    toast.add({
      severity: 'warn',
      summary: 'Select Integration',
      detail: 'Please select an integration type',
      life: 3000
    })
    return
  }

  const definition = store.getDefinitionByCode(selectedDefinitionCode.value)
  if (!definition) {
    toast.add({
      severity: 'error',
      summary: 'Invalid Integration',
      detail: 'Selected integration type not found',
      life: 3000
    })
    return
  }

  const payload = {
    title: (integrationTitle.value || definition.name).trim(),
    definition_id: definition.id,
    credentials: formData.value
  }

  try {
    if (editingIntegration.value?.id) {
      await store.updateIntegration(editingIntegration.value.id, payload)
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Integration updated',
        life: 3000
      })
    } else {
      await store.createIntegration(payload)
      toast.add({
        severity: 'success',
        summary: 'Success',
        detail: 'Integration created',
        life: 3000
      })
    }
    showDialog.value = false
  } catch (err) {
    const errorDetail = err.response?.data?.credentials?.[0] || 'Failed to save integration'
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: errorDetail,
      life: 3000
    })
  }
}

const deleteIntegration = (integration) => {
  confirm.require({
    message: `Delete "${integration.title || integration.definition_name}"?`,
    header: 'Confirm Delete',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await store.deleteIntegration(integration.id)
        toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Integration deleted',
          life: 3000
        })
      } catch (err) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete integration',
          life: 3000
        })
      }
    }
  })
}

const currentSchema = computed(() => {
  if (!selectedDefinitionCode.value) return null
  const def = store.getDefinitionByCode(selectedDefinitionCode.value)
  return def?.config_schema || null
})
</script>

<template>
  <div class="integrations-board">
    <div style="margin-bottom: 1.5rem; display: flex; justify-content: space-between; align-items: center;">
      <h2>{{ t('integrations.myIntegrations') }}</h2>
      <Button
        icon="pi pi-plus"
        label="Add Integration"
        @click="openCreateDialog"
        :disabled="store.loading"
      />
    </div>

    <DataTable
      :value="store.integrations"
      :loading="store.loading"
      :paginator="true"
      :rows="10"
      paginator-template="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
      :rows-per-page-options="[5, 10, 20]"
      current-page-report-template="Showing {first} to {last} of {totalRecords} integrations"
      responsive-layout="scroll"
      selection-mode="multiple"
      v-model:selection="selectedIntegrations"
      data-key="id"
      striped-rows
    >
      <Column selection-header-style="width: 3rem" header-style="width: 3rem" />

      <Column
        field="title"
        :header="t('common.name')"
        sortable
      />

      <Column
        field="definition_name"
        :header="t('integrations.type')"
        sortable
      />

      <Column
        field="definition_category"
        :header="t('integrations.category')"
        sortable
      >
        <template #body="{ data }">
          <Tag :value="data.definition_category" />
        </template>
      </Column>

      <Column
        field="status"
        :header="t('common.status')"
        sortable
      >
        <template #body="{ data }">
          <Tag
            :value="statusLabelMap[data.status] || data.status"
            :severity="statusSeverityMap[data.status] || 'info'"
          />
        </template>
      </Column>

      <Column :header="t('integrations.actions')" :style="{ width: '150px' }">
        <template #body="{ data }">
          <Button
            icon="pi pi-pencil"
            class="p-button-rounded p-button-text"
            @click="openEditDialog(data)"
            v-tooltip="'Edit'"
          />
          <Button
            icon="pi pi-trash"
            class="p-button-rounded p-button-text p-button-danger"
            @click="deleteIntegration(data)"
            v-tooltip="'Delete'"
          />
        </template>
      </Column>

      <template #empty>
        <div style="text-align: center; padding: 2rem; color: #6b7280;">
          {{ t('integrations.noIntegrations') }}
        </div>
      </template>

      <template #loading>
        <ProgressSpinner style="width: 32px; height: 32px;" stroke-width="6" />
      </template>
    </DataTable>

    <!-- Create/Edit Dialog -->
    <Dialog
      v-model:visible="showDialog"
      :header="editingIntegration ? 'Edit Integration' : 'Add New Integration'"
      :modal="true"
      :style="{ width: '500px' }"
    >
      <div class="form" v-if="!editingIntegration || !currentSchema">
        <div class="form-group">
          <label>Integration Title *</label>
          <InputText
            v-model="integrationTitle"
            placeholder="Name this integration"
            class="w-full"
            :disabled="store.loading"
          />
        </div>

        <div class="form-group">
          <label>Select Integration Type *</label>
          <Dropdown
            v-model="selectedDefinitionCode"
            :options="store.definitions"
            option-label="name"
            option-value="code"
            placeholder="Choose an integration..."
            class="w-full"
            :disabled="store.loading"
          />
        </div>
      </div>

      <div class="form" v-if="currentSchema">
        <div class="form-group">
          <label>{{ `Configure ${store.getDefinitionByCode(selectedDefinitionCode)?.name}` }}</label>
        </div>
        <DynamicSchemaForm
          :schema="currentSchema"
          :model-value="formData"
          :loading="store.loading"
          @update:model-value="formData = $event"
        />
      </div>

      <template #footer>
        <Button
          label="Cancel"
          icon="pi pi-times"
          @click="showDialog = false"
          class="p-button-text"
        />
        <Button
          label="Save"
          icon="pi pi-check"
          @click="saveIntegration"
          :loading="store.loading"
          :disabled="!integrationTitle.trim() || !selectedDefinitionCode"
        />
      </template>
    </Dialog>
  </div>
</template>

<style scoped lang="scss">
.integrations-board {
  padding: 1rem;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  font-size: 0.875rem;
  color: #374151;
}

:deep(.p-datatable) {
  font-size: 0.875rem;
}
</style>

<style scoped lang="scss">
.page {
  margin: 0;
}

.card {
  background: #ffffff;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 10px 20px rgba(15, 23, 42, 0.05);
}

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.grid-card {
  height: 100%;
}

.form {
  display: grid;
  gap: 16px;
}

.field {
  display: grid;
  gap: 8px;
  font-size: 14px;
  color: #374151;
}

.w-full {
  width: 100%;
}
</style>
