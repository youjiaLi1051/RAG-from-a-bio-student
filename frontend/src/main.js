import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import './style.css'

import ChatView from './views/ChatView.vue'
import FilesView from './views/FilesView.vue'
import HistoryView from './views/HistoryView.vue'
import SettingsView from './views/SettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/chat' },
    { path: '/chat', component: ChatView },
    { path: '/files', component: FilesView },
    { path: '/history', component: HistoryView },
    { path: '/settings', component: SettingsView },
  ],
})

createApp(App).use(router).mount('#app')
