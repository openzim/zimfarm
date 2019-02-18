import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Routes, RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { AgGridModule } from 'ag-grid-angular';

import { SharedModule } from '../shared/shared.module';
import { ScheduleListComponent } from './schedule-list/schedule-list.component';
import { ScheduleListFilterComponent } from './schedule-list-filter/schedule-list-filter.component';
import { ScheduleDetailComponent } from './schedule-detail/schedule-detail.component';
import { ScheduleOverviewComponent } from './schedule-overview/schedule-overview.component';
import { ScheduleOfflinerComponent } from './schedule-offliner/schedule-offliner.component';
import { ScheduleTaskComponent } from './schedule-task/schedule-task.component';
import { ScheduleGridComponent } from './schedule-grid/schedule-grid.component';

const routes: Routes = [
    {
        path: '', 
        component: ScheduleGridComponent, 
        children: [
            {path: ':name', component: ScheduleDetailComponent}
        ]
    }
];

@NgModule({
    imports: [
        CommonModule,
        SharedModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule.forChild(routes),
        AgGridModule.withComponents([])
    ],
    declarations: [
        ScheduleGridComponent,
        ScheduleListComponent, 
        ScheduleListFilterComponent, 
        ScheduleDetailComponent, 
        ScheduleOverviewComponent, 
        ScheduleOfflinerComponent, 
        ScheduleTaskComponent]
})
export class ScheduleModule { }
