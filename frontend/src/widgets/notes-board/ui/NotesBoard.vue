<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useNotesStore } from '~/src/entities/note'
import Button from 'primevue/button'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const store = useNotesStore()
const blogUuid = ref(route.params.id)
const statusFilter = ref('all')

const statusLabels = computed(() => ({
  draft: t('status.draft'),
  scheduled: t('status.scheduled'),
  published: t('status.published'),
  archived: t('status.archived'),
}))

const statusOptions = computed(() => [
  { label: t('notes.all'), value: 'all' },
  { label: t('status.draft'), value: 'draft' },
  { label: t('status.scheduled'), value: 'scheduled' },
  { label: t('status.published'), value: 'published' },
  { label: t('status.archived'), value: 'archived' },
])

const filteredNotes = computed(() => {
  if (statusFilter.value === 'all') return store.notes
  return store.notes.filter((note) => note.status === statusFilter.value)
})

const createNote = async () => {
  const note = await store.createNote({
    title: t('notes.defaultTitle'),
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
        <h2>{{ $t('notes.title') }}</h2>
        <Button :label="$t('notes.newNote')" icon="pi pi-plus" @click="createNote" />
      </div>
      <div style="display: flex; gap: 12px; margin-bottom: 16px;">
        <Dropdown v-model="statusFilter" :options="statusOptions" optionLabel="label" optionValue="value" :placeholder="$t('common.status')" style="width: 220px;" />
      </div>
      <DataTable
        :value="filteredNotes"
        :loading="store.loading"
        responsiveLayout="scroll"
      >
        <Column field="title" :header="$t('common.title')" />
        <Column :header="$t('common.status')" style="width: 180px;">
          <template #body="{ data }">
            <Tag v-if="data.status === 'draft'" severity="info">{{ statusLabels.draft }}</Tag>
            <Tag v-else-if="data.status === 'scheduled'" severity="warning">{{ statusLabels.scheduled }}</Tag>
            <Tag v-else-if="data.status === 'published'" severity="success">{{ statusLabels.published }}</Tag>
            <Tag v-else severity="secondary">{{ statusLabels.archived }}</Tag>
          </template>
        </Column>
        <Column :header="$t('common.updated')" style="width: 220px;">
          <template #body="{ data }">
            {{ new Date(data.updated_at).toLocaleString() }}
          </template>
        </Column>
        <Column style="width: 140px;">
          <template #body="{ data }">
            <Button :label="$t('common.open')" text @click="$router.push(`/notes/${data.uuid}`)" />
          </template>
        </Column>
        <template #loading>
          <div style="display: flex; justify-content: center; padding: 24px;">
            <ProgressSpinner style="width: 32px; height: 32px;" strokeWidth="6" />
          </div>
        </template>
        <template #empty>
          {{ $t('notes.noNotesFound') }}
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
