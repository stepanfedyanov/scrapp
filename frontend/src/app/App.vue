<script setup>
import { AppHeader } from '~/src/widgets/app-header'
</script>

<template>
  <div class="app-shell">
    <AppHeader />
    <main class="app-main">
      <router-view />
    </main>
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
