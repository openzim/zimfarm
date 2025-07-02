import PipelineView from '@/views/PipelineView.vue'
import ScheduleDetailView from '@/views/ScheduleDetailView.vue'
import SignInView from '@/views/SignInView.vue'
import TaskDetailView from '@/views/TaskDetailView.vue'
import { createRouter, createWebHistory } from "vue-router"

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
      component: PipelineView,
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
      props: true,
    },

    {
      path: '/recipes/:schedule_name',
      name: 'schedule-detail',
      component: ScheduleDetailView,
      props: true,
    },
    {
      path: '/recipes',
      name: 'schedules-list',
      component: PipelineView,
    },
    {
      path: '/users/:username',
      name: 'user-detail',
      component: PipelineView,
      props: true,
    },
    {
      path: '/users/:username/:selectedTab',
      name: 'user-detail-tab',
      component: PipelineView,
      props: true,
    },
    {
      path: '/users',
      name: 'users-list',
      component: PipelineView,
    },
    {
      path: '/workers',
      name: 'workers',
      component: PipelineView,
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
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
})

export default router
