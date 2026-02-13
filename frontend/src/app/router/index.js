import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '~/src/entities/user'
import { LoginPage } from '~/src/pages/login'
import { RegisterPage } from '~/src/pages/register'
import { BlogsPage } from '~/src/pages/blogs'
import { NotesPage } from '~/src/pages/notes'
import { NoteEditorPage } from '~/src/pages/note-editor'
import { IntegrationsPage } from '~/src/pages/integrations'

const routes = [
  { path: '/', redirect: '/blogs' },
  { path: '/login', component: LoginPage, meta: { public: true } },
  { path: '/register', component: RegisterPage, meta: { public: true } },
  { path: '/blogs', component: BlogsPage },
  { path: '/blogs/:id/notes', component: NotesPage, props: true },
  { path: '/notes/:id', component: NoteEditorPage, props: true },
  { path: '/integrations', component: IntegrationsPage }
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
