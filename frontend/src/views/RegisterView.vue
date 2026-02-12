<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Password from 'primevue/password'
import Message from 'primevue/message'

const router = useRouter()
const auth = useAuthStore()
const form = reactive({
  username: '',
  email: '',
  password: ''
})
const error = ref('')
const loading = ref(false)

const submit = async () => {
  error.value = ''
  loading.value = true
  try {
    await auth.register(form)
    await auth.login({ username: form.username, password: form.password })
    router.push('/notes')
  } catch (err) {
    error.value = 'Не удалось создать аккаунт'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <Card class="card" style="max-width: 420px; margin: 40px auto;">
      <template #title>Регистрация</template>
      <template #content>
        <form @submit.prevent="submit" class="form">
          <label class="field">
            <span>Логин</span>
            <InputText v-model="form.username" class="w-full" />
          </label>
          <label class="field">
            <span>Email</span>
            <InputText v-model="form.email" class="w-full" />
          </label>
          <label class="field">
            <span>Пароль</span>
            <Password v-model="form.password" toggleMask :feedback="false" class="w-full" />
          </label>
          <Message v-if="error" severity="error" :closable="false" style="margin-bottom: 12px;">
            {{ error }}
          </Message>
          <Button label="Создать" type="submit" :loading="loading" class="w-full" />
        </form>
        <div style="margin-top: 16px; text-align: center;">
          <Button label="Уже есть аккаунт" text @click="$router.push('/login')" />
        </div>
      </template>
    </Card>
  </div>
</template>
