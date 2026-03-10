<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { useConfirm } from 'primevue/useconfirm'
import { api } from '~/src/shared/api'
import { useNotesStore } from '~/src/entities/note'
import { useIntegrationsStore } from '~/src/entities/integrations'
import { NoteBlockText, NoteBlockHeader, BlockAdder } from '~/src/features/note-blocks'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Calendar from 'primevue/calendar'
import Toast from 'primevue/toast'
import Message from 'primevue/message'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import InputSwitch from 'primevue/inputswitch'
import DynamicSchemaForm from '~/src/shared/ui/forms/DynamicSchemaForm.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const confirm = useConfirm()
const store = useNotesStore()
const integrationsStore = useIntegrationsStore()
const noteUuid = route.params.id

// ─── Note meta ───────────────────────────────────────────────────────────────
const note = reactive({
  title: '',
  status: 'draft',
  scheduled_at: null,
})

// ─── Block state ─────────────────────────────────────────────────────────────
const blocks = ref([])

// ─── UI state ────────────────────────────────────────────────────────────────
const scheduleDialog = ref(false)
const integrationsDialog = ref(false)
const addTargetDialog = ref(false)
const connectIntegrationDialog = ref(false)
const scheduleDate = ref(null)
const saving = ref(false)
const integrationsLoading = ref(false)
const lastSaved = ref(null)
const cachedServerData = ref(null)
const selectedTargetOption = ref(null)
const selectedLibraryDefinitionCode = ref(null)
const newIntegrationTitle = ref('')
const connectFormData = ref({})
const newTargetForm = ref({
  integration_id: null,
  publish_settings: {},
  is_enabled: true
})

// ─── Storage keys ────────────────────────────────────────────────────────────
const metaKey = computed(() => `note-draft-${noteUuid}`)
const blocksKey = computed(() => `note-blocks-${noteUuid}`)

// ─── Local persistence ───────────────────────────────────────────────────────
function persistLocal() {
  localStorage.setItem(metaKey.value, JSON.stringify({
    title: note.title,
    status: note.status,
    scheduled_at: note.scheduled_at,
    localUpdatedAt: new Date().toISOString(),
  }))
  localStorage.setItem(blocksKey.value, JSON.stringify(blocks.value))
}

function clearLocal() {
  localStorage.removeItem(metaKey.value)
  localStorage.removeItem(blocksKey.value)
}

// ─── Helpers ─────────────────────────────────────────────────────────────────
function uid() {
  return (crypto.randomUUID?.() ?? Math.random().toString(36).slice(2))
}

function reorder() {
  blocks.value.forEach((b, i) => { b.order = i })
}

// ─── Per-block API sync (debounced) ──────────────────────────────────────────
const syncTimers = new Map()

function scheduleBlockSync(block) {
  if (syncTimers.has(block.localId)) clearTimeout(syncTimers.get(block.localId))
  syncTimers.set(block.localId, setTimeout(() => syncBlock(block), 700))
}

async function syncBlock(block) {
  try {
    if (block.type === 'header') {
      const payload = { note_uuid: noteUuid, text: block.text, level: block.level, order: block.order }
      if (block.serverId) {
        await api.patch(`/note-headers/${block.serverId}/`, payload)
      } else {
        const { data } = await api.post('/note-headers/', payload)
        block.serverId = data.uuid
        persistLocal()
      }
    } else {
      const payload = { note_uuid: noteUuid, html: block.html, order: block.order }
      if (block.serverId) {
        await api.patch(`/note-text-contents/${block.serverId}/`, payload)
      } else {
        const { data } = await api.post('/note-text-contents/', payload)
        block.serverId = data.uuid
        persistLocal()
      }
    }
  } catch (e) {
    console.error('Block sync error', e)
    toast.add({
      severity: 'error',
      summary: t('noteEditor.saveErrorTitle'),
      detail: t('noteEditor.blockSyncError'),
      life: 6000,
    })
  }
}

async function deleteBlockFromServer(block) {
  if (!block.serverId) return
  try {
    const endpoint = block.type === 'header' ? 'note-headers' : 'note-text-contents'
    await api.delete(`/${endpoint}/${block.serverId}/`)
  } catch (e) {
    console.error('Block delete error', e)
  }
}

