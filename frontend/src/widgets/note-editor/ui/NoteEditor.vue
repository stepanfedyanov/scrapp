<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { api } from '~/src/shared/api'
import { useNotesStore } from '~/src/entities/note'
import { NoteBlockText, NoteBlockHeader, BlockAdder } from '~/src/features/note-blocks'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Calendar from 'primevue/calendar'
import Message from 'primevue/message'
import Tag from 'primevue/tag'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
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
const error = ref('')
const lastSaved = ref(null)

// ─── Storage keys ────────────────────────────────────────────────────────────
const metaKey = computed(() => `note-draft-${noteUuid}`)
const blocksKey = computed(() => `note-blocks-${noteUuid}`)

// ─── Local persistence ───────────────────────────────────────────────────────
function persistLocal() {
  localStorage.setItem(metaKey.value, JSON.stringify({
    title: note.title,
    status: note.status,
    scheduled_at: note.scheduled_at,
  }))
  localStorage.setItem(blocksKey.value, JSON.stringify(blocks.value))
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
        block.serverId = data.id
        persistLocal()
      }
    } else {
      const payload = { note_uuid: noteUuid, html: block.html, order: block.order }
      if (block.serverId) {
        await api.patch(`/note-text-contents/${block.serverId}/`, payload)
      } else {
        const { data } = await api.post('/note-text-contents/', payload)
        block.serverId = data.id
        persistLocal()
      }
    }
  } catch (e) {
    console.error('Block sync error', e)
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
      error.value = t('noteEditor.saveError')
    } finally {
      saving.value = false
    }
  }, 600)
}

// ─── Load ─────────────────────────────────────────────────────────────────────
function buildBlocksFromServer(data) {
  const headers = (data.headers ?? []).map(h => ({
    localId: uid(),
    serverId: h.id,
    type: 'header',
    text: h.text,
    level: h.level,
    order: h.order,
  }))
  const texts = (data.text_contents ?? []).map(t => ({
    localId: uid(),
    serverId: t.id,
    type: 'text',
    html: t.html,
    order: t.order,
  }))
  return [...headers, ...texts].sort((a, b) => a.order - b.order)
}

async function loadNote() {
  const { data } = await api.get(`/notes/${noteUuid}/`)
  Object.assign(note, { title: data.title, status: data.status, scheduled_at: data.scheduled_at })

  const localMeta = localStorage.getItem(metaKey.value)
  if (localMeta) Object.assign(note, JSON.parse(localMeta))

  const localBlocks = localStorage.getItem(blocksKey.value)
  const serverBlocks = buildBlocksFromServer(data)
  if (localBlocks) {
    blocks.value = JSON.parse(localBlocks)
  } else if (serverBlocks.length > 0) {
    blocks.value = serverBlocks
  } else {
    // Seed default blocks for a brand new note
    const header = { localId: uid(), serverId: null, type: 'header', text: '', level: 2, order: 0 }
    const text   = { localId: uid(), serverId: null, type: 'text',   html: '',  order: 1 }
    blocks.value = [header, text]
    syncBlock(header)
    syncBlock(text)
  }
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
  localStorage.removeItem(metaKey.value)
  localStorage.removeItem(blocksKey.value)
  router.push('/blogs')
}

watch(() => note.title, scheduleTitleSave)

onMounted(async () => {
  try {
    await loadNote()
  } catch {
    error.value = t('noteEditor.notFound')
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
        <Message v-if="error" severity="error" :closable="false" class="error-msg">
          {{ error }}
        </Message>

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

.error-msg {
  margin: 16px 0;
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
</style>