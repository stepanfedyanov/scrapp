<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { api } from '~/src/shared/api'
import Button from 'primevue/button'
import Card from 'primevue/card'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Tag from 'primevue/tag'
import ProgressSpinner from 'primevue/progressspinner'

const integrations = ref([])
const { t } = useI18n()
const loading = ref(false)
const dialog = ref(false)
const form = reactive({
  name: '',
  provider: 'medium'
})

const providerOptions = [
  { label: 'Medium', value: 'medium' },
  { label: 'Dev.to', value: 'devto' },
  { label: 'Telegram', value: 'telegram' }
]

const fetchIntegrations = async () => {
  loading.value = true
  try {
    const { data } = await api.get('/integrations/')
    integrations.value = data
  } finally {
    loading.value = false
  }
}

const createIntegration = async () => {
  const { data } = await api.post('/integrations/', form)
  integrations.value.unshift(data)
  dialog.value = false
  form.name = ''
  form.provider = 'medium'
}

onMounted(fetchIntegrations)
</script>

<template>
  <div class="page">
    <div class="card">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
        <h2>{{ $t('integrations.title') }}</h2>
        <Button :label="$t('integrations.add')" icon="pi pi-plus" @click="dialog = true" />
      </div>

      <div v-if="loading" style="display: flex; justify-content: center; padding: 24px;">
        <ProgressSpinner style="width: 32px; height: 32px;" strokeWidth="6" />
      </div>

      <div v-else class="grid">
        <Card v-for="integration in integrations" :key="integration.id" class="grid-card">
          <template #title>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span>{{ integration.name }}</span>
              <Tag>{{ integration.provider }}</Tag>
            </div>
          </template>
          <template #content>
            <div style="color: #6b7280;">
              {{ $t('integrations.settingsNotActive') }}
            </div>
          </template>
        </Card>
      </div>

      <div v-if="!loading && integrations.length === 0" style="text-align: center; color: #6b7280; padding: 24px;">
        {{ $t('integrations.noIntegrationsYet') }}
      </div>
    </div>

    <Dialog v-model:visible="dialog" :header="$t('integrations.newIntegrationDialog')" modal style="max-width: 420px;">
      <div class="form">
        <label class="field">
          <span>{{ $t('common.name') }}</span>
          <InputText v-model="form.name" class="w-full" />
        </label>
        <label class="field">
          <span>{{ $t('common.provider') }}</span>
          <Dropdown v-model="form.provider" :options="providerOptions" optionLabel="label" optionValue="value" class="w-full" />
        </label>
      </div>
      <template #footer>
        <Button :label="$t('common.cancel')" text @click="dialog = false" />
        <Button :label="$t('common.create')" @click="createIntegration" />
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
</style>
