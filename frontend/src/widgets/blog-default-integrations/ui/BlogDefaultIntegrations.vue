<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useBlogsStore } from '~/src/entities/blog'
import { useIntegrationsStore } from '~/src/entities/integrations'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import InputSwitch from 'primevue/inputswitch'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import ProgressSpinner from 'primevue/progressspinner'
import DynamicSchemaForm from '~/src/shared/ui/forms/DynamicSchemaForm.vue'
import { useConfirm } from 'primevue/useconfirm'
import { useToast } from 'primevue/usetoast'

const props = defineProps({
  blogUuid: {
    type: String,
    required: true
  }
})

const { t } = useI18n()
const blogsStore = useBlogsStore()
const integrationsStore = useIntegrationsStore()
const confirm = useConfirm()
const toast = useToast()

const loading = ref(false)
const showAddDialog = ref(false)
const showConnectDialog = ref(false)
const selectedPickerOption = ref(null)
const selectedLibraryDefinitionCode = ref(null)
const newIntegrationTitle = ref('')
const connectFormData = ref({})
const newDefaultForm = ref({
  integration_id: null,
  publish_settings: {},
  is_enabled: true
})

const defaults = computed(() => blogsStore.getBlogDefaults(props.blogUuid))

const availableIntegrations = computed(() => {
  const usedIds = new Set(defaults.value.map(d => d.integration?.id))
  return integrationsStore.integrations.filter(i => !usedIds.has(i.id))
})

const integrationPickerOptions = computed(() => {
  const configured = availableIntegrations.value.map(i => ({
    label: i.title,
    description: i.definition?.name || '',
    kind: 'configured',
    integration_id: i.id
  }))

  const library = integrationsStore.definitions.map(definition => ({
    label: definition.name,
    description: definition.category || '',
    kind: 'library',
    definition_id: definition.id,
    definition_code: definition.code
  }))

  return [
    {
      label: t('blogDefaults.groupConfigured'),
      items: configured
    },
    {
      label: t('blogDefaults.groupLibrary'),
      items: library
    }
  ].filter(group => group.items.length > 0)
})

const selectedIntegrationDefinition = computed(() => {
  if (!newDefaultForm.value.integration_id) return null
  const integration = integrationsStore.integrations.find(
    i => i.id === newDefaultForm.value.integration_id
  )
  return integration?.definition
})

const publishSchema = computed(() => {
  return selectedIntegrationDefinition.value?.publish_schema || {}
})

const selectedLibraryDefinition = computed(() => {
  if (!selectedLibraryDefinitionCode.value) return null
  return integrationsStore.getDefinitionByCode(selectedLibraryDefinitionCode.value)
})

const selectedLibrarySchema = computed(() => {
  return selectedLibraryDefinition.value?.config_schema || {}
})

const loadData = async () => {
  loading.value = true
  try {
    await Promise.all([
      blogsStore.fetchBlogDefaults(props.blogUuid),
      integrationsStore.fetchIntegrations(),
      integrationsStore.fetchDefinitions()
    ])
  } catch (error) {
    console.error('Failed to load data:', error)
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail: t('blogDefaults.loadError'),
      life: 3000
    })
  } finally {
    loading.value = false
  }
}

const openAddDialog = () => {
  selectedPickerOption.value = null
  selectedLibraryDefinitionCode.value = null
  newIntegrationTitle.value = ''
  connectFormData.value = {}
  newDefaultForm.value = {
    integration_id: null,
    publish_settings: {},
    is_enabled: true
  }
  showAddDialog.value = true
}

const closeAddDialog = () => {
  showAddDialog.value = false
  selectedPickerOption.value = null
  selectedLibraryDefinitionCode.value = null
  newIntegrationTitle.value = ''
  connectFormData.value = {}
  newDefaultForm.value = {
    integration_id: null,
    publish_settings: {},
    is_enabled: true
  }
}

const handlePublishSettingsChange = (settings) => {
  newDefaultForm.value.publish_settings = settings
}

const openConnectDialogForDefinition = (definitionCode) => {
  selectedLibraryDefinitionCode.value = definitionCode
  const definition = integrationsStore.getDefinitionByCode(definitionCode)
  newIntegrationTitle.value = definition?.name || ''
  connectFormData.value = {}
  showConnectDialog.value = true
}

const closeConnectDialog = () => {
  showConnectDialog.value = false
  selectedLibraryDefinitionCode.value = null
  newIntegrationTitle.value = ''
  connectFormData.value = {}
}

