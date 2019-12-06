
import PipelineView from './views/PipelineView.vue'
import SignIn from './components/SignIn.vue'
import NotFound from './components/NotFound.vue'
import SchedulesList from './components/SchedulesList.vue'
import ScheduleView from './views/ScheduleView.vue'
import UsersView from './views/UsersView.vue'
import WorkersView from './views/WorkersView.vue'
import TaskView from './views/TaskView.vue'

export default [
  {
    path: '/',
    name: 'home',
    redirect: {name: 'pipeline'},
  },
  {
    path: '/pipeline/filter-:filter',
    name: 'pipeline-filtered',
    component: PipelineView,
    props: true,
  },
  {
    path: '/pipeline',
    name: 'pipeline',
    redirect: {name: 'pipeline-filtered', params: {filter: 'todo'}},
  },
  {
    path: '/pipeline/:_id',
    name: 'task-detail',
    component: TaskView,
    props: true,
  },
  {
    path: '/pipeline/:_id/:selectedTab',
    name: 'task-detail-tab',
    component: TaskView,
    props: true,
  },
  {
    path: '/sign-in',
    name: 'sign-in',
    component: SignIn,
  },
  {
    path: '/schedules/:schedule_name',
    name: 'schedule-detail',
    component: ScheduleView,
    props: true,
  },
  {
    path: '/schedules/:schedule_name/:selectedTab',
    name: 'schedule-detail-tab',
    component: ScheduleView,
    props: true,
  },
  {
    path: '/schedules',
    name: 'schedules-list',
    component: SchedulesList,
  },
  {
    path: '/users/:username',
    name: 'user-detail',
    component: UsersView,
    props: true,
  },
  {
    path: '/users',
    name: 'users-list',
    component: UsersView,
  },
  {
    path: '/workers',
    name: 'workers-list',
    component: WorkersView,
  },
  {
    path: '*',
    name: '404',
    component: NotFound
  },
]
