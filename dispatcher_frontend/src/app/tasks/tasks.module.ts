import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule }   from '@angular/forms';

import { TasksComponent } from './tasks.component';
import { TasksRoutingModule } from './tasks-routing.module';

import { ListTasksComponent } from './list/list-tasks.component';
import { AddTaskComponent } from './add/add-task.component';

@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        TasksRoutingModule
    ],
    declarations: [
        TasksComponent,
        ListTasksComponent,
        AddTaskComponent
    ]
})
export class TasksModule { }