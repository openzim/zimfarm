import ChangePasswordView from '@/views/ChangePasswordView.vue'
import NotFoundView from '@/views/NotFound.vue'
import PipelineView from '@/views/PipelineView.vue'
import ScheduleDetailView from '@/views/ScheduleDetailView.vue'
import SchedulesView from '@/views/SchedulesView.vue'
import SignInView from '@/views/SignInView.vue'
import SupportUsView from '@/views/SupportUs.vue'
import TaskDetailView from '@/views/TaskDetailView.vue'
import UsersView from '@/views/UsersView.vue'
import UserView from '@/views/UserView.vue'
import WorkerDetailView from '@/views/WorkerDetailView.vue'
import WorkersView from '@/views/WorkersView.vue'
import type { RouteLocationNormalized } from 'vue-router'
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/workers/:workerName',
    name: 'worker-detail',
    component: WorkerDetailView,
    props: true,
    meta: {
      title: (to: RouteLocationNormalized) => `Zimfarm | Worker • ${to.params.workerName}`,
    },
  },
  {
    path: '/workers/:workerName/:selectedTab',
    name: 'worker-detail-tab',
    component: WorkerDetailView,
    props: true,
    meta: {
      title: (to: RouteLocationNormalized) => `Zimfarm | Worker • ${to.params.workerName}`,
    },
  },
  {
    path: '/',
    name: 'home',
    redirect: { name: 'pipeline' },
  },
  {
    path: '/pipeline',
    name: 'pipeline',
    component: PipelineView,
    meta: { title: 'Zimfarm | Pipeline' },
  },
  {
    path: '/support-us',
    name: 'support',
    component: SupportUsView,
    meta: { title: 'Zimfarm | Support Us' },
  },
  {
    path: '/sign-in',
    name: 'sign-in',
    component: SignInView,
    meta: { title: 'Zimfarm | Sign In' },
  },
  {
    path: '/change-password',
    name: 'change-password',
    component: ChangePasswordView,
    meta: { title: 'Zimfarm | Change Password' },
  },

  {
    path: '/pipeline/:id',
    name: 'task-detail',
    component: TaskDetailView,
    props: true,
    meta: {
      title: (to: RouteLocationNormalized) => `Zimfarm | Task • ${to.params.id}`,
    },
  },

  {
    path: '/pipeline/:id/:selectedTab',
    name: 'task-detail-tab',
    component: TaskDetailView,
    props: true,
    meta: {
      title: (to: RouteLocationNormalized) => `Zimfarm | Task • ${to.params.id}`,
    },
  },

  {
    path: '/recipes/:scheduleName',
    name: 'schedule-detail',
    component: ScheduleDetailView,
    props: true,
    meta: {
      title: (to: RouteLocationNormalized) => `Zimfarm | Recipe • ${to.params.scheduleName}`,
    },
  },
  {
    path: '/recipes/:scheduleName/:selectedTab',
    name: 'schedule-detail-tab',
    component: ScheduleDetailView,
    props: true,
    meta: {
      title: (to: RouteLocationNormalized) => `Zimfarm | Recipe • ${to.params.scheduleName}`,
    },
  },
  {
    path: '/recipes',
    name: 'schedules-list',
    component: SchedulesView,
    meta: { title: 'Zimfarm | Recipes' },
  },
  {
    path: '/users/:username',
    name: 'user-detail',
    component: UserView,
    props: true,
    meta: {
      title: (to: RouteLocationNormalized) => `Zimfarm | User • ${to.params.username}`,
    },
  },
  {
    path: '/users/:username/:selectedTab',
    name: 'user-detail-tab',
    component: UserView,
    props: true,
    meta: {
      title: (to: RouteLocationNormalized) => `Zimfarm | User • ${to.params.username}`,
    },
  },
  {
    path: '/users',
    name: 'users-list',
    component: UsersView,
    meta: { title: 'Zimfarm | Users' },
  },
  {
    path: '/workers',
    name: 'workers',
    component: WorkersView,
    meta: { title: 'Zimfarm | Workers' },
  },
  {
    path: '/:pathMatch(.*)*',
    name: '404',
    component: NotFoundView,
    meta: { title: 'Zimfarm | Page Not Found' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Add global navigation guard to update title
router.beforeEach((to, from, next) => {
  // Update document title
  if (to.meta.title) {
    if (typeof to.meta.title === 'function') {
      // Handle dynamic titles with route parameters
      document.title = to.meta.title(to)
    } else {
      // Handle static titles
      document.title = to.meta.title as string
    }
  } else {
    document.title = 'Zimfarm' // fallback
  }
  next()
})

export default router