// ─── Block CRUD ──────────────────────────────────────────────────────────────
function addBlock(type, afterIndex) {
  const newBlock = {
    localId: uid(),
    serverId: null,
    type,
    order: 0,
    ...(type === 'header' ? { text: '', level: 2 } : { html: '' }),
  }
  blocks.value.splice(afterIndex + 1, 0, newBlock)
  reorder()
  persistLocal()
  syncBlock(newBlock)
}

function removeBlock(localId) {
  const idx = blocks.value.findIndex(b => b.localId === localId)
  if (idx === -1) return
  const block = blocks.value.splice(idx, 1)[0]
  reorder()
  persistLocal()
  deleteBlockFromServer(block)
}

function onBlockChange(block) {
  persistLocal()
  scheduleBlockSync(block)
}

const noteTargets = computed(() => integrationsStore.publishTargets)

const availableNoteIntegrations = computed(() => {
  const usedIds = new Set(noteTargets.value.map(t => t.integration?.id).filter(Boolean))
  return integrationsStore.integrations.filter(i => !usedIds.has(i.id))
})

const noteIntegrationPickerOptions = computed(() => {
  const configured = availableNoteIntegrations.value.map(i => ({
    label: i.title,
    description: i.definition?.name || '',
    kind: 'configured',
    integration_id: i.id
  }))

  const library = integrationsStore.definitions.map(definition => ({
    label: definition.name,
    description: definition.category || '',
    kind: 'library',
    definition_code: definition.code,
    definition_id: definition.id
  }))

  return [
    { label: t('noteEditor.groupConfigured'), items: configured },
    { label: t('noteEditor.groupLibrary'), items: library }
  ].filter(group => group.items.length > 0)
})

const selectedTargetIntegrationDefinition = computed(() => {
  if (!newTargetForm.value.integration_id) return null
  const integration = integrationsStore.integrations.find(i => i.id === newTargetForm.value.integration_id)
  return integration?.definition || null
})

const selectedTargetPublishSchema = computed(() => {
  return selectedTargetIntegrationDefinition.value?.publish_schema || {}
})

const selectedLibraryDefinition = computed(() => {
  if (!selectedLibraryDefinitionCode.value) return null
  return integrationsStore.getDefinitionByCode(selectedLibraryDefinitionCode.value)
})

const selectedLibrarySchema = computed(() => {
  return selectedLibraryDefinition.value?.config_schema || {}
})

const loadNoteIntegrations = async () => {
  integrationsLoading.value = true
  try {
    await Promise.all([
      integrationsStore.fetchPublishTargets({ content_type: 'note', object_id: noteUuid }),
      integrationsStore.fetchIntegrations(),
      integrationsStore.fetchDefinitions()
    ])
  } catch (error) {
    console.error('Failed to load note integrations', error)
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail: t('noteEditor.targetsLoadError'),
      life: 3000,
    })
  } finally {
    integrationsLoading.value = false
  }
}

const openIntegrationsDialog = async () => {
  integrationsDialog.value = true
  await loadNoteIntegrations()
}

const openAddTargetDialog = () => {
  selectedTargetOption.value = null
  selectedLibraryDefinitionCode.value = null
  newIntegrationTitle.value = ''
  connectFormData.value = {}
  newTargetForm.value = {
    integration_id: null,
    publish_settings: {},
    is_enabled: true
  }
  addTargetDialog.value = true
}

const closeAddTargetDialog = () => {
  addTargetDialog.value = false
  selectedTargetOption.value = null
  newTargetForm.value = {
    integration_id: null,
    publish_settings: {},
    is_enabled: true
  }
}

const openConnectIntegrationDialog = (definitionCode) => {
  selectedLibraryDefinitionCode.value = definitionCode
  const definition = integrationsStore.getDefinitionByCode(definitionCode)
  newIntegrationTitle.value = definition?.name || ''
  connectFormData.value = {}
  connectIntegrationDialog.value = true
}

const closeConnectIntegrationDialog = () => {
  connectIntegrationDialog.value = false
  selectedLibraryDefinitionCode.value = null
  newIntegrationTitle.value = ''
  connectFormData.value = {}
}

