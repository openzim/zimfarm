import { ScrollingModule } from '@angular/cdk/scrolling';
import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatTabsModule } from '@angular/material/tabs';
import { RouterModule, Routes } from '@angular/router';

import { FileSizePipe } from '../shared/file-size.pipe';
import { TaskDetailComponent } from './task-detail/task-detail';
import { TaskListItemComponent } from './task-list-item/task-list-item';
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
        MatIconModule,
        MatListModule,
        MatSidenavModule,
        MatTabsModule,
        ScrollingModule
    ],
    declarations: [
        FileSizePipe,
        TaskDetailComponent,
        TaskListItemComponent,
        TaskListComponent,
    ]
})
export class TaskModule { }
