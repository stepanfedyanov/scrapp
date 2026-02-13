<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '~/src/entities/user'
import Toolbar from 'primevue/toolbar'
import Button from 'primevue/button'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const showNav = computed(() => !route.meta.public)

const logout = () => {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <Toolbar class="app-header">
    <template #start>
      <RouterLink class="brand" to="/">Scrapp</RouterLink>
    </template>
    <template #end>
      <div v-if="showNav" class="nav">
        <Button label="Блоги" text @click="$router.push('/blogs')" />
        <Button label="Интеграции" text @click="$router.push('/integrations')" />
        <Button label="Выйти" severity="danger" text @click="logout" />
      </div>
    </template>
  </Toolbar>
</template>

<style scoped lang="scss">
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e5e7eb;
  background: #ffffff;
  padding: 0 24px;
  min-height: 64px;
}

.brand {
  text-decoration: none;
  color: inherit;
  font-weight: 700;
  font-size: 18px;
}

.nav {
  display: flex;
  gap: 8px;
  align-items: center;
}

.app-header :deep(.p-toolbar) {
  padding: 0;
  width: 100%;
}

.app-header :deep(.p-toolbar-group-start),
.app-header :deep(.p-toolbar-group-end) {
  display: flex;
  align-items: center;
}
</style>
