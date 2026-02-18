import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primevue/themes/aura'
import { definePreset } from '@primevue/themes'
import 'primeicons/primeicons.css'
import '~/src/app/styles/index.scss'
import App from '~/src/app/App.vue'
import router from '~/src/app/router'
import i18n from '~/src/shared/i18n'

const AquaPreset = definePreset(Aura, {
	semantic: {
		primary: {
			50: '{cyan.50}',
			100: '{cyan.100}',
			200: '{cyan.200}',
			300: '{cyan.300}',
			400: '{cyan.400}',
			500: '{cyan.500}',
			600: '{cyan.600}',
			700: '{cyan.700}',
			800: '{cyan.800}',
			900: '{cyan.900}',
			950: '{cyan.950}'
		}
	}
})

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(i18n)
app.use(PrimeVue, {
	theme: {
		preset: AquaPreset
	}
})
app.mount('#app')
