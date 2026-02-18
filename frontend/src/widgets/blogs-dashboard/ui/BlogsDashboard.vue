<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useBlogsStore } from '~/src/entities/blog'
import { useNotesStore } from '~/src/entities/note'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import ProgressSpinner from 'primevue/progressspinner'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import Dropdown from 'primevue/dropdown'

const router = useRouter()
const { t } = useI18n()
const store = useBlogsStore()
const notesStore = useNotesStore()
const dialog = ref(false)
const form = reactive({
  title: ''
})
const blogFilter = ref('all')
const statusFilter = ref('all')

const blogOptions = computed(() => [
  { label: t('blogs.allBlogs'), value: 'all' },
  ...store.blogs.map((blog) => ({ label: blog.title, value: blog.uuid }))
])

const statusOptions = computed(() => [
  { label: t('status.all'), value: 'all' },
  { label: t('status.draft'), value: 'draft' },
  { label: t('status.scheduled'), value: 'scheduled' },
  { label: t('status.published'), value: 'published' },
  { label: t('status.archived'), value: 'archived' },
])

const filteredNotes = computed(() => {
  let items = notesStore.notes
  if (blogFilter.value !== 'all') {
    items = items.filter((note) => note.blog?.uuid === blogFilter.value)
  }
  if (statusFilter.value !== 'all') {
    items = items.filter((note) => note.status === statusFilter.value)
  }
  return items
})

const openNotes = (blogUuid) => {
  router.push(`/blogs/${blogUuid}/notes`)
}

const createBlog = async () => {
  const blog = await store.createBlog({ title: form.title || t('blogs.defaultTitle') })
  dialog.value = false
  form.title = ''
  openNotes(blog.uuid)
}

const removeBlog = async (blogId) => {
  await store.deleteBlog(blogId)
}

onMounted(() => {
  store.fetchBlogs()
  notesStore.fetchNotes()
})
</script>

<template>
  <div class="page">
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h2>{{ $t('blogs.title') }}</h2>
        <Button :label="$t('blogs.createBlog')" icon="pi pi-plus" @click="dialog = true" />
      </div>

      <div v-if="store.loading" style="display: flex; justify-content: center; padding: 24px;">
        <ProgressSpinner style="width: 32px; height: 32px;" strokeWidth="6" />
      </div>

      <div v-else class="grid">
        <Card v-for="blog in store.blogs" :key="blog.uuid" class="grid-card blog-card">
          <template #title>
            <div class="blog-title" :title="blog.title">{{ blog.title }}</div>
          </template>
          <template #content>
            <div style="color: #6b7280; margin-bottom: 12px;">
              {{ $t('blogs.updatedAt', { date: new Date(blog.updated_at).toLocaleString() }) }}
            </div>
            <div class="blog-card-actions">
              <Button :label="$t('blogs.notes')" text @click="openNotes(blog.uuid)" />
              <Button :label="$t('common.delete')" text severity="danger" @click="removeBlog(blog.uuid)" />
            </div>
          </template>
        </Card>
      </div>

      <div v-if="!store.loading && store.blogs.length === 0" style="text-align: center; color: #6b7280; padding: 24px;">
        {{ $t('blogs.noBlogsYet') }}
      </div>
    </div>

    <div class="card" style="margin-top: 16px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h2>{{ $t('notes.title') }}</h2>
      </div>

      <div style="display: flex; gap: 12px; margin-bottom: 16px;">
        <Dropdown
          v-model="blogFilter"
          :options="blogOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="$t('common.blog')"
          style="width: 240px;"
        />
        <Dropdown
          v-model="statusFilter"
          :options="statusOptions"
          optionLabel="label"
          optionValue="value"
          :placeholder="$t('common.status')"
          style="width: 220px;"
        />
      </div>

      <DataTable
        :value="filteredNotes"
        :loading="notesStore.loading"
        responsiveLayout="scroll"
      >
        <Column :header="$t('common.title')">
          <template #body="{ data }">
            <button class="note-title-link" type="button" @click="router.push(`/notes/${data.uuid}`)">
              {{ data.title || $t('common.untitled') }}
            </button>
          </template>
        </Column>
        <Column :header="$t('common.blog')" style="width: 220px;">
          <template #body="{ data }">
            {{ data.blog?.title || '—' }}
          </template>
        </Column>
        <Column :header="$t('common.status')" style="width: 180px;">
          <template #body="{ data }">
            <Tag v-if="data.status === 'draft'" severity="info">{{ $t('status.draft') }}</Tag>
            <Tag v-else-if="data.status === 'scheduled'" severity="warning">{{ $t('status.scheduled') }}</Tag>
            <Tag v-else-if="data.status === 'published'" severity="success">{{ $t('status.published') }}</Tag>
            <Tag v-else severity="secondary">{{ $t('status.archived') }}</Tag>
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

    <Dialog v-model:visible="dialog" :header="$t('blogs.newBlogDialog')" modal style="max-width: 420px;">
      <div class="form">
        <label class="field">
          <span>{{ $t('common.name') }}</span>
          <InputText v-model="form.title" class="w-full" />
        </label>
      </div>
      <template #footer>
        <Button :label="$t('common.cancel')" text @click="dialog = false" />
        <Button :label="$t('common.create')" @click="createBlog" />
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

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}

.grid-card {
  height: 100%;
}

.blog-card {
  display: flex;
  flex-direction: column;
}

.blog-card :deep(.p-card-body) {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.blog-card :deep(.p-card-content) {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.blog-title {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.blog-card-actions {
  margin-top: auto;
  display: flex;
  gap: 8px;
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
}

.w-full {
  width: 100%;
}

.note-title-link {
  background: none;
  border: none;
  padding: 0;
  color: #2563eb;
  cursor: pointer;
  font: inherit;
  text-align: left;
}

.note-title-link:hover {
  text-decoration: underline;
}
</style>
