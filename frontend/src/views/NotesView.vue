<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useNotesStore } from '../stores/notes'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'

const router = useRouter()
const store = useNotesStore()
const statusFilter = ref('all')

const statusLabels = {
  draft: 'Заметка',
  scheduled: 'Запланировано',
  published: 'Опубликовано',
  archived: 'В архиве'
}

const statusOptions = [
  { label: 'Все', value: 'all' },
  { label: 'Заметка', value: 'draft' },
  { label: 'Запланировано', value: 'scheduled' },
  { label: 'Опубликовано', value: 'published' },
  { label: 'В архиве', value: 'archived' }
]

const filteredNotes = computed(() => {
  if (statusFilter.value === 'all') return store.notes
  return store.notes.filter((note) => note.status === statusFilter.value)
})

const createNote = async () => {
  const note = await store.createNote({ title: 'Новая заметка', body: '' })
  router.push(`/notes/${note.id}`)
}

onMounted(() => {
  store.fetchNotes()
})
</script>

<template>
  <div class="page">
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h2>Заметки</h2>
        <Button label="Новая заметка" icon="pi pi-plus" @click="createNote" />
      </div>
      <div style="display: flex; gap: 12px; margin-bottom: 16px;">
        <Dropdown v-model="statusFilter" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="Статус" style="width: 220px;" />
      </div>
      <DataTable :value="filteredNotes" :loading="store.loading" responsiveLayout="scroll">
        <Column field="title" header="Заголовок" />
        <Column header="Статус" style="width: 180px;">
          <template #body="{ data }">
            <Tag v-if="data.status === 'draft'" severity="info">{{ statusLabels.draft }}</Tag>
            <Tag v-else-if="data.status === 'scheduled'" severity="warning">{{ statusLabels.scheduled }}</Tag>
            <Tag v-else-if="data.status === 'published'" severity="success">{{ statusLabels.published }}</Tag>
            <Tag v-else severity="secondary">{{ statusLabels.archived }}</Tag>
          </template>
        </Column>
        <Column header="Обновлено" style="width: 220px;">
          <template #body="{ data }">
            {{ new Date(data.updated_at).toLocaleString() }}
          </template>
        </Column>
        <Column style="width: 140px;">
          <template #body="{ data }">
            <Button label="Открыть" text @click="$router.push(`/notes/${data.id}`)" />
          </template>
        </Column>
      </DataTable>
    </div>
  </div>
</template>
