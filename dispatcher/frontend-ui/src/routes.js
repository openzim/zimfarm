
import PipelineView from './views/PipelineView.vue'
import SignIn from './views/SignIn.vue'
import ChangePassword from './views/ChangePassword.vue'
import NotFound from './views/NotFound.vue'
import SchedulesView from './views/SchedulesView.vue'
import ScheduleView from './views/ScheduleView.vue'
import UsersView from './views/UsersView.vue'
import UserView from './views/UserView.vue'
import WorkersView from './views/WorkersView.vue'
import TaskView from './views/TaskView.vue'
import About from './views/About.vue'

export default [
  {
    path: '/',
    name: 'home',
    redirect: {name: 'pipeline'},
  },
  {
    path: '/about',
    name: 'about',
    component: About,
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
    path: '/change-password',
    name: 'change-password',
    component: ChangePassword,
  },
  {
    path: '/recipes/:schedule_name',
    name: 'schedule-detail',
    component: ScheduleView,
    props: true,
  },
  {
    path: '/recipes/:schedule_name/:selectedTab',
    name: 'schedule-detail-tab',
    component: ScheduleView,
    props: true,
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
    path: '*',
    name: '404',
    component: NotFound
  },
]