const connectAndSelectForTarget = async () => {
  if (!selectedLibraryDefinition.value) return

  integrationsLoading.value = true
  try {
    const integration = await integrationsStore.createIntegration({
      title: (newIntegrationTitle.value || selectedLibraryDefinition.value.name).trim(),
      definition_id: selectedLibraryDefinition.value.id,
      credentials: connectFormData.value
    })

    await integrationsStore.fetchIntegrations()
    newTargetForm.value.integration_id = integration.id
    selectedTargetOption.value = {
      label: integration.title,
      description: integration.definition?.name || '',
      kind: 'configured',
      integration_id: integration.id
    }

    toast.add({
      severity: 'success',
      summary: t('common.success'),
      detail: t('noteEditor.connected'),
      life: 3000,
    })

    closeConnectIntegrationDialog()
  } catch (error) {
    console.error('Failed to connect integration for note', error)
    const detail = error.response?.data?.credentials?.[0] || t('noteEditor.connectError')
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail,
      life: 3000,
    })
  } finally {
    integrationsLoading.value = false
  }
}

const addPublishTarget = async () => {
  if (!newTargetForm.value.integration_id) return

  integrationsLoading.value = true
  try {
    await integrationsStore.createPublishTarget({
      content_type: 'note',
      object_id: noteUuid,
      integration_id: newTargetForm.value.integration_id,
      publish_settings: newTargetForm.value.publish_settings,
      is_enabled: newTargetForm.value.is_enabled
    })
    await integrationsStore.fetchPublishTargets({ content_type: 'note', object_id: noteUuid })
    toast.add({
      severity: 'success',
      summary: t('common.success'),
      detail: t('noteEditor.targetAdded'),
      life: 3000,
    })
    closeAddTargetDialog()
  } catch (error) {
    console.error('Failed to add publish target', error)
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail: t('noteEditor.targetAddError'),
      life: 3000,
    })
  } finally {
    integrationsLoading.value = false
  }
}

const togglePublishTarget = async (target) => {
  integrationsLoading.value = true
  try {
    await integrationsStore.updatePublishTarget(target.id, {
      is_enabled: !target.is_enabled
    })
    await integrationsStore.fetchPublishTargets({ content_type: 'note', object_id: noteUuid })
  } catch (error) {
    console.error('Failed to toggle publish target', error)
    toast.add({
      severity: 'error',
      summary: t('common.error'),
      detail: t('noteEditor.targetUpdateError'),
      life: 3000,
    })
  } finally {
    integrationsLoading.value = false
  }
}

const deletePublishTarget = (target) => {
  confirm.require({
    message: t('noteEditor.targetDeleteConfirm', { name: target.integration?.title || 'integration' }),
    header: t('common.confirmation'),
    icon: 'pi pi-exclamation-triangle',
    accept: async () => {
      integrationsLoading.value = true
      try {
        await integrationsStore.deletePublishTarget(target.id)
        await integrationsStore.fetchPublishTargets({ content_type: 'note', object_id: noteUuid })
      } catch (error) {
        console.error('Failed to delete publish target', error)
        toast.add({
          severity: 'error',
          summary: t('common.error'),
          detail: t('noteEditor.targetDeleteError'),
          life: 3000,
        })
      } finally {
        integrationsLoading.value = false
      }
    }
  })
}

// ─── Note meta sync ──────────────────────────────────────────────────────────
let titleTimer = null
function scheduleTitleSave() {
  persistLocal()
  if (titleTimer) clearTimeout(titleTimer)
  titleTimer = setTimeout(async () => {
    saving.value = true
    try {
      await store.updateNote(noteUuid, {
        title: note.title,
        status: note.status,
        scheduled_at: note.scheduled_at,
      })
      lastSaved.value = new Date()
    } catch {
      toast.add({
        severity: 'error',
        summary: t('noteEditor.saveErrorTitle'),
        detail: t('noteEditor.saveErrorDetail'),
        life: 6000,
      })
    } finally {
      saving.value = false
    }
  }, 600)
}

