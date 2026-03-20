<script setup>
import { onMounted } from 'vue'
import { AppHeader } from '~/src/widgets/app-header'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
import { useAuthStore } from '~/src/entities/user'

const authStore = useAuthStore()

onMounted(async () => {
  if (authStore.isAuthenticated) {
    try {
      await authStore.fetchUser()
    } catch {
      // token may be expired; router guards will handle redirect
    }
  }
})
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <main class="app-main">
      <router-view />
    </main>
    <Toast position="bottom-right" />
    <ConfirmDialog />
  </div>
</template>

<style scoped lang="scss">
.app-shell {
  min-height: 100vh;
}

.app-main {
  padding: 20px;
}
</style>
