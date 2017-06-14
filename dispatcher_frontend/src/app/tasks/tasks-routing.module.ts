import { NgModule }            from '@angular/core';
import { RouterModule, Routes }        from '@angular/router';

import { TasksComponent }    from './tasks.component';
import { ListTasksComponent } from './list/list-tasks.component';
import { AddTaskComponent } from './add/add-task.component';

const routes: Routes = [
    { path: 'tasks', component: TasksComponent, children: [
        { path: '', component: ListTasksComponent, pathMatch: 'full'},
        { path: 'add', component: AddTaskComponent, pathMatch: 'full'}
    ]}
];

@NgModule({
    imports: [RouterModule.forChild(routes)],
    exports: [RouterModule]
})
export class TasksRoutingModule {}