// ─── Save all (retry) ─────────────────────────────────────────────────────────
async function saveAll() {
  saving.value = true
  toast.removeGroup('note-editor')
  try {
    // Fetch current server state to find orphaned blocks (deleted locally but still on server)
    const { data: freshServerData } = await api.get(`/notes/${noteUuid}/`)
    const localServerIds = new Set(blocks.value.map(b => b.serverId).filter(Boolean))

    const orphanedHeaders = (freshServerData.headers ?? []).filter(h => !localServerIds.has(h.uuid))
    const orphanedTexts = (freshServerData.text_contents ?? []).filter(t => !localServerIds.has(t.uuid))

    await Promise.all([
      ...orphanedHeaders.map(h => api.delete(`/note-headers/${h.uuid}/`)),
      ...orphanedTexts.map(t => api.delete(`/note-text-contents/${t.uuid}/`)),
    ])

    await store.updateNote(noteUuid, {
      title: note.title,
      status: note.status,
      scheduled_at: note.scheduled_at,
    })
    await Promise.all(blocks.value.map(block => syncBlock(block)))
    // Server is now authoritative — drop local draft entirely
    clearLocal()
    lastSaved.value = new Date()
    toast.add({
      severity: 'success',
      summary: t('noteEditor.savedSuccess'),
      life: 3000,
    })
  } catch {
    toast.add({
      severity: 'error',
      group: 'note-editor',
      summary: t('noteEditor.saveErrorTitle'),
      detail: t('noteEditor.saveErrorDetail'),
      sticky: true,
      data: { retryable: true, discardable: false },
    })
  } finally {
    saving.value = false
  }
}

// ─── Sync check ───────────────────────────────────────────────────────────────
function checkLocalVsServer(serverData) {
  const localMetaRaw = localStorage.getItem(metaKey.value)
  const localBlocksRaw = localStorage.getItem(blocksKey.value)
  if (!localMetaRaw && !localBlocksRaw) return

  const localMeta = localMetaRaw ? JSON.parse(localMetaRaw) : null
  const localUpdatedAt = localMeta?.localUpdatedAt ? new Date(localMeta.localUpdatedAt) : null
  const serverUpdatedAt = new Date(serverData.updated_at)

  // Server is strictly newer → another device/browser already saved a later version.
  // The current browser's local draft is stale — discard silently and keep server data.
  if (localUpdatedAt && serverUpdatedAt > localUpdatedAt) {
    clearLocal()
    return
  }

  // Local is newer (or has no timestamp = old format) → run a content diff to decide
  // whether there is actually anything unsaved or all debounced syncs succeeded.
  let mismatch = false

  if (localMeta) {
    if (localMeta.title !== serverData.title || localMeta.status !== serverData.status) {
      mismatch = true
    }
  }

  if (localBlocksRaw && !mismatch) {
    const localBlocks = JSON.parse(localBlocksRaw)

    // Any block without a serverId has never been persisted to the backend
    if (localBlocks.some(b => !b.serverId)) {
      mismatch = true
    }

    if (!mismatch) {
      // Build a lookup map of server blocks by UUID for O(1) access
      const serverHeaderMap = new Map((serverData.headers ?? []).map(h => [h.uuid, h]))
      const serverTextMap = new Map((serverData.text_contents ?? []).map(t => [t.uuid, t]))

      for (const b of localBlocks) {
        if (!b.serverId) continue
        if (b.type === 'header') {
          const srv = serverHeaderMap.get(b.serverId)
          if (!srv || srv.text !== b.text || srv.level !== b.level || srv.order !== b.order) {
            mismatch = true; break
          }
        } else {
          const srv = serverTextMap.get(b.serverId)
          if (!srv || srv.html !== b.html || srv.order !== b.order) {
            mismatch = true; break
          }
        }
      }

      if (!mismatch) {
        // Orphaned server blocks (deleted locally but DELETE call failed)
        const localServerIds = new Set(localBlocks.map(b => b.serverId).filter(Boolean))
        const serverBlockCount = (serverData.headers ?? []).length + (serverData.text_contents ?? []).length
        const referencedCount = [...localServerIds].filter(id =>
          (serverData.headers ?? []).some(h => h.uuid === id) ||
          (serverData.text_contents ?? []).some(t => t.uuid === id)
        ).length
        if (serverBlockCount !== referencedCount) mismatch = true
      }
    }
  }

  if (!mismatch) {
    // All debounced saves completed successfully — local and server are in sync
    clearLocal()
    return
  }

  // Real unsaved local changes: override reactive state with local draft and warn user
  if (localMeta) {
    Object.assign(note, {
      title: localMeta.title ?? note.title,
      status: localMeta.status ?? note.status,
      scheduled_at: localMeta.scheduled_at ?? note.scheduled_at,
    })
  }
  if (localBlocksRaw) {
    blocks.value = JSON.parse(localBlocksRaw)
  }

  toast.add({
    severity: 'warn',
    group: 'note-editor',
    summary: t('noteEditor.syncWarningTitle'),
    detail: t('noteEditor.syncWarningDetail'),
    sticky: true,
    data: { retryable: true, discardable: true },
  })
}

