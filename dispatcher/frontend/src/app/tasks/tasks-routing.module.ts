import { NgModule }            from '@angular/core';
import { RouterModule, Routes }        from '@angular/router';

import { AuthGuard } from '../guard/auth.guard';
import { ListTasksComponent } from './list/list-tasks.component';
import { AddTaskComponent } from './add/add-task.component';
// import { TaskDetailComponent } from './detail/task-detail.component'; 


const routes: Routes = [
    { path: 'tasks', canActivate: [AuthGuard], children: [
        { path: '', component: ListTasksComponent, pathMatch: 'full'},
        { path: 'add', component: AddTaskComponent, pathMatch: 'full'},
        // { path: 'detail/:id', component: TaskDetailComponent, pathMatch: 'full'}
    ]}
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class TasksRoutingModule {}