<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '~/src/entities/user'
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Message from 'primevue/message'

const router = useRouter()
const auth = useAuthStore()
const form = reactive({
  username: '',
  password: ''
})
const error = ref('')
const loading = ref(false)

const submit = async () => {
  error.value = ''
  loading.value = true
  try {
    await auth.login(form)
    router.push('/blogs')
  } catch (err) {
    error.value = 'Неверный логин или пароль'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <Card class="card" style="max-width: 420px; margin: 40px auto;">
      <template #title>Вход</template>
      <template #content>
        <form @submit.prevent="submit" class="form">
          <label class="field">
            <span>Логин</span>
            <InputText v-model="form.username" class="w-full" />
          </label>
          <label class="field">
            <span>Пароль</span>
            <Password
              v-model="form.password"
              toggleMask
              :feedback="false"
              class="w-full"
              inputClass="w-full"
            />
          </label>
          <Message v-if="error" severity="error" :closable="false" style="margin-bottom: 12px;">
            {{ error }}
          </Message>
          <Button label="Войти" type="submit" :loading="loading" class="w-full" />
        </form>
        <div style="margin-top: 16px; text-align: center;">
          <Button label="Создать аккаунт" text @click="$router.push('/register')" />
        </div>
      </template>
    </Card>
  </div>
</template>

<style scoped lang="scss">
.page {
  display: flex;
  justify-content: center;
  padding: 40px 0;
}

.card {
  width: min(420px, 100%);
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

.field :deep(.p-password),
.field :deep(.p-inputtext) {
  width: 100%;
}

.field :deep(.p-password-input) {
  width: 100%;
}
</style>
