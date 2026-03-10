<script setup>
import { onMounted, ref } from 'vue'
import { useIntegrationsStore } from '~/src/entities/integrations'
import Dialog from 'primevue/dialog'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import Button from 'primevue/button'
import Panel from 'primevue/panel'
import { useToast } from 'primevue/usetoast'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  publishTargetId: {
    type: [String, Number],
    required: true
  }
})

const emit = defineEmits(['update:visible'])

const toast = useToast()
const store = useIntegrationsStore()
const expandedRows = ref([])

const statusSeverityMap = {
  success: 'success',
  error: 'danger'
}

const statusLabelMap = {
  success: 'Success',
  error: 'Error'
}

const loadLogs = async () => {
  try {
    await store.fetchPublishLogs(props.publishTargetId, { ordering: '-created_at' })
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load logs',
      life: 3000
    })
  }
}

onMounted(loadLogs)

const closeDialog = () => {
  emit('update:visible', false)
}

const formatJson = (obj) => {
  return JSON.stringify(obj, null, 2)
}
</script>

<template>
  <Dialog
    :visible="visible"
    header="Publish Logs"
    modal
    :style="{ width: '800px' }"
    @update:visible="closeDialog"
  >
    <div v-if="store.loading" style="display: flex; justify-content: center; padding: 2rem;">
      <ProgressSpinner style="width: 32px; height: 32px;" stroke-width="6" />
    </div>

    <div v-else-if="store.publishLogs.length === 0" style="text-align: center; padding: 2rem; color: #6b7280;">
      No logs available
    </div>

    <DataTable
      v-else
      :value="store.publishLogs"
      v-model:expandedRows="expandedRows"
      striped-rows
      expandable-rows
      responsive-layout="scroll"
    >
      <Column :expander="true" :style="{ width: '3rem' }" />

      <Column
        field="created_at"
        header="Date"
        sortable
        :style="{ width: '150px' }"
      >
        <template #body="{ data }">
          <span style="font-size: 0.875rem;">
            {{ new Date(data.created_at).toLocaleString() }}
          </span>
        </template>
      </Column>

      <Column
        field="status"
        header="Status"
        :style="{ width: '100px' }"
      >
        <template #body="{ data }">
          <Tag
            :value="statusLabelMap[data.status] || data.status"
            :severity="statusSeverityMap[data.status]"
          />
        </template>
      </Column>

      <Column
        field="error_message"
        header="Message"
      >
        <template #body="{ data }">
          <span v-if="data.error_message" style="font-size: 0.875rem;">
            {{ data.error_message.substring(0, 50) }}{{ data.error_message.length > 50 ? '...' : '' }}
          </span>
          <span v-else style="color: #9ca3af;">—</span>
        </template>
      </Column>

      <template #expansion="{ data }">
        <div style="padding: 2rem; background-color: #f9fafb;">
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">
            <Panel v-if="data.request_payload" header="Request" :toggleable="true" :collapsed="true">
              <pre style="background-color: #fff; padding: 1rem; border-radius: 0.375rem; overflow-x: auto; font-size: 0.75rem;">{{ formatJson(data.request_payload) }}</pre>
            </Panel>

            <Panel v-if="data.response_payload" header="Response" :toggleable="true" :collapsed="true">
              <pre style="background-color: #fff; padding: 1rem; border-radius: 0.375rem; overflow-x: auto; font-size: 0.75rem;">{{ formatJson(data.response_payload) }}</pre>
            </Panel>
          </div>
        </div>
      </template>

      <template #empty>
        <div style="text-align: center; padding: 2rem; color: #6b7280;">
          No logs found
        </div>
      </template>
    </DataTable>

    <template #footer>
      <Button label="Close" @click="closeDialog" />
    </template>
  </Dialog>
</template>

<style scoped lang="scss">
:deep(.p-datatable) {
  font-size: 0.875rem;
}

:deep(.p-panel) {
  margin: 0;
}

pre {
  color: #374151;
  margin: 0;
}
</style>
