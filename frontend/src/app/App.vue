<script setup>
import { AppHeader } from '~/src/widgets/app-header'
import Toast from 'primevue/toast'
import ConfirmDialog from 'primevue/confirmdialog'
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
