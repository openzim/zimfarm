import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatListModule } from '@angular/material/list';
import { MatSidenavModule } from '@angular/material/sidenav';
import { RouterModule, Routes } from '@angular/router';

import { TaskDetailComponent } from './task-detail/task-detail';
import { TaskListComponent } from './task-list/task-list';


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
        MatListModule,
        MatSidenavModule,
        // AgGridModule.withComponents([CategoryFilterComponent])
    ],
    declarations: [
        TaskListComponent,
        TaskDetailComponent
    ]
})
export class TaskModule { }
