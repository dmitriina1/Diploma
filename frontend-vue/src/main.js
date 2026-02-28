import { createApp } from 'vue'
import { createPinia } from 'pinia'
import PrimeVue from 'primevue/config'
import App from './App.vue'
import router from './router'

// PrimeVue styles
import 'primevue/resources/themes/lara-dark-purple/theme.css'
import 'primevue/resources/primevue.min.css'
import 'primeicons/primeicons.css'

// PrimeVue components
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Card from 'primevue/card'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Tag from 'primevue/tag'
import ProgressBar from 'primevue/progressbar'
import Dialog from 'primevue/dialog'
import Dropdown from 'primevue/dropdown'
import Textarea from 'primevue/textarea'
import Toast from 'primevue/toast'
import ToastService from 'primevue/toastservice'
import Checkbox from 'primevue/checkbox'
import Badge from 'primevue/badge'
import Chip from 'primevue/chip'
import Panel from 'primevue/panel'
import Divider from 'primevue/divider'
import SelectButton from 'primevue/selectbutton'
import TabView from 'primevue/tabview'
import TabPanel from 'primevue/tabpanel'
import ProgressSpinner from 'primevue/progressspinner'
import Message from 'primevue/message'
import Tooltip from 'primevue/tooltip'
import Slider from 'primevue/slider'
import Paginator from 'primevue/paginator'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(PrimeVue, { ripple: true })
app.use(ToastService)

// Register components
app.component('Button', Button)
app.component('InputText', InputText)
app.component('Card', Card)
app.component('DataTable', DataTable)
app.component('Column', Column)
app.component('Tag', Tag)
app.component('ProgressBar', ProgressBar)
app.component('Dialog', Dialog)
app.component('Dropdown', Dropdown)
app.component('Textarea', Textarea)
app.component('Toast', Toast)
app.component('Checkbox', Checkbox)
app.component('Badge', Badge)
app.component('Chip', Chip)
app.component('Panel', Panel)
app.component('Divider', Divider)
app.component('SelectButton', SelectButton)
app.component('TabView', TabView)
app.component('TabPanel', TabPanel)
app.component('ProgressSpinner', ProgressSpinner)
app.component('Message', Message)
app.component('Slider', Slider)
app.component('Paginator', Paginator)

// Register directives
app.directive('tooltip', Tooltip)

app.mount('#app')
