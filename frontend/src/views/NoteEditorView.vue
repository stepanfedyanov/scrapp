<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '../api/client'
import { useNotesStore } from '../stores/notes'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Textarea from 'primevue/textarea'
import Calendar from 'primevue/calendar'
import Message from 'primevue/message'
import Tag from 'primevue/tag'

const route = useRoute()
const router = useRouter()
const store = useNotesStore()
const noteId = Number(route.params.id)

const note = reactive({
  id: noteId,
  title: '',
  body: '',
  status: 'draft',
  scheduled_at: null
})

const scheduleDialog = ref(false)
const integrationsDialog = ref(false)
const scheduleDate = ref(null)
const saving = ref(false)
const error = ref('')
const lastSaved = ref(null)

const storageKey = computed(() => `note-draft-${noteId}`)

const loadNote = async () => {
  const { data } = await api.get(`/notes/${noteId}/`)
  Object.assign(note, data)
  const localDraft = localStorage.getItem(storageKey.value)
  if (localDraft) {
    const parsed = JSON.parse(localDraft)
    Object.assign(note, parsed)
  }
}

const persistLocal = () => {
  localStorage.setItem(storageKey.value, JSON.stringify({
    title: note.title,
    body: note.body,
    status: note.status,
    scheduled_at: note.scheduled_at
  }))
}

let saveTimer = null
const scheduleSave = () => {
  persistLocal()
  if (saveTimer) clearTimeout(saveTimer)
  saveTimer = setTimeout(async () => {
    saving.value = true
    try {
      await store.updateNote(noteId, {
        title: note.title,
        body: note.body,
        status: note.status,
        scheduled_at: note.scheduled_at
      })
      lastSaved.value = new Date()
    } catch (err) {
      error.value = 'Не удалось сохранить изменения'
    } finally {
      saving.value = false
    }
  }, 600)
}

const openSchedule = () => {
  scheduleDate.value = note.scheduled_at ? new Date(note.scheduled_at) : new Date()
  scheduleDialog.value = true
}

const applySchedule = () => {
  note.status = 'scheduled'
  note.scheduled_at = scheduleDate.value ? scheduleDate.value.toISOString() : null
  scheduleDialog.value = false
}

const markPublished = async () => {
  note.status = 'published'
}

const deleteNote = async () => {
  await store.deleteNote(noteId)
  localStorage.removeItem(storageKey.value)
  router.push('/notes')
}

watch(() => [note.title, note.body, note.status, note.scheduled_at], scheduleSave)

onMounted(async () => {
  try {
    await loadNote()
  } catch (err) {
    error.value = 'Заметка не найдена'
  }
})
</script>

<template>
  <div class="page">
    <Card class="card">
      <template #title>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div>
            <div style="font-size: 20px; font-weight: 600;">Редактор</div>
            <div style="color: #6b7280; font-size: 13px;">
              <span v-if="saving">Сохранение...</span>
              <span v-else-if="lastSaved">Последнее сохранение: {{ lastSaved.toLocaleTimeString() }}</span>
            </div>
          </div>
          <div style="display: flex; gap: 8px;">
            <Button label="Интеграции" icon="pi pi-share-alt" outlined @click="integrationsDialog = true" />
            <Button label="Запланировать" icon="pi pi-calendar" outlined @click="openSchedule" />
            <Button label="Опубликовать" icon="pi pi-check" severity="success" @click="markPublished" />
            <Button label="Удалить" icon="pi pi-trash" severity="danger" outlined @click="deleteNote" />
          </div>
        </div>
      </template>
      <template #content>
        <Message v-if="error" severity="error" :closable="false" style="margin: 16px 0;">
          {{ error }}
        </Message>

        <div class="form">
          <label class="field">
            <span>Заголовок</span>
            <InputText v-model="note.title" placeholder="Введите заголовок" class="w-full" />
          </label>
          <label class="field">
            <span>Текст</span>
            <Textarea v-model="note.body" rows="12" placeholder="Текст заметки" class="w-full" autoResize />
          </label>
        </div>

      </template>
    </Card>

    <Dialog v-model:visible="scheduleDialog" header="Дата публикации" modal style="max-width: 420px;">
      <Calendar v-model="scheduleDate" showTime hourFormat="24" class="w-full" />
      <template #footer>
        <Button label="Отмена" text @click="scheduleDialog = false" />
        <Button label="Сохранить" @click="applySchedule" />
      </template>
    </Dialog>

    <Dialog v-model:visible="integrationsDialog" header="Интеграции" modal style="max-width: 720px;">
      <Message severity="info" :closable="false">
        Интеграции пока не активны. Настройки сохраняются для будущей автоматической публикации.
      </Message>
      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 12px; margin-top: 12px;">
        <Card>
          <template #title>Medium</template>
          <template #content>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>Статус</span>
              <Tag severity="success">Включено</Tag>
            </div>
            <div style="margin-top: 8px; color: #6b7280;">Фейковые поля для будущей интеграции.</div>
          </template>
        </Card>
        <Card>
          <template #title>Dev.to</template>
          <template #content>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>Статус</span>
              <Tag severity="secondary">Выключено</Tag>
            </div>
            <div style="margin-top: 8px; color: #6b7280;">Фейковые поля для будущей интеграции.</div>
          </template>
        </Card>
      </div>
      <template #footer>
        <Button label="Закрыть" text @click="integrationsDialog = false" />
      </template>
    </Dialog>
  </div>
</template>
