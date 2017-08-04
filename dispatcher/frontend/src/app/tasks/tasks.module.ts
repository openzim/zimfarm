import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule }   from '@angular/forms';
import { NgbModule } from '@ng-bootstrap/ng-bootstrap';

import { TasksRoutingModule } from './tasks-routing.module';

import { ListTasksComponent } from './list/list-tasks.component';
import { AddTaskComponent } from './add/add-task.component';
import { TaskDetailComponent } from './detail/task-detail.component';

import { MWOfflinerComponent } from './view/mwoffliner/mwoffliner.component';

@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        NgbModule,
        TasksRoutingModule
    ],
    declarations: [
        ListTasksComponent,
        AddTaskComponent,
        TaskDetailComponent,
        MWOfflinerComponent
    ]
})
export class TasksModule { }