import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';

import { DashboardComponent } from './dashboard.component';
import { DashboardRoutingModule } from './dashboard-routing.module';

import { TaskProgressComponent } from './task-progress/tasks-progress.component';
import { RecentEventsComponent } from './recent-events/recent-events.component';
import { TaskCountComponent } from './task-count/task-count.component';

@NgModule({
    imports: [
        CommonModule,
        DashboardRoutingModule
    ],
    declarations: [
        DashboardComponent,
        TaskProgressComponent,
        RecentEventsComponent,
        TaskCountComponent
    ]
})
export class DashboardModule { }