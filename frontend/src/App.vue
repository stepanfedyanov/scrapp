<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from './stores/auth'
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
  <div class="app-shell">
    <Toolbar class="app-header">
      <template #start>
        <div class="brand">Scrapp</div>
      </template>
      <template #end>
        <div v-if="showNav" class="nav">
          <Button label="Заметки" text @click="$router.push('/notes')" />
          <Button label="Интеграции" text @click="$router.push('/integrations')" />
          <Button label="Выйти" severity="danger" text @click="logout" />
        </div>
      </template>
    </Toolbar>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>
