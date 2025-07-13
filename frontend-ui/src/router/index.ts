import PipelineView from '@/views/PipelineView.vue'
import ScheduleDetailView from '@/views/ScheduleDetailView.vue'
import SchedulesView from '@/views/SchedulesView.vue'
import SignInView from '@/views/SignInView.vue'
import SupportUsView from '@/views/SupportUs.vue'
import TaskDetailView from '@/views/TaskDetailView.vue'
import UsersView from '@/views/UsersView.vue'
import UserView from '@/views/UserView.vue'
import WorkersView from '@/views/WorkersView.vue'
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'home',
    redirect: { name: 'pipeline' },
  },
  {
    path: '/pipeline',
    name: 'pipeline',
    component: PipelineView,
  },
  {
    path: '/support-us',
    name: 'support',
    component: SupportUsView,
  },
  {
    path: '/sign-in',
    name: 'sign-in',
    component: SignInView,
  },
  {
    path: '/change-password',
    name: 'change-password',
    component: TaskDetailView,
  },

  {
    path: '/tasks/:id',
    name: 'task-detail',
    component: TaskDetailView,
  },

  {
    path: '/recipes/:schedule_name',
    name: 'schedule-detail',
    component: ScheduleDetailView,
  },
  {
    path: '/recipes',
    name: 'schedules-list',
    component: SchedulesView,
  },
  {
    path: '/users/:username',
    name: 'user-detail',
    component: UserView,
    props: true,
  },
  {
    path: '/users/:username/:selectedTab',
    name: 'user-detail-tab',
    component: UserView,
    props: true,
  },
  {
    path: '/users',
    name: 'users-list',
    component: UsersView,
  },
  {
    path: '/workers',
    name: 'workers',
    component: WorkersView,
  },
  {
    path: '/stats',
    name: 'stats',
    component: PipelineView,
  },
  {
    path: '/:pathMatch(.*)*',
    name: '404',
    component: PipelineView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