// ─── Discard local draft ──────────────────────────────────────────────────────
function discardLocal() {
  clearLocal()
  toast.removeGroup('note-editor')
  // Restore server state from cache (no extra round-trip)
  const data = cachedServerData.value
  if (!data) return
  Object.assign(note, { title: data.title, status: data.status, scheduled_at: data.scheduled_at })
  blocks.value = buildBlocksFromServer(data)
}

// ─── Load ─────────────────────────────────────────────────────────────────────
function buildBlocksFromServer(data) {
  const headers = (data.headers ?? []).map(h => ({
    localId: uid(),
    serverId: h.uuid,
    type: 'header',
    text: h.text,
    level: h.level,
    order: h.order,
  }))
  const texts = (data.text_contents ?? []).map(t => ({
    localId: uid(),
    serverId: t.uuid,
    type: 'text',
    html: t.html,
    order: t.order,
  }))
  return [...headers, ...texts].sort((a, b) => a.order - b.order)
}

async function loadNote() {
  const { data } = await api.get(`/notes/${noteUuid}/`)
  cachedServerData.value = data

  // Apply server data as the baseline; checkLocalVsServer() will override if local is newer
  Object.assign(note, { title: data.title, status: data.status, scheduled_at: data.scheduled_at })
  const serverBlocks = buildBlocksFromServer(data)
  if (serverBlocks.length > 0) {
    blocks.value = serverBlocks
  } else {
    // Seed default blocks for a brand new note (synced only on first edit)
    const header = { localId: uid(), serverId: null, type: 'header', text: '', level: 2, order: 0 }
    const text   = { localId: uid(), serverId: null, type: 'text',   html: '',  order: 1 }
    blocks.value = [header, text]
  }

  return data
}

// ─── Schedule / publish / delete ─────────────────────────────────────────────
const openSchedule = () => {
  scheduleDate.value = note.scheduled_at ? new Date(note.scheduled_at) : new Date()
  scheduleDialog.value = true
}

const applySchedule = () => {
  note.status = 'scheduled'
  note.scheduled_at = scheduleDate.value?.toISOString() ?? null
  scheduleDialog.value = false
  scheduleTitleSave()
}

const markPublished = () => {
  note.status = 'published'
  scheduleTitleSave()
}

const deleteNote = async () => {
  await store.deleteNote(noteUuid)
  clearLocal()
  router.push('/blogs')
}

watch(() => note.title, scheduleTitleSave)

watch(selectedTargetOption, (option) => {
  if (!option) {
    newTargetForm.value.integration_id = null
    newTargetForm.value.publish_settings = {}
    return
  }

  if (option.kind === 'configured') {
    newTargetForm.value.integration_id = option.integration_id
    newTargetForm.value.publish_settings = {}
    return
  }

  if (option.kind === 'library' && option.definition_code) {
    newTargetForm.value.integration_id = null
    newTargetForm.value.publish_settings = {}
    selectedTargetOption.value = null
    openConnectIntegrationDialog(option.definition_code)
  }
})

onMounted(async () => {
  try {
    const serverData = await loadNote()
    checkLocalVsServer(serverData)
  } catch {
    toast.add({
      severity: 'error',
      summary: t('noteEditor.notFound'),
      life: 8000,
    })
  }
})
</script>

