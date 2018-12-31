import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Routes, RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { SharedModule } from '../shared/shared.module';
import { ScheduleListComponent } from './schedule-list/schedule-list.component';
import { ScheduleListFilterComponent } from './schedule-list-filter/schedule-list-filter.component';
import { ScheduleDetailComponent } from './schedule-detail/schedule-detail.component';
import { ScheduleOverviewComponent } from './schedule-overview/schedule-overview.component';
import { ScheduleBeatComponent } from './schedule-beat/schedule-beat.component';
import { ScheduleOfflinerComponent } from './schedule-offliner/schedule-offliner.component';
import { ScheduleTaskComponent } from './schedule-task/schedule-task.component';

const routes: Routes = [
    {
        path: '', 
        component: ScheduleListComponent, 
        children: [
            {path: ':name', component: ScheduleBeatComponent}
        ]
    }
];

@NgModule({
    imports: [
        CommonModule,
        SharedModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule.forChild(routes)
    ],
    declarations: [
        ScheduleListComponent, 
        ScheduleListFilterComponent, 
        ScheduleDetailComponent, 
        ScheduleOverviewComponent, 
        ScheduleBeatComponent, 
        ScheduleOfflinerComponent, 
        ScheduleTaskComponent]
})
export class ScheduleModule { }
