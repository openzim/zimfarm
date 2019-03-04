import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Routes, RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { AgGridModule } from 'ag-grid-angular';

import { SharedModule } from '../shared/shared.module';
import { ScheduleGridComponent } from './schedule-grid/schedule-grid.component';
import { CategoryFilterComponent } from './schedule-filters/category-filter';

const routes: Routes = [
    {
        path: '', 
        component: ScheduleGridComponent, 
        // children: [
        //     {path: ':name', component: ScheduleDetailComponent}
        // ]
    }
];

@NgModule({
    imports: [
        CommonModule,
        SharedModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule.forChild(routes),
        AgGridModule.withComponents([CategoryFilterComponent])
    ],
    declarations: [
        ScheduleGridComponent,
        CategoryFilterComponent]
})
export class ScheduleModule { }