const connectAndSelectIntegration = async () => {
  if (!selectedLibraryDefinitionCode.value) {
    return
  }

  loading.value = true
  try {
    if (!selectedLibraryDefinition.value) {
      throw new Error('Integration definition is not selected')
    }

    const createdIntegration = await integrationsStore.createIntegration({
      title: (newIntegrationTitle.value || selectedLibraryDefinition.value.name || selectedLibraryDefinition.value.code).trim(),
      definition_id: selectedLibraryDefinition.value.id,
      credentials: connectFormData.value
    })

    await integrationsStore.fetchIntegrations()

    newDefaultForm.value.integration_id = createdIntegration.id
    selectedPickerOption.value = {
      label: createdIntegration.title,
      description: createdIntegration.definition?.name || '',
      kind: 'configured',
      integration_id: createdIntegration.id
    }

    toast.add({
      severity: 'success',
      summary: t('common.success'),
      detail: t('blogDefaults.connected'),
      life: 3000
    })

    closeConnectDialog()
  } catch (error) {
    console.error('Failed to connect integration:', error)
    const detail = error.response?.data?.credentials?.[0] || t('blogDefaults.connectError')
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail,
      life: 4000
    })
  } finally {
    loading.value = false
  }
}

const createDefault = async () => {
  if (!newDefaultForm.value.integration_id) {
    return
  }

  loading.value = true
  try {
    await blogsStore.createBlogDefault(props.blogUuid, newDefaultForm.value)
    toast.add({
      severity: 'success',
      summary: t('common.success'),
      detail: t('blogDefaults.created'),
      life: 3000
    })
    closeAddDialog()
  } catch (error) {
    console.error('Failed to create default:', error)
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail: t('blogDefaults.createError'),
      life: 3000
    })
  } finally {
    loading.value = false
  }
}

watch(selectedPickerOption, (option) => {
  if (!option) {
    newDefaultForm.value.integration_id = null
    newDefaultForm.value.publish_settings = {}
    return
  }

  if (option.kind === 'configured') {
    newDefaultForm.value.integration_id = option.integration_id
    newDefaultForm.value.publish_settings = {}
    return
  }

  if (option.kind === 'library' && option.definition_code) {
    newDefaultForm.value.integration_id = null
    newDefaultForm.value.publish_settings = {}
    selectedPickerOption.value = null
    openConnectDialogForDefinition(option.definition_code)
  }
})

const toggleEnabled = async (defaultItem) => {
  loading.value = true
  try {
    await blogsStore.updateBlogDefault(defaultItem.id, {
      blog_uuid: props.blogUuid,
      integration_id: defaultItem.integration.id,
      is_enabled: !defaultItem.is_enabled,
      publish_settings: defaultItem.publish_settings
    })
    toast.add({
      severity: 'success',
      summary: t('common.success'),
      detail: t('blogDefaults.updated'),
      life: 3000
    })
  } catch (error) {
    console.error('Failed to toggle default:', error)
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail: t('blogDefaults.updateError'),
      life: 3000
    })
  } finally {
    loading.value = false
  }
}

const removeDefault = (defaultItem) => {
  confirm.require({
    message: t('blogDefaults.confirmDelete', { name: defaultItem.integration?.title }),
    header: t('common.confirmation'),
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      loading.value = true
      try {
        await blogsStore.deleteBlogDefault(defaultItem.id)
        toast.add({
          severity: 'success',
          summary: t('common.success'),
          detail: t('blogDefaults.deleted'),
          life: 3000
        })
      } catch (error) {
        console.error('Failed to delete default:', error)
        toast.add({
          severity: 'error',
          summary: t('common.error'),
          detail: t('blogDefaults.deleteError'),
          life: 3000
        })
      } finally {
        loading.value = false
      }
    }
  })
}

onMounted(loadData)
</script>

