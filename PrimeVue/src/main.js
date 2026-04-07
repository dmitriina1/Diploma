import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import App from './App.vue'
import router from './router'
import './assets/global.css'
import 'primeicons/primeicons.css'
import { useThemeStore } from './stores/theme'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

app.use(PrimeVue, {
	ripple: true,
	theme: {
		preset: Aura,
		options: {
			darkModeSelector: '[data-theme="dark"]'
		}
	}
})

const theme = useThemeStore(pinia)
theme.init()

app.mount('#app')
