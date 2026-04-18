import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import Aura from '@primeuix/themes/aura'
import { definePreset } from '@primeuix/themes'
import App from './App.vue'
import router from './router'
import './assets/global.css'
import 'primeicons/primeicons.css'
import { useThemeStore } from './stores/theme'

const AppPreset = definePreset(Aura, {
	semantic: {
		primary: {
			50:  '{emerald.50}',
			100: '{emerald.100}',
			200: '{emerald.200}',
			300: '{emerald.300}',
			400: '{emerald.400}',
			500: '{emerald.500}',
			600: '{emerald.600}',
			700: '{emerald.700}',
			800: '{emerald.800}',
			900: '{emerald.900}',
			950: '{emerald.950}',
		},
		borderRadius: {
			none: '0',
			xs:   '4px',
			sm:   '8px',
			md:   '12px',
			lg:   '16px',
			xl:   '20px',
		},
	},
	components: {
		button: {
			borderRadius: '9999px',
			paddingX: '1.4rem',
			paddingY: '.65rem',
			fontWeight: '500',
		},
		card: {
			borderRadius: '16px',
			shadow: '0 4px 20px rgba(0,0,0,.14)',
		},
		inputtext: {
			borderRadius: '10px',
		},
		select: {
			borderRadius: '10px',
		},
		multiselect: {
			borderRadius: '10px',
		},
		dialog: {
			borderRadius: '18px',
		},
		panel: {
			borderRadius: '16px',
		},
	}
})

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

app.use(PrimeVue, {
	ripple: true,
	theme: {
		preset: AppPreset,
		options: {
			darkModeSelector: '[data-theme="dark"]'
		}
	}
})

const theme = useThemeStore(pinia)
theme.init()

app.mount('#app')
