import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';

import { DashboardComponent } from './Dashboard/dashboard.component';
import { TasksComponent } from './Tasks/tasks.component';
import { TaskDetailComponent } from './Tasks/task-detail.component';
import { TemplatesComponent } from './Templates/templates.component';
import { NodesComponent } from './Nodes/nodes.component';

const routes: Routes = [
    { path: '', redirectTo: '/tasks', pathMatch: 'full' },
    { path: 'dashboard', component: DashboardComponent },
    { path: 'tasks', component: TasksComponent},
    { path: 'tasks/detail/:id', component: TaskDetailComponent},
    { path: 'templates', component: TemplatesComponent},
    { path: 'nodes', component: NodesComponent}
];


@NgModule({
    imports: [ RouterModule.forRoot(routes) ],
    exports: [ RouterModule ]
})
export class AppRoutingModule {}