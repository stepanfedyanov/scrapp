<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useNotesStore } from '~/src/entities/note'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'

const route = useRoute()
const router = useRouter()
const store = useNotesStore()
const blogUuid = ref(route.params.id)
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
  const note = await store.createNote({
    title: 'Новая заметка',
    body: '',
    blog_uuid: blogUuid.value
  })
  router.push(`/notes/${note.uuid}`)
}

onMounted(() => {
  store.fetchNotes(blogUuid.value)
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
      <DataTable
        :value="filteredNotes"
        :loading="store.loading"
        responsiveLayout="scroll"
      >
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
            <Button label="Открыть" text @click="$router.push(`/notes/${data.uuid}`)" />
          </template>
        </Column>
        <template #loading>
          <div style="display: flex; justify-content: center; padding: 24px;">
            <ProgressSpinner style="width: 32px; height: 32px;" strokeWidth="6" />
          </div>
        </template>
        <template #empty>
          Заметок не найдено
        </template>
      </DataTable>
    </div>
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
</style>
