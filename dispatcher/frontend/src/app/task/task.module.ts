import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Routes, RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { AgGridModule } from 'ag-grid-angular';
import { MatListModule } from '@angular/material/list';

import { TaskListComponent } from './task-list/task-list';

const routes: Routes = [
    {
        path: '', 
        component: TaskListComponent, 
        // children: [
        //     {path: ':name', component: ScheduleDetailComponent}
        // ]
    }
];

@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule.forChild(routes),
        MatListModule
        // AgGridModule.withComponents([CategoryFilterComponent])
    ],
    declarations: [
        TaskListComponent
    ]
})
export class TaskModule { }
