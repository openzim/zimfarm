import PipelineView from '@/views/PipelineView.vue'
import ScheduleDetailView from '@/views/ScheduleDetailView.vue'
import TaskDetailView from '@/views/TaskDetailView.vue'
import { createRouter, createWebHistory } from "vue-router"

const routes = [
    {
        path: '/',
        name: 'home',
        component: PipelineView,
    },
    {
      path: '/pipeline/:id',
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

]

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes,
})

export default router
