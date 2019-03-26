import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Routes, RouterModule } from '@angular/router';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { AgGridModule } from 'ag-grid-angular';

import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatListModule } from '@angular/material/list';

import { TaskListComponent } from './task-list/task-list';
import { TaskDetailComponent } from './task-detail/task-detail';


const routes: Routes = [
    {
        path: '', 
        component: TaskListComponent, 
        children: [
            {path: ':id', component: TaskDetailComponent}
        ]
    }
];

@NgModule({
    imports: [
        CommonModule,
        FormsModule,
        ReactiveFormsModule,
        RouterModule.forChild(routes),
        MatCardModule,
        MatDividerModule,
        MatExpansionModule,
        MatListModule
        // AgGridModule.withComponents([CategoryFilterComponent])
    ],
    declarations: [
        TaskListComponent,
        TaskDetailComponent
    ]
})
export class TaskModule { }
