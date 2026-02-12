import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import RegisterView from '../views/RegisterView.vue'
import NotesView from '../views/NotesView.vue'
import NoteEditorView from '../views/NoteEditorView.vue'
import IntegrationsView from '../views/IntegrationsView.vue'

const routes = [
  { path: '/', redirect: '/notes' },
  { path: '/login', component: LoginView, meta: { public: true } },
  { path: '/register', component: RegisterView, meta: { public: true } },
  { path: '/notes', component: NotesView },
  { path: '/notes/:id', component: NoteEditorView, props: true },
  { path: '/integrations', component: IntegrationsView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.isAuthenticated) {
    return '/login'
  }
  return true
})

export default router
