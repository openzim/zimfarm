import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { TasksComponent } from './tasks.component';
import { TasksRoutingModule } from './tasks-routing.module';

// import { TaskProgressComponent } from './task-progress/tasks-progress.component';
// import { RecentEventsComponent } from './recent-events/recent-events.component';
// import { TaskCountComponent } from './task-count/task-count.component';

@NgModule({
    imports: [
        CommonModule,
        TasksRoutingModule
    ],
    declarations: [
        TasksComponent
    ]
})
export class TasksModule { }