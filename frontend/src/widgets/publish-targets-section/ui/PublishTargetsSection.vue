<script setup>
import { onMounted, ref, computed } from 'vue'
import { useIntegrationsStore } from '~/src/entities/integrations'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import InputSwitch from 'primevue/inputswitch'
import Calendar from 'primevue/calendar'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'
import PublishLogsModal from '~/src/widgets/publish-logs-modal/ui/PublishLogsModal.vue'

const props = defineProps({
  contentTypeId: {
    type: String,
    required: true
  },
  objectId: {
    type: String,
    required: true
  }
})

const confirm = useConfirm()
const toast = useToast()
const store = useIntegrationsStore()

const showLogsModal = ref(false)
const selectedPublishTargetId = ref(null)

const statusSeverityMap = {
  draft: 'secondary',
  queued: 'info',
  published: 'success',
  failed: 'danger'
}

const statusLabelMap = {
  draft: 'Draft',
  queued: 'Queued',
  published: 'Published',
  failed: 'Failed'
}

const applicableTargets = computed(() => {
  return store.publishTargets.filter(
    pt => pt.content_type_id === props.contentTypeId && pt.object_id === props.objectId
  )
})

const loadTargets = async () => {
  try {
    await store.fetchPublishTargets({
      content_type_id: props.contentTypeId,
      object_id: props.objectId
    })
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to load publish targets',
      life: 3000
    })
  }
}

onMounted(loadTargets)

const toggleTarget = async (target) => {
  try {
    await store.updatePublishTarget(target.id, {
      is_enabled: !target.is_enabled
    })
    toast.add({
      severity: 'success',
      summary: 'Success',
      detail: `Target ${target.is_enabled ? 'enabled' : 'disabled'}`,
      life: 3000
    })
  } catch (err) {
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: 'Failed to update target',
      life: 3000
    })
  }
}

const publishNow = (target) => {
  confirm.require({
    message: `Publish to ${target.integration_title}?`,
    header: 'Confirm Publish',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await store.publishTarget(target.id)
        toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Published successfully',
          life: 3000
        })
      } catch (err) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: err.response?.data?.detail || 'Failed to publish',
          life: 3000
        })
      }
    }
  })
}

const viewLogs = (target) => {
  selectedPublishTargetId.value = target.id
  showLogsModal.value = true
}

const deleteTarget = (target) => {
  confirm.require({
    message: `Remove ${target.integration_title}?`,
    header: 'Confirm Delete',
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      try {
        await store.deletePublishTarget(target.id)
        toast.add({
          severity: 'success',
          summary: 'Success',
          detail: 'Target removed',
          life: 3000
        })
      } catch (err) {
        toast.add({
          severity: 'error',
          summary: 'Error',
          detail: 'Failed to delete target',
          life: 3000
        })
      }
    }
  })
}
</script>

<template>
  <div class="publish-targets-section">
    <h3 style="margin-bottom: 1rem; font-size: 1.125rem; font-weight: 600;">
      Publish Targets
    </h3>

    <div v-if="store.loading" style="display: flex; justify-content: center; padding: 2rem;">
      <ProgressSpinner style="width: 32px; height: 32px;" stroke-width="6" />
    </div>

    <div v-else-if="applicableTargets.length === 0" style="text-align: center; padding: 2rem; color: #6b7280; background-color: #f9fafb; border-radius: 0.375rem;">
      No publish targets configured for this content
    </div>

    <DataTable
      v-else
      :value="applicableTargets"
      striped-rows
      style="font-size: 0.875rem;"
    >
      <Column
        field="integration_title"
        header="Integration"
        sortable
      />

      <Column
        field="status"
        header="Status"
        :style="{ width: '120px' }"
      >
        <template #body="{ data }">
          <Tag
            :value="statusLabelMap[data.status] || data.status"
            :severity="statusSeverityMap[data.status]"
          />
        </template>
      </Column>

      <Column
        header="Enabled"
        :style="{ width: '100px' }"
      >
        <template #body="{ data }">
          <InputSwitch
            :model-value="data.is_enabled"
            :disabled="store.loading"
            @update:model-value="toggleTarget(data)"
          />
        </template>
      </Column>

      <Column
        field="scheduled_at"
        header="Scheduled"
        :style="{ width: '150px' }"
      >
        <template #body="{ data }">
          <span v-if="data.scheduled_at" style="font-size: 0.75rem;">
            {{ new Date(data.scheduled_at).toLocaleString() }}
          </span>
          <span v-else style="color: #9ca3af;">—</span>
        </template>
      </Column>

      <Column
        field="last_published_at"
        header="Last Published"
        :style="{ width: '150px' }"
      >
        <template #body="{ data }">
          <span v-if="data.last_published_at" style="font-size: 0.75rem;">
            {{ new Date(data.last_published_at).toLocaleString() }}
          </span>
          <span v-else style="color: #9ca3af;">—</span>
        </template>
      </Column>

      <Column header="Actions" :style="{ width: '180px' }">
        <template #body="{ data }">
          <Button
            icon="pi pi-send"
            class="p-button-rounded p-button-text p-button-sm"
            @click="publishNow(data)"
            :disabled="store.loading || !data.is_enabled"
            v-tooltip="'Publish Now'"
          />
          <Button
            icon="pi pi-list"
            class="p-button-rounded p-button-text p-button-sm"
            @click="viewLogs(data)"
            :disabled="store.loading"
            v-tooltip="'View Logs'"
          />
          <Button
            icon="pi pi-trash"
            class="p-button-rounded p-button-text p-button-danger p-button-sm"
            @click="deleteTarget(data)"
            :disabled="store.loading"
            v-tooltip="'Delete'"
          />
        </template>
      </Column>
    </DataTable>

    <PublishLogsModal
      v-if="showLogsModal"
      :visible="showLogsModal"
      :publish-target-id="selectedPublishTargetId"
      @update:visible="showLogsModal = $event"
    />

  </div>
</template>

<style scoped lang="scss">
.publish-targets-section {
  padding: 1.5rem;
  background-color: #f9fafb;
  border-radius: 0.375rem;
  border: 1px solid #e5e7eb;
}
</style>
