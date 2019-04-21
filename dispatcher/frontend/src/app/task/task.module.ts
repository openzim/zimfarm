import { CommonModule } from '@angular/common';
import { NgModule } from '@angular/core';
import { FormsModule, ReactiveFormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatExpansionModule } from '@angular/material/expansion';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatTabsModule } from '@angular/material/tabs';
import { RouterModule, Routes } from '@angular/router';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatChipsModule} from '@angular/material/chips';
import {ScrollingModule} from '@angular/cdk/scrolling';

import { TaskDetailComponent } from './task-detail/task-detail';
import { TaskListComponent } from './task-list/task-list';
import { TaskListItemComponent } from './task-list-item/task-list-item';


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
        MatIconModule,
        MatListModule,
        MatSidenavModule,
        MatTabsModule,
        MatGridListModule,
        MatChipsModule,
        ScrollingModule
        
        // AgGridModule.withComponents([CategoryFilterComponent])
    ],
    declarations: [
        TaskListComponent,
        TaskDetailComponent,
        TaskListItemComponent
    ]
})
export class TaskModule { }