<template>
  <div class="page">
    <Card class="card">
      <template #title>
        <div class="header-row">
          <div>
            <div class="editor-title">{{ $t('noteEditor.title') }}</div>
            <div class="save-status">
              <span v-if="saving">{{ $t('noteEditor.saving') }}</span>
              <span v-else-if="lastSaved">{{ $t('noteEditor.saved') }} {{ lastSaved.toLocaleTimeString() }}</span>
            </div>
          </div>
          <div class="actions">
            <Button :label="$t('noteEditor.integrations')" icon="pi pi-share-alt" outlined @click="openIntegrationsDialog" />
            <Button :label="$t('noteEditor.schedule')" icon="pi pi-calendar" outlined @click="openSchedule" />
            <Button :label="$t('noteEditor.publish')" icon="pi pi-check" severity="success" @click="markPublished" />
            <Button :label="$t('noteEditor.delete')" icon="pi pi-trash" severity="danger" outlined @click="deleteNote" />
          </div>
        </div>
      </template>

      <template #content>
        <!-- Note title -->
        <div class="field">
          <InputText v-model="note.title" :placeholder="$t('noteEditor.noteTitlePlaceholder')" class="title-input" />
        </div>

        <!-- Blocks -->
        <div class="blocks">
          <!-- Adder before first block -->
          <BlockAdder @add="addBlock($event, -1)" />

          <template v-for="(block, index) in blocks" :key="block.localId">
            <NoteBlockHeader
              v-if="block.type === 'header'"
              :text="block.text"
              :level="block.level"
              @update:text="block.text = $event; onBlockChange(block)"
              @update:level="block.level = $event; onBlockChange(block)"
              @delete="removeBlock(block.localId)"
            />
            <NoteBlockText
              v-else
              :model-value="block.html"
              @update:model-value="block.html = $event; onBlockChange(block)"
              @delete="removeBlock(block.localId)"
            />

            <!-- Adder after each block -->
            <BlockAdder @add="addBlock($event, index)" />
          </template>

          <!-- Empty state hint -->
          <div v-if="blocks.length === 0" class="empty-hint">
            {{ $t('noteEditor.emptyHint') }}
          </div>
        </div>
      </template>
    </Card>

    <!-- Schedule dialog -->
    <Dialog v-model:visible="scheduleDialog" :header="$t('noteEditor.scheduleDialog')" modal style="max-width: 420px;">
      <Calendar v-model="scheduleDate" showTime hourFormat="24" class="w-full" />
      <template #footer>
        <Button :label="$t('common.cancel')" text @click="scheduleDialog = false" />
        <Button :label="$t('common.save')" @click="applySchedule" />
      </template>
    </Dialog>

    <!-- Sync-error toast with retry / discard buttons -->
    <Toast group="note-editor" position="bottom-right">
      <template #message="{ message }">
        <div class="toast-sync">
          <i :class="`pi pi-${message.severity === 'warn' ? 'exclamation-triangle' : 'times-circle'}`" class="toast-sync-icon" />
          <div class="toast-sync-body">
            <div class="toast-sync-summary">{{ message.summary }}</div>
            <div class="toast-sync-detail">{{ message.detail }}</div>
          </div>
          <div class="toast-sync-actions">
            <Button
              v-if="message.data?.retryable"
              :label="$t('noteEditor.retrySave')"
              size="small"
              severity="contrast"
              @click="saveAll"
            />
            <Button
              v-if="message.data?.discardable"
              :label="$t('noteEditor.discardChanges')"
              size="small"
              severity="secondary"
              text
              @click="discardLocal"
            />
          </div>
        </div>
      </template>
    </Toast>

    <!-- Integrations dialog -->
    <Dialog v-model:visible="integrationsDialog" :header="$t('noteEditor.integrationsDialog')" modal style="max-width: 860px; width: 92vw;">
      <Message severity="info" :closable="false">
        {{ $t('noteEditor.integrationsDescription') }}
      </Message>

      <div class="integrations-toolbar">
        <Button
          :label="$t('noteEditor.addTarget')"
          icon="pi pi-plus"
          @click="openAddTargetDialog"
          :disabled="integrationsLoading || noteIntegrationPickerOptions.length === 0"
        />
      </div>

      <DataTable
        :value="noteTargets"
        :loading="integrationsLoading"
        responsive-layout="scroll"
      >
        <Column :header="$t('common.integration')" style="min-width: 220px;">
          <template #body="{ data }">
            <div>{{ data.integration?.title || '—' }}</div>
          </template>
        </Column>
        <Column :header="$t('common.type')" style="min-width: 160px;">
          <template #body="{ data }">
            <span class="muted">{{ data.integration?.definition?.name || '—' }}</span>
          </template>
        </Column>
        <Column :header="$t('common.enabled')" style="width: 120px;">
          <template #body="{ data }">
            <InputSwitch :modelValue="data.is_enabled" @update:modelValue="togglePublishTarget(data)" />
          </template>
        </Column>
        <Column :header="$t('common.actions')" style="width: 120px;">
          <template #body="{ data }">
            <Button icon="pi pi-trash" text severity="danger" @click="deletePublishTarget(data)" />
          </template>
        </Column>

        <template #empty>
          <div class="empty-targets">
            {{ $t('noteEditor.noTargets') }}
          </div>
        </template>
      </DataTable>

      <template #footer>
        <Button :label="$t('common.close')" text @click="integrationsDialog = false" />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="addTargetDialog"
      :header="$t('noteEditor.addTarget')"
      modal
      style="max-width: 640px; width: 92vw;"
    >
      <div class="form-grid">
        <label class="field-label">
          <span>{{ $t('common.integration') }}</span>
          <Dropdown
            v-model="selectedTargetOption"
            :options="noteIntegrationPickerOptions"
            optionGroupLabel="label"
            optionGroupChildren="items"
            optionLabel="label"
            :placeholder="$t('noteEditor.selectIntegration')"
            class="w-full"
            filter
            :filterPlaceholder="$t('noteEditor.searchIntegrations')"
          />
          <small class="field-hint">{{ $t('noteEditor.selectHint') }}</small>
        </label>

        <div v-if="selectedTargetPublishSchema.properties">
          <h4 class="sub-title">{{ $t('noteEditor.publishSettings') }}</h4>
          <DynamicSchemaForm
            :schema="selectedTargetPublishSchema"
            :modelValue="newTargetForm.publish_settings"
            @update:modelValue="newTargetForm.publish_settings = $event"
          />
        </div>

        <label class="field-inline">
          <InputSwitch v-model="newTargetForm.is_enabled" />
          <span>{{ $t('noteEditor.enabledByDefault') }}</span>
        </label>
      </div>

      <template #footer>
        <Button :label="$t('common.cancel')" text @click="closeAddTargetDialog" />
        <Button :label="$t('common.add')" :disabled="!newTargetForm.integration_id" @click="addPublishTarget" />
      </template>
    </Dialog>

    <Dialog
      v-model:visible="connectIntegrationDialog"
      :header="$t('noteEditor.connectDialogTitle', { name: selectedLibraryDefinition?.name || '' })"
      modal
      style="max-width: 640px; width: 92vw;"
    >
      <div class="form-grid">
        <Message severity="info" :closable="false">
          {{ $t('noteEditor.connectDialogDescription') }}
        </Message>

        <label class="field-label">
          <span>{{ $t('common.title') }}</span>
          <InputText v-model="newIntegrationTitle" :placeholder="$t('noteEditor.integrationTitlePlaceholder')" />
        </label>

        <DynamicSchemaForm
          v-if="selectedLibrarySchema.properties"
          :schema="selectedLibrarySchema"
          :modelValue="connectFormData"
          @update:modelValue="connectFormData = $event"
        />
      </div>

      <template #footer>
        <Button :label="$t('common.cancel')" text @click="closeConnectIntegrationDialog" />
        <Button
          :label="$t('noteEditor.connectAndSelect')"
          :disabled="!newIntegrationTitle.trim()"
          :loading="integrationsLoading"
          @click="connectAndSelectForTarget"
        />
      </template>
    </Dialog>
  </div>
