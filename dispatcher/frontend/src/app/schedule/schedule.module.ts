import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Routes, RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';

import { SharedModule } from '../shared/shared.module';
import { ScheduleListComponent } from './schedule-list/schedule-list.component';
import { ScheduleDetailComponent } from './schedule-detail/schedule-detail.component';
import { ScheduleOverviewComponent } from './schedule-overview/schedule-overview.component';
import { ScheduleBeatComponent } from './schedule-beat/schedule-beat.component';
import { ScheduleOfflinerComponent } from './schedule-offliner/schedule-offliner.component';
import { ScheduleTaskComponent } from './schedule-task/schedule-task.component';

const routes: Routes = [
    { path: '', component: ScheduleListComponent },
    {
        path: ':name', 
        component: ScheduleDetailComponent,
        children: [
            { path: '', component: ScheduleOverviewComponent },
            { path: 'beat', component: ScheduleBeatComponent },
            { path: 'offliner', component: ScheduleOfflinerComponent },
            { path: 'task', component: ScheduleTaskComponent },
            { path: '**', redirectTo: '' }
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
        ScheduleDetailComponent, 
        ScheduleOverviewComponent, 
        ScheduleBeatComponent, 
        ScheduleOfflinerComponent, 
        ScheduleTaskComponent]
})
export class ScheduleModule { }