<template>
  <div class="blog-default-integrations">
    <div class="header">
      <div>
        <h3>{{ $t('blogDefaults.title') }}</h3>
        <p class="description">{{ $t('blogDefaults.description') }}</p>
      </div>
      <Button 
        :label="$t('blogDefaults.addIntegration')" 
        icon="pi pi-plus" 
        @click="openAddDialog"
        :disabled="loading || integrationPickerOptions.length === 0"
      />
    </div>

    <Message v-if="!loading && defaults.length === 0" severity="info">
      {{ $t('blogDefaults.noDefaults') }}
    </Message>

    <Message severity="warn" :closable="false" style="margin-bottom: 16px;">
      <i class="pi pi-info-circle" style="margin-right: 8px;"></i>
      {{ $t('blogDefaults.warning') }}
    </Message>

    <DataTable
      v-if="defaults.length > 0"
      :value="defaults"
      :loading="loading"
      responsiveLayout="scroll"
    >
      <Column :header="$t('common.integration')" style="min-width: 200px;">
        <template #body="{ data }">
          <div style="display: flex; align-items: center; gap: 8px;">
            <i class="pi pi-table" style="color: #6b7280;"></i>
            <span>{{ data.integration?.title || '—' }}</span>
          </div>
        </template>
      </Column>
      <Column :header="$t('common.type')" style="width: 150px;">
        <template #body="{ data }">
          <span style="color: #6b7280;">{{ data.integration?.definition?.name || '—' }}</span>
        </template>
      </Column>
      <Column :header="$t('common.enabled')" style="width: 120px;">
        <template #body="{ data }">
          <InputSwitch 
            :modelValue="data.is_enabled" 
            @update:modelValue="toggleEnabled(data)"
          />
        </template>
      </Column>
      <Column :header="$t('common.actions')" style="width: 140px;">
        <template #body="{ data }">
          <Button 
            icon="pi pi-trash" 
            text 
            severity="danger"
            @click="removeDefault(data)"
          />
        </template>
      </Column>
      <template #loading>
        <div style="display: flex; justify-content: center; padding: 24px;">
          <ProgressSpinner style="width: 32px; height: 32px;" strokeWidth="6" />
        </div>
      </template>
    </DataTable>

    <!-- Add Integration Dialog -->
    <Dialog 
      v-model:visible="showAddDialog" 
      :header="$t('blogDefaults.addIntegration')" 
      modal 
      style="max-width: 600px; width: 90vw;"
    >
      <div class="form">
        <label class="field">
          <span>{{ $t('common.integration') }}</span>
          <Dropdown
            v-model="selectedPickerOption"
            :options="integrationPickerOptions"
            optionGroupLabel="label"
            optionGroupChildren="items"
            optionLabel="label"
            :placeholder="$t('blogDefaults.selectIntegration')"
            class="w-full"
            filter
            :filterPlaceholder="$t('blogDefaults.searchIntegrations')"
          />
          <small class="hint">{{ $t('blogDefaults.selectHint') }}</small>
        </label>

        <div v-if="selectedIntegrationDefinition && publishSchema.properties">
          <h4>{{ $t('blogDefaults.publishSettings') }}</h4>
          <DynamicSchemaForm
            :schema="publishSchema"
            :modelValue="newDefaultForm.publish_settings"
            @update:modelValue="handlePublishSettingsChange"
          />
        </div>

        <label class="field">
          <div style="display: flex; align-items: center; gap: 8px;">
            <InputSwitch v-model="newDefaultForm.is_enabled" />
            <span>{{ $t('blogDefaults.enabledByDefault') }}</span>
          </div>
        </label>
      </div>

      <template #footer>
        <Button :label="$t('common.cancel')" text @click="closeAddDialog" />
        <Button 
          :label="$t('common.add')" 
          @click="createDefault"
          :disabled="!newDefaultForm.integration_id"
        />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="showConnectDialog"
      :header="$t('blogDefaults.connectDialogTitle', { name: selectedLibraryDefinition?.name || '' })"
      modal
      style="max-width: 600px; width: 90vw;"
    >
      <div class="form">
        <Message severity="info" :closable="false">
          {{ $t('blogDefaults.connectDialogDescription') }}
        </Message>

        <label class="field">
          <span>{{ $t('common.title') }}</span>
          <InputText
            v-model="newIntegrationTitle"
            :placeholder="$t('blogDefaults.integrationTitlePlaceholder')"
          />
        </label>

        <DynamicSchemaForm
          v-if="selectedLibrarySchema.properties"
          :schema="selectedLibrarySchema"
          :modelValue="connectFormData"
          @update:modelValue="connectFormData = $event"
        />
      </div>

      <template #footer>
        <Button :label="$t('common.cancel')" text @click="closeConnectDialog" />
        <Button
          :label="$t('blogDefaults.connectAndSelect')"
          @click="connectAndSelectIntegration"
          :loading="loading"
          :disabled="!newIntegrationTitle.trim()"
        />
      </template>
    </Dialog>
  </div>
</template>

<style scoped lang="scss">
.blog-default-integrations {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;

  h3 {
    margin: 0 0 4px 0;
    font-size: 18px;
    font-weight: 600;
  }

  .description {
    margin: 0;
    font-size: 14px;
    color: #6b7280;
  }
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

  span {
    font-weight: 500;
  }
}

.w-full {
  width: 100%;
}

.hint {
  color: #6b7280;
  font-size: 12px;
}

h4 {
  margin: 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}
</style>