</template>

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

.header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor-title {
  font-size: 20px;
  font-weight: 600;
}

.save-status {
  color: #6b7280;
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 8px;
}

.field {
  margin-bottom: 20px;
}

.title-input {
  width: 100%;
  font-size: 15px;
}

.blocks {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.empty-hint {
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
  padding: 16px 0 8px;
}

.integrations-toolbar {
  display: flex;
  justify-content: flex-end;
  margin: 12px 0;
}

.empty-targets {
  padding: 20px;
  text-align: center;
  color: #6b7280;
}

.form-grid {
  display: grid;
  gap: 12px;
}

.field-label {
  display: grid;
  gap: 8px;

  span {
    font-size: 14px;
    font-weight: 500;
    color: #374151;
  }
}

.field-hint {
  color: #6b7280;
  font-size: 12px;
}

.field-inline {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.sub-title {
  margin: 4px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.muted {
  color: #6b7280;
}

.w-full {
  width: 100%;
}

.toast-sync {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 4px 2px;

  .toast-sync-icon {
    font-size: 18px;
    margin-top: 2px;
    flex-shrink: 0;
  }

  .toast-sync-body {
    flex: 1;
    min-width: 0;

    .toast-sync-summary {
      font-weight: 600;
      font-size: 14px;
      margin-bottom: 4px;
    }

    .toast-sync-detail {
      font-size: 13px;
      color: #6b7280;
      line-height: 1.4;
    }
  }

  .toast-sync-actions {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex-shrink: 0;
  }
}
</style>