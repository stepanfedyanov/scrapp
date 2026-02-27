<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useToast } from 'primevue/usetoast'
import { api } from '~/src/shared/api'
import { useNotesStore } from '~/src/entities/note'
import { NoteBlockText, NoteBlockHeader, BlockAdder } from '~/src/features/note-blocks'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Calendar from 'primevue/calendar'
import Toast from 'primevue/toast'
import Message from 'primevue/message'
import Tag from 'primevue/tag'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const toast = useToast()
const store = useNotesStore()
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
const scheduleDate = ref(null)
const saving = ref(false)
const lastSaved = ref(null)
const cachedServerData = ref(null)

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

  // special-case: brand new note with only default empty blocks
  if (
    serverData.headers.length === 0 &&
    serverData.text_contents.length === 0 &&
    localBlocksRaw
  ) {
    try {
      const lb = JSON.parse(localBlocksRaw)
      if (
        lb.length === 2 &&
        lb[0].type === 'header' && !lb[0].serverId && lb[0].text === '' &&
        lb[1].type === 'text' && !lb[1].serverId && lb[1].html === ''
      ) {
        // no actual edits yet; drop the draft so we don't warn the user
        clearLocal()
        return
      }
    } catch {}
  }

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
            <Button :label="$t('noteEditor.integrations')" icon="pi pi-share-alt" outlined @click="integrationsDialog = true" />
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
    <Dialog v-model:visible="integrationsDialog" :header="$t('noteEditor.integrationsDialog')" modal style="max-width: 720px;">
      <Message severity="info" :closable="false">
        {{ $t('noteEditor.integrationsNotActive') }}
      </Message>
      <div class="integrations-grid">
        <Card>
          <template #title>Medium</template>
          <template #content>
            <div class="integration-row">
              <span>{{ $t('noteEditor.integrationsStatus') }}</span>
              <Tag severity="success">{{ $t('noteEditor.enabled') }}</Tag>
            </div>
          </template>
        </Card>
        <Card>
          <template #title>Dev.to</template>
          <template #content>
            <div class="integration-row">
              <span>{{ $t('noteEditor.integrationsStatus') }}</span>
              <Tag severity="secondary">{{ $t('noteEditor.disabled') }}</Tag>
            </div>
          </template>
        </Card>
      </div>
      <template #footer>
        <Button :label="$t('common.close')" text @click="integrationsDialog = false" />
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

.integrations-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 12px;
  margin-top: 12px;
}

.integration-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
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