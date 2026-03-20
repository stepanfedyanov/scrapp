<script setup>
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useBlogsStore } from '~/src/entities/blog'
import { BlogDefaultIntegrations } from '~/src/widgets/blog-default-integrations'
import Button from 'primevue/button'
import Breadcrumb from 'primevue/breadcrumb'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const blogsStore = useBlogsStore()

const blogUuid = computed(() => route.params.uuid)
const blog = computed(() => blogsStore.blogs.find(b => b.uuid === blogUuid.value))

const breadcrumbItems = computed(() => [
  { label: t('blogs.title'), command: () => router.push('/blogs') },
  { label: blog.value?.title || t('common.loading'), disabled: true }
])

const breadcrumbHome = { icon: 'pi pi-home', command: () => router.push('/') }

onMounted(async () => {
  if (!blogsStore.blogs.length) {
    await blogsStore.fetchBlogs()
  }
})
</script>

<template>
  <div class="page">
    <div class="card">
      <Breadcrumb :home="breadcrumbHome" :model="breadcrumbItems" style="margin-bottom: 16px;" />
      
      <div class="header">
        <div>
          <h1>{{ $t('blogSettings.title') }}</h1>
          <p class="subtitle">{{ blog?.title }}</p>
        </div>
        <Button 
          :label="$t('common.back')" 
          icon="pi pi-arrow-left" 
          text
          @click="router.push('/blogs')"
        />
      </div>

      <BlogDefaultIntegrations v-if="blogUuid" :blog-uuid="blogUuid" />
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

.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;

  h1 {
    margin: 0 0 4px 0;
    font-size: 24px;
    font-weight: 700;
  }

  .subtitle {
    margin: 0;
    font-size: 14px;
    color: #6b7280;
  }
}
</style>
